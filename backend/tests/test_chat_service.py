# ruff: noqa: E501
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _reject_str(self):
    raise AssertionError("exception details were serialized")


class FailingHandler(logging.Handler):
    def emit(self, record):
        raise RuntimeError("LOG-HANDLER-SENSITIVE")


class TestChatService:
    @pytest.fixture(autouse=True)
    def mock_retriever(self):
        with patch("app.services.chat_service.retriever") as mock_ret:
            mock_ret.search.return_value = [
                {
                    "text": "Documento sobre kinesiología aplicada.",
                    "metadata": {
                        "title": "Manual de Kinesiología",
                        "source": "UBA",
                        "original_source_name": "manual.md",
                        "evidence_level": "book",
                        "fragment_hash": "a" * 64,
                        "section_heading": "Rodilla",
                        "section_path": ["Miembro inferior", "Rodilla"],
                    },
                    "score": 0.95,
                    "rerank_score": 0.99,
                    "retrieval_mode": "hybrid", "score_type": "rrf",
                },
                {
                    "text": "Guía de rehabilitación para LCA.",
                    "metadata": {
                        "title": "Protocolo LCA",
                        "source": "Hospital Clínicas",
                        "evidence_level": "protocol",
                    },
                    "score": 0.88,
                },
            ]
            yield mock_ret

    @pytest.fixture(autouse=True)
    def mock_reranker(self):
        with patch("app.services.chat_service.rerank", side_effect=lambda query, documents: documents) as mock_rer:
            yield mock_rer

    @pytest.fixture(autouse=True)
    def mock_llm(self):
        with patch("app.services.chat_service.llm_provider") as mock_llm:
            mock_llm.generate_response = AsyncMock(
                return_value=(
                    "La kinesiología es una disciplina que estudia el movimiento "
                    "humano y su relación con la salud."
                )
            )
            yield mock_llm

    @pytest.mark.asyncio
    async def test_chat_returns_answer_and_sources(self):
        """Chat should return an answer with formatted sources."""
        from app.services.chat_service import chat_service

        result = await chat_service.chat(
            query="¿Qué es la kinesiología?",
            mode="student",
        )

        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
        assert len(result["sources"]) > 0
        assert "title" in result["sources"][0]
        assert "evidence_level" in result["sources"][0]
        assert "score" in result["sources"][0]

    @pytest.mark.asyncio
    async def test_sync_and_stream_share_exact_citation_contract(self, mock_retriever):
        from app.api.v1.chat import ChatRequest, create_chat_message_stream
        from app.services.chat_service import chat_service

        async def stream(**_kwargs):
            yield "answer"

        session, manager = AsyncMock(), AsyncMock()
        session.add = MagicMock()
        manager.__aenter__.return_value = session
        with patch("app.services.chat_service.async_session", return_value=manager):
            sync = await chat_service.chat(query="test", user_id="user-1")
        http_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(retriever=mock_retriever)))
        with (patch("app.api.v1.chat.rerank", side_effect=lambda query, documents: documents),
              patch("app.api.v1.chat.llm_provider.generate_response_stream", new=stream)):
            response = await create_chat_message_stream(ChatRequest(query="test"), http_request, current_user=None)
            events = [chunk async for chunk in response.body_iterator]
        streamed = next(json.loads(event[6:])["sources"] for event in events if '"sources"' in event)

        assistant = next(call.args[0] for call in session.add.call_args_list if getattr(call.args[0], "role", None) == "assistant")
        assert streamed == sync["sources"] == assistant.sources
        assert streamed[0]["fragment_hash"] == "a" * 64
        assert streamed[0]["page_start"] is streamed[0]["page_end"] is None

    @pytest.mark.asyncio
    async def test_history_normalizes_legacy_sources_before_returning_them(self):
        from app.services.chat_service import chat_service
        from app.services.rag.citations import format_sources

        conversation = SimpleNamespace(id="c1", title="History", mode="student", created_at=None, updated_at=None)
        legacy = {"title": "/private/guide.md", "source": "/private/guide.md", "url": "file:///private/guide.md", "fragment_hash": "forged"}
        messages = [SimpleNamespace(id=f"m{i}", role="assistant", content="answer", sources=sources,
                    tokens_used=None, response_time_ms=1, created_at=None)
                    for i, sources in enumerate(([legacy], None, {}, legacy))]
        first, second = MagicMock(), MagicMock()
        first.scalar_one_or_none.return_value = conversation
        second.scalars.return_value.all.return_value = messages
        session = AsyncMock()
        session.execute.side_effect = [first, second]
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        with patch("app.services.chat_service.async_session", return_value=manager):
            result = await chat_service.get_conversation_messages("c1", "user-1")

        returned = [item["sources"] for item in result["messages"]]
        source = returned[0][0]
        assert source == format_sources([legacy])[0]
        assert source["source"] == source["title"] == "guide.md"
        assert source["url"] is source["fragment_hash"] is None
        assert returned[1:3] == [[], []] and returned[3] == [source]

    @pytest.mark.asyncio
    async def test_chat_passes_mode_to_llm(self, mock_llm):
        """The mode parameter should be passed to the LLM provider."""
        from app.services.chat_service import chat_service

        await chat_service.chat(query="test query", mode="professional")

        call_kwargs = mock_llm.generate_response.call_args[1]
        assert call_kwargs["mode"] == "professional"

    @pytest.mark.asyncio
    async def test_chat_passes_history_to_llm(self, mock_llm):
        """Chat history should be forwarded to the LLM provider."""
        from app.services.chat_service import chat_service

        history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"},
        ]

        await chat_service.chat(query="Siguiente pregunta", history=history)

        call_kwargs = mock_llm.generate_response.call_args[1]
        assert call_kwargs["history"] == history

    @pytest.mark.asyncio
    async def test_chat_without_user_id_does_not_persist(self):
        """Chat without user_id should not attempt DB persistence."""
        from app.services.chat_service import chat_service

        result = await chat_service.chat(
            query="Pregunta sin autenticación",
            user_id=None,
        )

        assert "answer" in result
        assert "conversation_id" not in result

    @pytest.mark.asyncio
    async def test_chat_hides_llm_failure_details(self, mock_llm, caplog):
        """LLM failures should expose only a stable public reason code."""
        from app.services.chat_service import chat_service

        sentinel = "sk-live-SENSITIVE https://internal.example request-id=secret-7F9C prompt=patient-data GROQ_API_KEY=.env Traceback"
        unsafe_error = type("Secret\nInjected", (RuntimeError,), {"__str__": _reject_str})
        mock_llm.generate_response.side_effect = unsafe_error(sentinel)

        result = await chat_service.chat(query="test query")

        assert result["answer"] == "⚠️ No pude generar una respuesta porque el servicio de IA no está disponible. Intentá nuevamente más tarde.\n\nCódigo: AI_SERVICE_UNAVAILABLE"
        assert sentinel not in result["answer"] + caplog.text
        assert not any(value in result["answer"] + caplog.text for value in ("sk-live", "internal.example", "secret-7F9C", "patient-data", "GROQ_API_KEY", ".env", "Traceback"))
        diagnostic = next(record for record in caplog.records
                          if record.getMessage() == "llm_generation_failed")
        assert diagnostic.reason_code == "AI_SERVICE_UNAVAILABLE"
        assert diagnostic.exception_class == "Exception"
        assert len(diagnostic.correlation_id) == 32
        assert diagnostic.exc_info is None

    @pytest.mark.asyncio
    async def test_stream_failure_emits_one_terminal_safe_error(self, mock_retriever, caplog):
        """A failed stream ends with one safe event and is not persisted."""
        from app.api.v1.chat import ChatRequest, create_chat_message_stream
        from app.services.chat_service import logger

        sentinel = "sk-live-STREAM-SENSITIVE"

        malicious_error = type("Secret\nStream", (Exception,), {"__str__": _reject_str})

        async def failing_stream(**kwargs):
            yield "partial"
            raise malicious_error(sentinel)

        request = ChatRequest(query="test query")
        http_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(retriever=mock_retriever)))
        handler = FailingHandler()
        logger.addHandler(handler)
        try:
            with (
                patch("app.api.v1.chat.rerank", side_effect=lambda query, documents: documents),
                patch("app.api.v1.chat.llm_provider.generate_response_stream", new=failing_stream),
                patch("app.db.postgres.async_session") as db_session,
            ):
                response = await create_chat_message_stream(
                    request, http_request, current_user=SimpleNamespace(id="user-1"))
                chunks = [chunk async for chunk in response.body_iterator]
        finally:
            logger.removeHandler(handler)

        assert json.loads(chunks[0][6:]) == {"token": "partial"}
        error = json.loads(chunks[1][6:])["error"]
        assert error["code"] == "AI_SERVICE_UNAVAILABLE"
        assert error["message"].endswith("Intentá nuevamente más tarde.")
        assert len(error["correlation_id"]) == 32
        assert all(secret not in "".join(chunks) + caplog.text for secret in (sentinel, "LOG-HANDLER-SENSITIVE", "Traceback"))
        assert len(chunks) == 2 and all("[DONE]" not in chunk for chunk in chunks)
        db_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_with_area_filter(self, mock_retriever):
        """Area filter should be passed to the retriever."""
        from app.services.chat_service import chat_service

        await chat_service.chat(query="test", area="kinesiologia")

        call_kwargs = mock_retriever.search.call_args[1]
        assert call_kwargs["area"] == "kinesiologia"

    @pytest.mark.asyncio
    async def test_chat_with_evidence_level_filter(self, mock_retriever):
        """Evidence_level filter should be passed to the retriever."""
        from app.services.chat_service import chat_service

        await chat_service.chat(query="test", evidence_level="protocol")

        call_kwargs = mock_retriever.search.call_args[1]
        assert call_kwargs["evidence_level"] == "protocol"

    @pytest.mark.asyncio
    async def test_chat_sources_include_score(self):
        """Sources should include the retrieval/re-rank score."""
        from app.services.chat_service import chat_service

        result = await chat_service.chat(query="test query")

        for source in result["sources"]:
            assert "score" in source
            assert isinstance(source["score"], (int, float))
        assert result["sources"][0]["score"] == 0.95
        assert (result["sources"][0]["retrieval_mode"],
                result["sources"][0]["score_type"]) == ("hybrid", "rrf")
