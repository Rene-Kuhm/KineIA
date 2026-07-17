import logging
from contextlib import suppress
from time import perf_counter

from app.config import settings
from app.core.ingestion.embedder import generate_embedding
from app.core.rag.sparse_encoder import SpanishBm25Encoder
from app.db.qdrant import get_qdrant
from qdrant_client.models import (
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
)

logger = logging.getLogger(__name__)
_SHADOW_LOG = (
    "retrieval_shadow retrieval_mode=dense_primary_hybrid_shadow "
    "primary_score_type=cosine shadow_score_type=rrf status=%s "
    "primary_latency_ms=%.3f shadow_latency_ms=%.3f primary_candidates=%d "
    "shadow_candidates=%d comparison_k=%d overlap_count=%d overlap_ratio=%.6f"
)


def _log_shadow(status, primary_ms, shadow_ms, primary_count, shadow_count,
                comparison_k, overlap, ratio, error=None):
    args = (status, primary_ms, shadow_ms, primary_count, shadow_count,
            comparison_k, overlap, ratio)
    if error is None:
        logger.info(_SHADOW_LOG, *args)
    else:
        logger.warning(_SHADOW_LOG + " exception_class=%s", *args, type(error).__name__)


def _emit_shadow_metric(*args, **kwargs):
    with suppress(Exception):
        _log_shadow(*args, **kwargs)


