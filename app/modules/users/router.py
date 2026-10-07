"""
User router — presentation layer for user account endpoints.
Exposes REST endpoints that delegate execution to UserService.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from prisma import Prisma

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_active_user, require_roles
from app.modules.users.repository import UserRepository
from app.modules.users.schema import (
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserUpdateRole,
)
from app.modules.users.service import UserService
from app.shared.constants import SortOrder, UserRole
from app.shared.exceptions import AuthorizationException
from app.shared.responses import APIListResponse, APIResponse

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore

router = APIRouter(prefix="/users", tags=["Users"])


def _get_service(db: Prisma = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


# ── GET /users ────────────────────────────────────────────
@router.get(
    "",
    response_model=APIListResponse[UserListResponse],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)
async def list_users(
    service: UserService = Depends(_get_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search query"),
    role: str | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sort direction"),
) -> APIListResponse[UserListResponse]:
    result = await service.get_users(
        page=page,
        size=size,
        search=search,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )
    return APIListResponse(
        data=[UserListResponse.model_validate(u) for u in result["items"]],
        total=result["total"],
        page=result["page"],
        size=result["size"],
        total_pages=result["total_pages"],
    )


# ── GET /users/me ─────────────────────────────────────────
@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> APIResponse[UserResponse]:
    return APIResponse(data=UserResponse.model_validate(current_user))


# ── GET /users/{id} ───────────────────────────────────────
@router.get(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)
async def get_user(
    user_id: str,
    service: UserService = Depends(_get_service),
) -> APIResponse[UserResponse]:
    user = await service.get_user_by_id(user_id)
    return APIResponse(data=UserResponse.model_validate(user))


# ── PATCH /users/{id} ────────────────────────────────────
@router.patch("/{user_id}", response_model=APIResponse[UserResponse])
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_service),
) -> APIResponse[UserResponse]:
    # Users can only update their own record unless they are an admin
    current_role = getattr(current_user, "role", "")
    if current_user.id != user_id and current_role not in (
        UserRole.ADMIN.value,
        UserRole.SUPER_ADMIN.value,
    ):
        raise AuthorizationException()

    user = await service.update_user(user_id, data)
    return APIResponse(data=UserResponse.model_validate(user), message="User updated successfully")


# ── PATCH /users/{id}/role ────────────────────────────────
@router.patch(
    "/{user_id}/role",
    response_model=APIResponse[UserResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def update_user_role(
    user_id: str,
    data: UserUpdateRole,
    service: UserService = Depends(_get_service),
) -> APIResponse[UserResponse]:
    user = await service.update_user_role(user_id, data)
    return APIResponse(data=UserResponse.model_validate(user), message="Role updated successfully")


# ── DELETE /users/{id} ────────────────────────────────────
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def delete_user(
    user_id: str,
    service: UserService = Depends(_get_service),
) -> APIResponse[None]:
    await service.delete_user(user_id)
    return APIResponse(message="User deleted successfully")
