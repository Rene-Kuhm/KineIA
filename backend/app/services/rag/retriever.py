from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.db.qdrant import get_qdrant
from app.config import settings
from app.core.ingestion.embedder import generate_embedding


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
                FieldCondition(key="metadata.area", match=MatchValue(value=area))
            )
        if evidence_level:
            must_conditions.append(
                FieldCondition(
                    key="metadata.evidence_level", match=MatchValue(value=evidence_level)
                )
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
                doc = {
                    "text": res.payload.get("text", ""),
                    "metadata": res.payload.get("metadata", {}),
                    "score": res.score,
                }
                documents.append(doc)

        return documents


retriever = Retriever()