class Retriever:
    def __init__(self, *, client=None, read_mode=None, gate=None):
        self.client = client or get_qdrant()
        self.collection_name = settings.qdrant_collection
        self.read_mode, self.gate = read_mode, gate
        self._sparse_encoder = None

    def evaluation_identity(self):
        gate, expiry = self.gate, getattr(self.gate, "expires_at", None)
        allowed = bool(gate and gate.allows_hybrid())
        served = "hybrid" if self.read_mode == "hybrid" and allowed else (
            "dense_fallback" if self.read_mode == "hybrid" else "dense")
        return {
            "class": f"{type(self).__module__}.{type(self).__qualname__}",
            "configured_read_mode": self.read_mode, "served_mode": served,
            "score_type": "rrf" if served == "hybrid" else "cosine",
            "collections": {"dense": self.collection_name,
                            "hybrid": settings.qdrant_hybrid_collection},
            "vectors": {"dense": settings.qdrant_dense_vector_name,
                        "sparse": settings.qdrant_sparse_vector_name},
            "embedding_model": settings.embedding_model,
            "hybrid": {"candidate_k": settings.retriever_hybrid_candidate_k,
                       "timeout_seconds": settings.retriever_hybrid_timeout_seconds},
            "gate": None if gate is None else {"allowed": allowed,
                     "reason": getattr(gate, "reason", None),
                     "expires_at": expiry.isoformat() if expiry else None},
        }

    def _hybrid_search(self, query, query_vector, query_filter, limit):
        if self._sparse_encoder is None:
            self._sparse_encoder = SpanishBm25Encoder()
        candidate_k = max(limit, settings.retriever_hybrid_candidate_k)
        return self.client.query_points(
            collection_name=settings.qdrant_hybrid_collection,
            prefetch=[
                Prefetch(query=query_vector, using=settings.qdrant_dense_vector_name,
                         filter=query_filter, limit=candidate_k),
                Prefetch(query=self._sparse_encoder.encode(query),
                         using=settings.qdrant_sparse_vector_name,
                         filter=query_filter, limit=candidate_k),
            ],
            query=FusionQuery(fusion=Fusion.RRF), limit=limit, with_payload=True,
            timeout=settings.retriever_hybrid_timeout_seconds,
        )

    def _dense_search(self, query_vector, query_filter, limit):
        return self.client.query_points(
            collection_name=self.collection_name, query=query_vector,
            query_filter=query_filter, limit=limit, with_payload=True,
        )

    @staticmethod
    def _documents(results, retrieval_mode, score_type):
        documents = []
        for res in results.points:
            if not res.payload:
                continue
            metadata_fields = (
                "title", "source_id", "source_version", "source_version_id", "content_hash",
                "original_source_name", "original_source_path", "url", "doi", "isbn", "edition",
                "publisher", "license", "rights", "author", "year", "publication_date",
                "acquisition_date", "reviewer", "review_date", "review_due_date", "evidence_level",
                "area", "population", "source_type", "university", "chunk_index",
            )
            metadata = {key: res.payload[key] for key in metadata_fields
                        if key in res.payload and res.payload[key] is not None}
            source = (res.payload.get("original_source_path") or res.payload.get("source_file")
                      or res.payload.get("file_name"))
            if source:
                metadata["source"] = source
            documents.append({"text": res.payload.get("text", ""), "metadata": metadata,
                              "score": res.score, "retrieval_mode": retrieval_mode,
                              "score_type": score_type})
        return documents

    def _shadow_search(self, query, query_vector, query_filter, limit,
                       primary_points, primary_ms):
        candidate_k = settings.retriever_hybrid_candidate_k
        comparison_k = max(0, min(limit, candidate_k))
        started = perf_counter()
        try:
            if self._sparse_encoder is None:
                self._sparse_encoder = SpanishBm25Encoder()
            shadow = self.client.query_points(
                collection_name=settings.qdrant_hybrid_collection,
                prefetch=[
                    Prefetch(query=query_vector, using=settings.qdrant_dense_vector_name,
                             filter=query_filter, limit=candidate_k),
                    Prefetch(query=self._sparse_encoder.encode(query),
                             using=settings.qdrant_sparse_vector_name,
                             filter=query_filter, limit=candidate_k),
                ],
                query=FusionQuery(fusion=Fusion.RRF), limit=comparison_k,
                with_payload=False, timeout=settings.retriever_hybrid_timeout_seconds,
            )
            primary_ids = {point.id for point in primary_points[:comparison_k]}
            shadow_ids = {point.id for point in shadow.points[:comparison_k]}
            overlap = len(primary_ids & shadow_ids)
            ratio = overlap / max(len(primary_ids), len(shadow_ids), 1)
        except Exception as error:
            _emit_shadow_metric(
                "fallback", primary_ms, (perf_counter() - started) * 1000,
                len(primary_points), 0, comparison_k, 0, 0.0, error,
            )
        else:
            _emit_shadow_metric(
                "success", primary_ms, (perf_counter() - started) * 1000,
                len(primary_points), len(shadow.points), comparison_k, overlap, ratio,
            )

    def search(
        self,
        query: str,
        area: str | None = None,
        evidence_level: str | None = None,
        limit: int = settings.retriever_top_k,
    ) -> list[dict]:
        query_vector = generate_embedding(query)

        must_conditions = []
        if area:
            must_conditions.append(
                FieldCondition(key="area", match=MatchValue(value=area))
            )
        if evidence_level:
            must_conditions.append(
                FieldCondition(key="evidence_level", match=MatchValue(value=evidence_level))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        if self.read_mode == "hybrid":
            if self.gate and self.gate.allows_hybrid():
                try:
                    return self._documents(
                        self._hybrid_search(query, query_vector, query_filter, limit),
                        "hybrid", "rrf")
                except Exception as error:
                    with suppress(Exception):
                        logger.warning("retrieval_hybrid status=fallback exception_class=%s",
                                       type(error).__name__)
            results = self._dense_search(query_vector, query_filter, limit)
            return self._documents(results, "dense_fallback", "cosine")

        primary_started = perf_counter()
        results = self._dense_search(query_vector, query_filter, limit)
        if self.read_mode is None and settings.retriever_hybrid_shadow_enabled:
            with suppress(Exception):
                self._shadow_search(query, query_vector, query_filter, limit, results.points,
                                    (perf_counter() - primary_started) * 1000)
        return self._documents(results, "dense", "cosine")


retriever = Retriever(read_mode="dense")
