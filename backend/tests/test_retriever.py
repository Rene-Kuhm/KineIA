import logging
from unittest.mock import MagicMock, patch

import pytest
from qdrant_client.models import Fusion, FusionQuery, SparseVector


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
    def test_search_with_evidence_level_filter(
        self, mock_get_qdrant, mock_embedding, mock_qdrant_results
    ):
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

    @patch("app.services.rag.retriever.generate_embedding")
    def test_shadow_rrf_keeps_dense_results_authoritative(
        self, mock_embedding, mock_qdrant_results, monkeypatch, caplog
    ):
        from app.services.rag import retriever as module

        caplog.set_level("INFO", logger=module.__name__)
        mock_embedding.return_value = [0.1] * 384
        shadow = MagicMock()
        shadow.points = list(reversed(mock_qdrant_results.points[:2]))
        client = MagicMock()
        client.query_points.side_effect = [mock_qdrant_results, shadow]
        encoder = MagicMock()
        encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
        now = [0.0]
        def encoder_factory():
            now[0] += 0.4
            return encoder
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "perf_counter", lambda: now[0])
        monkeypatch.setattr(module, "SpanishBm25Encoder", encoder_factory, raising=False)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "retriever_hybrid_candidate_k", 30, raising=False)
        monkeypatch.setattr(module.settings, "retriever_hybrid_timeout_seconds", 2, raising=False)

        documents = module.Retriever().search(
            "private clinical query", area="kinesiologia", evidence_level="book", limit=300
        )

        assert [doc["score"] for doc in documents] == [0.9, 0.8, 0.7]
        primary, hybrid = [call.kwargs for call in client.query_points.call_args_list]
        assert primary["collection_name"] == module.settings.qdrant_collection
        assert primary["limit"] == 300
        assert hybrid["collection_name"] == module.settings.qdrant_hybrid_collection
        assert isinstance(hybrid["query"], FusionQuery)
        assert hybrid["query"].fusion is Fusion.RRF
        assert [item.using for item in hybrid["prefetch"]] == [
            module.settings.qdrant_dense_vector_name,
            module.settings.qdrant_sparse_vector_name,
        ]
        assert all(item.filter is primary["query_filter"] for item in hybrid["prefetch"])
        assert all(item.limit == 30 and item.score_threshold is None
                   for item in hybrid["prefetch"])
        assert hybrid["limit"] == 30 and hybrid.get("score_threshold") is None
        assert hybrid["timeout"] == 2 and hybrid["with_payload"] is False
        log = caplog.text
        for field in (
            "retrieval_mode=dense_primary_hybrid_shadow", "primary_score_type=cosine",
            "shadow_score_type=rrf", "status=success", "primary_latency_ms=0.000",
            "shadow_latency_ms=400.000", "primary_candidates=3", "shadow_candidates=2",
            "comparison_k=30", "overlap_count=2", "overlap_ratio=0.666667",
        ):
            assert field in log
        assert "private clinical query" not in log

    @pytest.mark.parametrize("failure_stage", ["encoder", "qdrant"])
    @patch("app.services.rag.retriever.generate_embedding")
    def test_shadow_failure_returns_dense_results_without_sensitive_logs(
        self, mock_embedding, mock_qdrant_results, monkeypatch, caplog, failure_stage
    ):
        from app.services.rag import retriever as module

        query = "PHI_QUERY_SENTINEL"
        mock_embedding.return_value = [0.1] * 384
        client = MagicMock()
        error = RuntimeError("PHI_EXCEPTION_SENTINEL")
        side_effect = [mock_qdrant_results]
        if failure_stage == "qdrant":
            side_effect.append(error)
        client.query_points.side_effect = side_effect
        encoder = MagicMock()
        encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
        if failure_stage == "encoder":
            encoder.encode.side_effect = error
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "SpanishBm25Encoder", lambda: encoder)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", True)

        documents = module.Retriever().search(query, area="PHI_FILTER_SENTINEL")

        assert len(documents) == 3
        log = caplog.text
        assert "status=fallback" in log and "exception_class=RuntimeError" in log
        assert all(secret not in log for secret in (
            query, "PHI_EXCEPTION_SENTINEL", "PHI_FILTER_SENTINEL", "point-0",
            "Texto del documento",
        ))

    @patch("app.services.rag.retriever.generate_embedding", return_value=[0.1] * 384)
    def test_disabled_shadow_never_starts_sparse_encoder(
        self, _embedding, mock_qdrant_results, monkeypatch
    ):
        from app.services.rag import retriever as module

        client, factory = MagicMock(), MagicMock()
        client.query_points.return_value = mock_qdrant_results
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "SpanishBm25Encoder", factory)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", False)

        assert len(module.Retriever().search("test")) == 3
        factory.assert_not_called()
        assert client.query_points.call_count == 1

    @patch("app.services.rag.retriever.generate_embedding", return_value=[0.1] * 384)
    def test_primary_failure_remains_visible(self, _embedding, monkeypatch):
        from app.services.rag import retriever as module

        client, factory = MagicMock(), MagicMock()
        client.query_points.side_effect = RuntimeError("primary unavailable")
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "SpanishBm25Encoder", factory)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", True)

        with pytest.raises(RuntimeError, match="primary unavailable"):
            module.Retriever().search("test")
        factory.assert_not_called()
        assert client.query_points.call_count == 1

    @patch("app.services.rag.retriever.generate_embedding", return_value=[0.1] * 384)
    def test_failing_success_log_handler_cannot_hide_dense_results(
        self, _embedding, mock_qdrant_results, monkeypatch, caplog
    ):
        from app.services.rag import retriever as module

        records = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                records.append(record)

        class FailingHandler(logging.Handler):
            def emit(self, _record):
                raise RuntimeError("PHI_HANDLER_SENTINEL")

        client, encoder = MagicMock(), MagicMock()
        shadow = MagicMock(points=mock_qdrant_results.points[:2])
        client.query_points.side_effect = [mock_qdrant_results, shadow]
        encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "SpanishBm25Encoder", lambda: encoder)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", True)
        caplog.set_level("INFO", logger=module.__name__)
        capture_handler, failing_handler = CaptureHandler(), FailingHandler()
        module.logger.addHandler(capture_handler)
        module.logger.addHandler(failing_handler)
        try:
            documents = module.Retriever().search("PHI_QUERY_SENTINEL")
        finally:
            module.logger.removeHandler(failing_handler)
            module.logger.removeHandler(capture_handler)

        assert len(documents) == 3
        messages = [record.getMessage() for record in records]
        assert len(messages) == 1
        assert "status=success" in messages[0]
        assert "status=fallback" not in messages[0]
        assert all(secret not in messages[0] for secret in (
            "PHI_QUERY_SENTINEL", "PHI_HANDLER_SENTINEL",
        ))

    @patch("app.services.rag.retriever.generate_embedding", return_value=[0.1] * 384)
    def test_shadow_post_processing_failure_falls_back_to_dense_results(
        self, _embedding, mock_qdrant_results, monkeypatch, caplog
    ):
        from app.services.rag import retriever as module

        client, encoder = MagicMock(), MagicMock()
        client.query_points.side_effect = [mock_qdrant_results, MagicMock(points=None)]
        encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
        monkeypatch.setattr(module, "get_qdrant", lambda: client)
        monkeypatch.setattr(module, "SpanishBm25Encoder", lambda: encoder)
        monkeypatch.setattr(module.settings, "retriever_hybrid_shadow_enabled", True)

        documents = module.Retriever().search("PHI_QUERY_SENTINEL")

        assert len(documents) == 3
        records = [record.getMessage() for record in caplog.records
                   if record.name == module.__name__]
        assert len(records) == 1
        assert "status=fallback" in records[0] and "exception_class=TypeError" in records[0]
        assert "status=success" not in records[0]
        assert "PHI_QUERY_SENTINEL" not in records[0]
