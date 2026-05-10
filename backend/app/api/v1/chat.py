import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.auth.dependencies import get_current_user, get_optional_user
from app.core.llm.provider import llm_provider
from app.core.rag.reranker import rerank
from app.models.user import User
from app.services.chat_service import chat_service
from app.services.rag.retriever import retriever

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    mode: str = "student"
    area: str | None = None
    evidence_level: str | None = None
    conversation_id: str | None = None
    history: list[dict] = []


@router.post("")
async def create_chat_message(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    result = await chat_service.chat(
        query=request.query,
        area=request.area,
        evidence_level=request.evidence_level,
        mode=request.mode,
        history=request.history,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
    )
    return {"status": "success", "data": result}


@router.post("/stream")
async def create_chat_message_stream(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Stream chat response tokens via Server-Sent Events.

    Format:
      data: {"token": "word"}\n\n          — per token
      data: {"sources": [...]}\n\n          — sources after tokens
      data: [DONE]\n\n                      — completion signal
    """
    async def event_generator():
        full_response = ""
        start_time = time.time()

        # 1. Retrieve and re-rank context
        docs = retriever.search(
            query=request.query,
            area=request.area,
            evidence_level=request.evidence_level,
        )
        docs = rerank(query=request.query, documents=docs)

        # 2. Stream tokens from LLM
        async for token in llm_provider.generate_response_stream(
            query=request.query,
            context_docs=docs,
            history=request.history,
            mode=request.mode,
        ):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        response_time_ms = int((time.time() - start_time) * 1000)

        # 3. Format and send sources
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

        yield f"data: {json.dumps({'sources': sources})}\n\n"

        # 4. Signal completion
        yield "data: [DONE]\n\n"

        # 5. Persist conversation when user is authenticated
        if current_user is not None:
            from datetime import datetime
            from app.db.postgres import async_session
            from app.models.conversation import Conversation
            from app.models.message import Message
            from sqlalchemy import select

            async with async_session() as session:
                if request.conversation_id:
                    conv_result = await session.execute(
                        select(Conversation).where(
                            Conversation.id == request.conversation_id,
                            Conversation.user_id == current_user.id,
                        )
                    )
                    conversation = conv_result.scalar_one_or_none()
                    if not conversation:
                        conversation = Conversation(
                            user_id=current_user.id, mode=request.mode
                        )
                        session.add(conversation)
                        await session.flush()
                else:
                    conversation = Conversation(
                        user_id=current_user.id, mode=request.mode
                    )
                    session.add(conversation)
                    await session.flush()

                if conversation.title == "Nueva conversación":
                    query = request.query
                    conversation.title = query[:100] + ("..." if len(query) > 100 else "")

                user_msg = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=request.query,
                )
                session.add(user_msg)

                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    sources=sources,
                    response_time_ms=response_time_ms,
                )
                session.add(assistant_msg)

                conversation.updated_at = datetime.utcnow()
                await session.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
):
    conversations = await chat_service.get_conversations(user_id=current_user.id)
    return {"status": "success", "data": conversations}


@router.get("/history/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await chat_service.get_conversation_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )
    return {"status": "success", "data": result}


@router.delete("/history/{conversation_id}")
async def delete_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    deleted = await chat_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )
    return {"status": "success", "message": "Conversación eliminada"}
