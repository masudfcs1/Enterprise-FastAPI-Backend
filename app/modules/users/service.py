"""
User service — business logic layer for user operations.
Applies domain invariants, validation rules, and coordinates with UserRepository.
"""

from typing import Any

from app.core.security import hash_password
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserUpdate, UserUpdateRole
from app.shared.constants import UserRole
from app.shared.exceptions import DuplicateException, NotFoundException

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def create_user(self, data: UserCreate) -> User:
        """Register a new user — ensures email and username uniqueness."""
        if await self.repo.get_by_email(data.email):
            raise DuplicateException(field="email")
        if await self.repo.get_by_username(data.username):
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
        return await self.repo.create(user_data)

    async def get_user_by_id(self, user_id: str) -> User:
        """Fetch user by ID or raise NotFoundException."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(resource="User", resource_id=user_id)
        return user

    async def get_users(
        self,
        *,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Fetch paginated users with metadata."""
        offset = (page - 1) * size
        users, total = await self.repo.get_all(
            offset=offset,
            limit=size,
            search=search,
            role=role,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total_pages = (total + size - 1) // size if total > 0 else 0
        return {
            "items": users,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }

    async def update_user(self, user_id: str, data: UserUpdate) -> User:
        """Update user profile fields with conflict checks."""
        user = await self.get_user_by_id(user_id)

        if data.email and data.email != user.email:
            existing = await self.repo.get_by_email(data.email)
            if existing:
                raise DuplicateException(field="email")

        if data.username and data.username != user.username:
            existing = await self.repo.get_by_username(data.username)
            if existing:
                raise DuplicateException(field="username")

        update_payload = data.model_dump(exclude_unset=True)
        if not update_payload:
            return user

        return await self.repo.update(user_id, update_payload)

    async def update_user_role(self, user_id: str, data: UserUpdateRole) -> User:
        """Update role for administrative privileges."""
        await self.get_user_by_id(user_id)
        return await self.repo.update(user_id, {"role": data.role.value})

    async def delete_user(self, user_id: str) -> None:
        """Permanently delete user record."""
        await self.get_user_by_id(user_id)
        await self.repo.delete(user_id)

    async def deactivate_user(self, user_id: str) -> User:
        """Soft deactivate user account."""
        await self.get_user_by_id(user_id)
        return await self.repo.update(user_id, {"is_active": False})
