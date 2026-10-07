"""
Auth router — presentation endpoints for registration, login, token refresh, and logout.
"""

from fastapi import APIRouter, Depends, status
from prisma import Prisma

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.repository import UserRepository
from app.shared.responses import APIResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_service(db: Prisma = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        auth_repo=AuthRepository(db),
    )


# ── POST /auth/register ───────────────────────────────────
@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(_get_service),
) -> APIResponse[TokenResponse]:
    tokens = await service.register(data)
    return APIResponse(
        data=TokenResponse(**tokens),
        message="Registration successful",
    )


# ── POST /auth/login ──────────────────────────────────────
@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> APIResponse[TokenResponse]:
    tokens = await service.login(email=data.email, password=data.password)
    return APIResponse(
        data=TokenResponse(**tokens),
        message="Login successful",
    )


# ── POST /auth/refresh ────────────────────────────────────
@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token for fresh tokens",
)
async def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(_get_service),
) -> APIResponse[TokenResponse]:
    tokens = await service.refresh(data.refresh_token)
    return APIResponse(
        data=TokenResponse(**tokens),
        message="Token refreshed successfully",
    )


# ── POST /auth/logout ─────────────────────────────────────
@router.post(
    "/logout",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Invalidate refresh token session",
)
async def logout(
    data: RefreshTokenRequest,
    service: AuthService = Depends(_get_service),
    _current_user=Depends(get_current_user),
) -> APIResponse[None]:
    await service.logout(data.refresh_token)
    return APIResponse(message="Logged out successfully")
