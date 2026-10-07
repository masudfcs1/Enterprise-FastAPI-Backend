"""
Auth service — orchestrates registration, authentication, token refresh, and logout.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import RegisterRequest
from app.modules.users.repository import UserRepository
from app.shared.constants import UserRole
from app.shared.exceptions import AuthenticationException, DuplicateException

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore


class AuthService:
    def __init__(self, user_repo: UserRepository, auth_repo: AuthRepository) -> None:
        self.user_repo = user_repo
        self.auth_repo = auth_repo

    async def register(self, data: RegisterRequest) -> dict[str, str]:
        """Create a new user and issue an initial JWT token pair."""
        if await self.user_repo.get_by_email(data.email):
            raise DuplicateException(field="email")
        if await self.user_repo.get_by_username(data.username):
            raise DuplicateException(field="username")

        user_data = {
            "email": data.email,
            "username": data.username,
            "password_hash": hash_password(data.password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "role": UserRole.USER.value,
            "is_active": True,
        }
        user = await self.user_repo.create(user_data)
        return await self._issue_tokens(user)

    async def login(self, email: str, password: str) -> dict[str, str]:
        """Verify user credentials and issue a new JWT token pair."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationException(detail="Invalid email or password")

        if not user.is_active:
            raise AuthenticationException(detail="Account is deactivated")

        return await self._issue_tokens(user)

    async def refresh(self, refresh_token_str: str) -> dict[str, str]:
        """Rotate refresh token and issue a fresh access/refresh token pair."""
        stored = await self.auth_repo.get_refresh_token(refresh_token_str)
        if not stored or stored.revoked:
            raise AuthenticationException(detail="Invalid or revoked refresh token")

        expires_at = (
            stored.expires_at
            if stored.expires_at.tzinfo
            else stored.expires_at.replace(tzinfo=timezone.utc)
        )
        if expires_at < datetime.now(timezone.utc):
            await self.auth_repo.revoke_token(refresh_token_str)
            raise AuthenticationException(detail="Refresh token has expired")

        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise AuthenticationException(detail="Invalid token type")
        except JWTError:
            raise AuthenticationException(detail="Invalid refresh token")

        # Invalidate old token (Rotation)
        await self.auth_repo.revoke_token(refresh_token_str)

        user = await self.user_repo.get_by_id(stored.user_id)
        if not user or not user.is_active:
            raise AuthenticationException(detail="User not found or deactivated")

        return await self._issue_tokens(user)

    async def logout(self, refresh_token_str: str) -> None:
        """Revoke a refresh token to log out the user session."""
        try:
            await self.auth_repo.revoke_token(refresh_token_str)
        except Exception:
            pass

    async def _issue_tokens(self, user: User) -> dict[str, str]:
        """Issue access and refresh tokens and persist the refresh token."""
        user_role = getattr(user, "role", UserRole.USER.value)
        if hasattr(user_role, "value"):
            user_role = user_role.value

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": user_role},
        )
        refresh_token = create_refresh_token(subject=user.id)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.auth_repo.save_refresh_token(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
