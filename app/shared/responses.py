"""
Consistent API response wrappers.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all successful responses."""
    success: bool = True
    message: str = "OK"
    data: T | None = None


class APIListResponse(BaseModel, Generic[T]):
    """Standard envelope for paginated list responses."""
    success: bool = True
    message: str = "OK"
    data: list[T] = []
    total: int = 0
    page: int = 1
    size: int = 20
    total_pages: int = 0
