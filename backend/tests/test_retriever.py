from unittest.mock import MagicMock, patch

import pytest


class TestRetriever:
    @pytest.fixture
    def mock_qdrant_results(self):
        """Create mock Qdrant search results with points."""
        results = MagicMock()
        points = []
        for i in range(3):
            point = MagicMock()
            point.id = f"point-{i}"
            point.score = 0.9 - i * 0.1
            point.payload = {
                "text": f"Texto del documento {i} sobre kinesiología.",
                "title": f"Documento {i}",
                "source_type": "book",
                "area": "kinesiologia",
                "evidence_level": "book",
                "university": "UBA",
                "author": f"Autor {i}",
                "year": 2020,
            }
            points.append(point)
        results.points = points
        return results

    @patch("app.services.rag.retriever.generate_embedding")
    @patch("app.services.rag.retriever.get_qdrant")
    def test_search_returns_documents(self, mock_get_qdrant, mock_embedding, mock_qdrant_results):
        """Basic search should return formatted documents."""
        mock_embedding.return_value = [0.1] * 384
        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_qdrant_results
        mock_get_qdrant.return_value = mock_client

        from app.services.rag.retriever import Retriever

        retriever = Retriever()
        results = retriever.search(query="test query", limit=3)

        assert len(results) == 3
        assert all("text" in doc for doc in results)
        assert all("metadata" in doc for doc in results)
        assert all("score" in doc for doc in results)
        assert results[0]["score"] >= results[-1]["score"]

    @patch("app.services.rag.retriever.generate_embedding")
    @patch("app.services.rag.retriever.get_qdrant")
    def test_search_with_area_filter(self, mock_get_qdrant, mock_embedding, mock_qdrant_results):
        """Search with area filter should include filter condition."""
        mock_embedding.return_value = [0.1] * 384
        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_qdrant_results
        mock_get_qdrant.return_value = mock_client

        from app.services.rag.retriever import Retriever

        retriever = Retriever()
        results = retriever.search(query="test", area="kinesiologia")

        assert len(results) == 3
        # Verify filter was passed
        call_kwargs = mock_client.query_points.call_args[1]
        assert call_kwargs["query_filter"] is not None

    @patch("app.services.rag.retriever.generate_embedding")
    @patch("app.services.rag.retriever.get_qdrant")
    def test_search_with_evidence_level_filter(self, mock_get_qdrant, mock_embedding, mock_qdrant_results):
        """Search with evidence_level filter should include filter condition."""
        mock_embedding.return_value = [0.1] * 384
        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_qdrant_results
        mock_get_qdrant.return_value = mock_client

        from app.services.rag.retriever import Retriever

        retriever = Retriever()
        results = retriever.search(query="test", evidence_level="book")

        assert len(results) == 3
        call_kwargs = mock_client.query_points.call_args[1]
        assert call_kwargs["query_filter"] is not None

    @patch("app.services.rag.retriever.generate_embedding")
    @patch("app.services.rag.retriever.get_qdrant")
    def test_search_no_filters(self, mock_get_qdrant, mock_embedding, mock_qdrant_results):
        """Search without filters should pass None as filter."""
        mock_embedding.return_value = [0.1] * 384
        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_qdrant_results
        mock_get_qdrant.return_value = mock_client

        from app.services.rag.retriever import Retriever

        retriever = Retriever()
        results = retriever.search(query="test")

        assert len(results) == 3
        call_kwargs = mock_client.query_points.call_args[1]
        assert call_kwargs["query_filter"] is None

    @patch("app.services.rag.retriever.generate_embedding")
    @patch("app.services.rag.retriever.get_qdrant")
    def test_search_respects_limit(self, mock_get_qdrant, mock_embedding):
        """Search should respect the limit parameter."""
        mock_embedding.return_value = [0.1] * 384
        mock_client = MagicMock()
        results_mock = MagicMock()
        results_mock.points = []  # Empty results
        mock_client.query_points.return_value = results_mock
        mock_get_qdrant.return_value = mock_client

        from app.services.rag.retriever import Retriever

        retriever = Retriever()
        retriever.search(query="test", limit=7)

        call_kwargs = mock_client.query_points.call_args[1]
        assert call_kwargs["limit"] == 7
