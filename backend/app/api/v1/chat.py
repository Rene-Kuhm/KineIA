from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def create_chat_message():
    return {"status": "not_implemented", "message": "Chat endpoint - Fase 2"}


@router.get("/history")
async def get_chat_history():
    return {"status": "not_implemented", "message": "History endpoint - Fase 2"}
