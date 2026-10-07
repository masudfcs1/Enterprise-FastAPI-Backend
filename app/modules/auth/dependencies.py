"""
Auth dependencies — JWT extraction, current user resolution, and role-based access control.
"""

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from prisma import Prisma

from app.core.database import get_db
from app.core.security import decode_token
from app.modules.users.repository import UserRepository
from app.shared.constants import UserRole
from app.shared.exceptions import AuthenticationException, AuthorizationException

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Prisma = Depends(get_db),
) -> User:
    """
    Extract JWT Bearer token, decode it, and retrieve the authenticated User.
    """
    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if not user_id or token_type != "access":
            raise AuthenticationException(detail="Invalid authentication token")
    except (JWTError, ValueError):
        raise AuthenticationException(detail="Could not validate credentials")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException(detail="User does not exist")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that the authenticated user account is currently active."""
    if not current_user.is_active:
        raise AuthenticationException(detail="User account is deactivated")
    return current_user


def require_roles(*roles: UserRole) -> Callable:
    """
    FastAPI dependency factory enforcing role-based access control.

    Example:
        dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))]
    """
    role_values = [r.value if hasattr(r, "value") else str(r) for r in roles]

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role = getattr(current_user, "role", "")
        if hasattr(user_role, "value"):
            user_role = user_role.value

        if user_role not in role_values:
            raise AuthorizationException()
        return current_user

    return role_checker
