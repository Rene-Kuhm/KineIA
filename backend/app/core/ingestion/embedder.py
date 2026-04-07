from sentence_transformers import SentenceTransformer

from app.config import settings

_model = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model (singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    return embeddings.tolist()


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    return generate_embeddings([text])[0]
