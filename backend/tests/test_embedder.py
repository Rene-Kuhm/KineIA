import numpy as np
import pytest
from unittest.mock import MagicMock, patch


class TestEmbedder:
    @patch("app.core.ingestion.embedder.SentenceTransformer")
    def test_generate_embeddings_returns_correct_shape(self, mock_transformer):
        """Embedding generation should return a list of vectors with correct dimensions."""
        # Setup mock
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array(
            [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        )
        mock_transformer.return_value = mock_model

        from app.core.ingestion.embedder import generate_embeddings, _model

        # Force model to None to trigger lazy loading with mock
        import app.core.ingestion.embedder as embedder_mod
        embedder_mod._model = None

        texts = ["texto uno", "texto dos", "texto tres"]
        embeddings = generate_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

    @patch("app.core.ingestion.embedder.SentenceTransformer")
    def test_generate_single_embedding(self, mock_transformer):
        """Single embedding should return one vector."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.5] * 384])
        mock_transformer.return_value = mock_model

        import app.core.ingestion.embedder as embedder_mod
        embedder_mod._model = None

        from app.core.ingestion.embedder import generate_embedding

        embedding = generate_embedding("un solo texto")
        assert len(embedding) == 384
        assert isinstance(embedding, list)

    @patch("app.core.ingestion.embedder.SentenceTransformer")
    def test_model_is_singleton(self, mock_transformer):
        """get_embedding_model should reuse the same model instance."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.0] * 384])
        mock_transformer.return_value = mock_model

        import app.core.ingestion.embedder as embedder_mod
        embedder_mod._model = None

        from app.core.ingestion.embedder import get_embedding_model

        model1 = get_embedding_model()
        model2 = get_embedding_model()
        assert model1 is model2
        # Should only be instantiated once
        assert mock_transformer.call_count == 1

    @patch("app.core.ingestion.embedder.SentenceTransformer")
    def test_normalize_embeddings_flag(self, mock_transformer):
        """encode should be called with normalize_embeddings=True."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.0] * 384])
        mock_transformer.return_value = mock_model

        import app.core.ingestion.embedder as embedder_mod
        embedder_mod._model = None

        from app.core.ingestion.embedder import generate_embeddings

        generate_embeddings(["test"])
        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs.get("normalize_embeddings") is True
