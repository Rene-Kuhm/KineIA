from sentence_transformers import CrossEncoder

from app.config import settings

_model = None


def get_reranker_model() -> CrossEncoder:
    """Lazy-load the cross-encoder reranker model (singleton)."""
    global _model
    if _model is None:
        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            device="cpu",
        )
    return _model


def rerank(query: str, documents: list[dict], top_k: int = settings.reranker_top_k) -> list[dict]:
    """Re-rank documents by semantic relevance to the query using a cross-encoder.

    Args:
        query: The user query string.
        documents: List of dicts with at least a "text" key.
        top_k: Number of top documents to return after re-ranking.

    Returns:
        Re-ranked list of documents with updated "rerank_score" field.
    """
    if not documents:
        return documents

    model = get_reranker_model()

    # Build (query, doc_text) pairs for the cross-encoder
    pairs = [(query, doc.get("text", "")) for doc in documents]
    scores = model.predict(pairs, show_progress_bar=False)

    # Attach rerank scores and sort descending
    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    documents.sort(key=lambda d: d.get("rerank_score", 0.0), reverse=True)

    return documents[:top_k]
