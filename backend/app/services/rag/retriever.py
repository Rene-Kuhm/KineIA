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
                # Payload fields are at top level (title, source_type, area, etc.)
                metadata = {
                    "title": res.payload.get("title", "Desconocido"),
                    "source": res.payload.get("source_file", res.payload.get("file_name", "Desconocido")),
                    "source_type": res.payload.get("source_type", "unknown"),
                    "area": res.payload.get("area", "general"),
                    "evidence_level": res.payload.get("evidence_level", "unknown"),
                    "author": res.payload.get("author", ""),
                    "year": res.payload.get("year", 0),
                    "university": res.payload.get("university", ""),
                }
                doc = {
                    "text": res.payload.get("text", ""),
                    "metadata": metadata,
                    "score": res.score,
                }
                documents.append(doc)

        return documents


retriever = Retriever()
