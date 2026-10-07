"""
Auth repository — token persistence and revocation using Prisma Client.
"""

from datetime import datetime
from typing import Any

from prisma import Prisma

try:
    from prisma.models import RefreshToken
except (ImportError, AttributeError):
    RefreshToken = Any  # type: ignore


class AuthRepository:
    def __init__(self, db: Prisma) -> None:
        self.db = db

    async def save_refresh_token(
        self, token: str, user_id: str, expires_at: datetime
    ) -> RefreshToken:
        """Store an issued refresh token in the database."""
        return await self.db.refreshtoken.create(
            data={
                "token": token,
                "user_id": user_id,
                "expires_at": expires_at,
                "revoked": False,
            }
        )

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        """Fetch a refresh token record by token string."""
        return await self.db.refreshtoken.find_unique(where={"token": token})

    async def revoke_token(self, token: str) -> None:
        """Mark a specific refresh token as revoked."""
        await self.db.refreshtoken.update(
            where={"token": token},
            data={"revoked": True},
        )

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all active refresh tokens belonging to a user."""
        await self.db.refreshtoken.update_many(
            where={"user_id": user_id, "revoked": False},
            data={"revoked": True},
        )
