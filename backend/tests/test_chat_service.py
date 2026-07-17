# ruff: noqa: E501
from unittest.mock import AsyncMock, patch

import pytest


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
                        "evidence_level": "book",
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
