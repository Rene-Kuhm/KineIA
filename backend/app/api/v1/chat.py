from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    mode: str = "student"
    area: str | None = None
    evidence_level: str | None = None
    history: list[dict] = []


@router.post("")
async def create_chat_message(request: ChatRequest):
    result = await chat_service.chat(
        query=request.query,
        area=request.area,
        evidence_level=request.evidence_level,
        mode=request.mode,
        history=request.history,
    )
    return {"status": "success", "data": result}


@router.get("/history")
async def get_chat_history():
    return {"status": "not_implemented", "message": "History endpoint - Fase 2"}
