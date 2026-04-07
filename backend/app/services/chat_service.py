from app.core.llm.provider import llm_provider
from app.services.rag.retriever import retriever


class ChatService:
    async def chat(
        self,
        query: str,
        area: str | None = None,
        evidence_level: str | None = None,
        mode: str = "student",
        history: list[dict] | None = None,
    ) -> dict:
        # Retrieve relevant context
        docs = retriever.search(query=query, area=area, evidence_level=evidence_level)

        # Generate response
        response = await llm_provider.generate_response(
            query=query, context_docs=docs, history=history, mode=mode
        )

        # Format sources
        sources = []
        for doc in docs:
            metadata = doc.get("metadata", {})
            sources.append(
                {
                    "title": metadata.get("title", "Desconocido"),
                    "source": metadata.get("source", "Desconocido"),
                    "evidence_level": metadata.get("evidence_level", "unknown"),
                    "score": doc.get("score", 0.0),
                }
            )

        return {"answer": response, "sources": sources}


chat_service = ChatService()
