from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuthService:
    @pytest.fixture(autouse=True)
    def mock_session(self):
        """Mock the async DB session for all auth tests."""
        with patch("app.services.auth_service.async_session") as mock_session_maker:
            mock_session = MagicMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.flush = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.delete = AsyncMock()
            yield mock_session

    @pytest.mark.asyncio
    async def test_register_creates_user(self, mock_session):
        """Registration should create a new user and return a token."""
        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        from app.services.auth_service import auth_service

        result = await auth_service.register(
            email="test@example.com",
            password="secure_password_123",
            full_name="Test User",
            role="student",
        )

        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["full_name"] == "Test User"
        assert result["user"]["role"] == "student"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(self, mock_session):
        """Registration with existing email should raise 400."""
        mock_user = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from fastapi import HTTPException

        from app.services.auth_service import auth_service

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(
                email="existing@example.com",
                password="password123",
                full_name="Existing User",
            )

        assert exc_info.value.status_code == 400
        assert "registrado" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, mock_session):
        """Login with valid credentials should return a token."""
        from app.core.auth.dependencies import get_password_hash
        from app.services.auth_service import auth_service

        # Create a mock user with hashed password
        mock_user = MagicMock()
        mock_user.id = "user-uuid-123"
        mock_user.email = "login@example.com"
        mock_user.full_name = "Login User"
        mock_user.role = "student"
        mock_user.is_active = True
        mock_user.hashed_password = get_password_hash("correct_password")
        mock_user.created_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await auth_service.login(
            email="login@example.com",
            password="correct_password",
        )

        assert "access_token" in result
        assert result["user"]["email"] == "login@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_session):
        """Login with wrong password should raise 401."""
        from fastapi import HTTPException

        from app.core.auth.dependencies import get_password_hash
        from app.services.auth_service import auth_service

        mock_user = MagicMock()
        mock_user.hashed_password = get_password_hash("correct_password")
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(
                email="test@example.com",
                password="wrong_password",
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Email o contraseña incorrectos"

    @pytest.mark.asyncio
    async def test_login_malformed_password_hash_returns_generic_401(self, mock_session):
        """Malformed stored hashes should be indistinguishable from wrong credentials."""
        mock_user = MagicMock()
        mock_user.hashed_password = "not-a-passlib-hash"
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from fastapi import HTTPException

        from app.services.auth_service import auth_service

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(
                email="test@example.com",
                password="any_password",
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Email o contraseña incorrectos"

    def test_password_verification_does_not_hide_unexpected_errors(self):
        from app.core.auth import dependencies

        with patch.object(
            dependencies.pwd_context,
            "verify",
            side_effect=RuntimeError("unexpected verification failure"),
        ):
            with pytest.raises(RuntimeError, match="unexpected verification failure"):
                dependencies.verify_password("password", "hash")

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, mock_session):
        """Login with non-existent email should raise 401."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        from fastapi import HTTPException

        from app.services.auth_service import auth_service

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(
                email="nonexistent@example.com",
                password="any_password",
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_profile(self, mock_session):
        """Get profile should return user data."""
        mock_user = MagicMock()
        mock_user.id = "user-id"
        mock_user.email = "profile@example.com"
        mock_user.full_name = "Profile User"
        mock_user.role = "professional"
        mock_user.is_active = True
        mock_user.created_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from app.services.auth_service import auth_service

        result = await auth_service.get_profile(user_id="user-id")

        assert result["email"] == "profile@example.com"
        assert result["role"] == "professional"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_update_profile(self, mock_session):
        """Update profile should change the full_name."""
        mock_user = MagicMock()
        mock_user.id = "user-id"
        mock_user.full_name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from app.services.auth_service import auth_service

        result = await auth_service.update_profile(
            user_id="user-id",
            full_name="New Name",
        )

        assert mock_user.full_name == "New Name"
        assert result["full_name"] == "New Name"
        mock_session.commit.assert_called_once()
