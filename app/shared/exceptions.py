"""
Application exception classes and FastAPI exception handlers.
Every exception maps to a structured, consistent JSON error envelope.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ── Base Exception ────────────────────────────────────────
class AppException(Exception):
    """Base exception for all domain and HTTP application errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        error_code: str = "INTERNAL_ERROR",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.headers = headers
        super().__init__(detail)


# ── Concrete Exceptions ──────────────────────────────────
class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource", resource_id: Any = None) -> None:
        detail = (
            f"{resource} not found"
            if not resource_id
            else f"{resource} with identifier '{resource_id}' not found"
        )
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class DuplicateException(AppException):
    def __init__(self, field: str = "resource") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A record with this {field} already exists",
            error_code="DUPLICATE",
        )


class AuthenticationException(AppException):
    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(AppException):
    def __init__(
        self, detail: str = "You do not have permission to perform this action"
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR",
        )


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
        )


class DatabaseException(AppException):
    def __init__(self, detail: str = "A database error occurred") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
        )


# ── Exception Handlers ────────────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "detail": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "detail": "Request validation failed",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "detail": "An unexpected internal error occurred",
            },
        )
