from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.core.auth.dependencies import get_current_user, require_role
from app.models.user import User
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None


@router.post("/register")
async def register(request: RegisterRequest):
    return await auth_service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
    )


@router.post("/login")
async def login(request: LoginRequest):
    return await auth_service.login(email=request.email, password=request.password)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return await auth_service.get_profile(current_user.id)


@router.put("/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
):
    return await auth_service.update_profile(current_user.id, full_name=request.full_name)


@router.get("/users")
async def list_users(
    current_user: User = Depends(require_role(["admin"])),
):
    return {"status": "not_implemented", "message": "List users - requires pagination"}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(require_role(["admin"])),
):
    return {"status": "not_implemented", "message": f"Update role to {role}"}