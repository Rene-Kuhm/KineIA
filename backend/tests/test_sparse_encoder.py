from types import SimpleNamespace

import pytest


def test_spanish_bm25_is_deterministic_and_rejects_invalid_text(monkeypatch):
    from app.core.rag import sparse_encoder
    class FakeModel:
        def __init__(self, model_name, **kwargs):
            assert (model_name, kwargs["language"]) == ("Qdrant/bm25", "spanish")

        def embed(self, documents):
            assert documents == ["rehabilitación de rodilla"]
            yield SimpleNamespace(indices=[9, 2], values=[0.9, 0.2])
    monkeypatch.setattr(sparse_encoder, "SparseTextEmbedding", FakeModel)
    encoder = sparse_encoder.SpanishBm25Encoder()
    first = encoder.encode("rehabilitación de rodilla")
    second = encoder.encode("rehabilitación de rodilla")
    assert (first.indices, first.values) == ([2, 9], [0.2, 0.9])
    assert first == second
    for invalid in (None, 42, "", "   "):
        with pytest.raises(ValueError, match="non-empty string"):
            encoder.encode(invalid)
