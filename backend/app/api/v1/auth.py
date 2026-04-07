from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register():
    return {"status": "not_implemented", "message": "Register endpoint - Fase 4"}


@router.post("/login")
async def login():
    return {"status": "not_implemented", "message": "Login endpoint - Fase 4"}
