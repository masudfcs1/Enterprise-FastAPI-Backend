"""
Reusable pagination schemas and query parameter dependency.
"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency for extracting page / size query params."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.size = size
        self.offset = (page - 1) * size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    size: int
    total_pages: int
