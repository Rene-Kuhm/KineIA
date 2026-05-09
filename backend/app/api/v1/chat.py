from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.services.chat_service import chat_service

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
