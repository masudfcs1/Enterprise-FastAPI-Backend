"""
User repository — data access layer using Prisma Client.
Handles all queries, filters, pagination, and persistence for users.
"""

from typing import Any

from prisma import Prisma

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore


class UserRepository:
    def __init__(self, db: Prisma) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """Find a single user by primary key ID."""
        return await self.db.user.find_unique(where={"id": user_id})

    async def get_by_email(self, email: str) -> User | None:
        """Find a single user by email address."""
        return await self.db.user.find_unique(where={"email": email})

    async def get_by_username(self, username: str) -> User | None:
        """Find a single user by username."""
        return await self.db.user.find_unique(where={"username": username})

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """
        List users with filtering, searching, sorting, and total count.
        """
        where: dict[str, Any] = {}

        if search:
            where["OR"] = [
                {"email": {"contains": search, "mode": "insensitive"}},
                {"username": {"contains": search, "mode": "insensitive"}},
                {"first_name": {"contains": search, "mode": "insensitive"}},
                {"last_name": {"contains": search, "mode": "insensitive"}},
            ]

        if role:
            where["role"] = role

        if is_active is not None:
            where["is_active"] = is_active

        order = {sort_by: sort_order}

        users = await self.db.user.find_many(
            where=where,
            skip=offset,
            take=limit,
            order=order,
        )
        total = await self.db.user.count(where=where)
        return users, total

    async def create(self, data: dict[str, Any]) -> User:
        """Persist a new user record."""
        return await self.db.user.create(data=data)

    async def update(self, user_id: str, data: dict[str, Any]) -> User:
        """Update an existing user record."""
        return await self.db.user.update(where={"id": user_id}, data=data)

    async def delete(self, user_id: str) -> None:
        """Delete user record by ID."""
        await self.db.user.delete(where={"id": user_id})
