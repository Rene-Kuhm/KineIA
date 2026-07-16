from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.core.ingestion.embedder import generate_embedding
from app.db.qdrant import get_qdrant


class Retriever:
    def __init__(self):
        self.client = get_qdrant()
        self.collection_name = settings.qdrant_collection

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

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        documents = []
        for res in results.points:
            if res.payload:
                metadata_fields = (
                    "title", "source_id", "source_version", "source_version_id",
                    "content_hash", "original_source_name",
                    "original_source_path", "url", "doi", "isbn", "edition", "publisher",
                    "license", "rights", "author", "year", "publication_date",
                    "acquisition_date", "reviewer", "review_date", "review_due_date",
                    "evidence_level", "area", "population", "source_type", "university",
                )
                metadata = {
                    key: res.payload[key]
                    for key in metadata_fields
                    if key in res.payload and res.payload[key] is not None
                }
                source = (
                    res.payload.get("original_source_path")
                    or res.payload.get("source_file")
                    or res.payload.get("file_name")
                )
                if source:
                    metadata["source"] = source
                doc = {
                    "text": res.payload.get("text", ""),
                    "metadata": metadata,
                    "score": res.score,
                }
                documents.append(doc)

        return documents


retriever = Retriever()
