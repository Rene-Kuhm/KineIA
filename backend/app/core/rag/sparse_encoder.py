from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector


class SpanishBm25Encoder:
    """Deterministic Spanish BM25 sparse vectors for Qdrant IDF indexes."""

    def __init__(self) -> None:
        self._model = SparseTextEmbedding("Qdrant/bm25", language="spanish")

    def encode(self, text: object) -> SparseVector:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        embedding = next(iter(self._model.embed([text])))
        pairs = sorted(zip(embedding.indices, embedding.values, strict=True))
        if not pairs:
            raise ValueError("text contains no indexable terms")
        return SparseVector(
            indices=[int(index) for index, _ in pairs],
            values=[float(value) for _, value in pairs],
        )
