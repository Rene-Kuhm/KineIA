from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.auth.dependencies import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.postgres import async_session
from app.models.user import User


class AuthService:
    async def register(self, email: str, password: str, full_name: str, role: str = "student") -> dict:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado",
                )
            
            hashed_password = get_password_hash(password)
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=role,
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            access_token = create_access_token(
                data={"sub": new_user.id, "role": new_user.role},
                expires_delta=timedelta(days=7),
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "full_name": new_user.full_name,
                    "role": new_user.role,
                },
            }

    async def login(self, email: str, password: str) -> dict:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user or not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos",
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuario inactivo",
                )
            
            access_token = create_access_token(
                data={"sub": user.id, "role": user.role},
                expires_delta=timedelta(days=7),
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                },
            }

    async def get_profile(self, user_id: str) -> dict:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

    async def update_profile(self, user_id: str, full_name: str | None = None) -> dict:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            
            if full_name:
                user.full_name = full_name
            
            await session.commit()
            await session.refresh(user)
            
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }


auth_service = AuthService()