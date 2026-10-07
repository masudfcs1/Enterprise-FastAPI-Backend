"""
Product router — presentation endpoints for product management and catalog queries.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from prisma import Prisma

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.products.repository import ProductRepository
from app.modules.products.schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.modules.products.service import ProductService
from app.shared.constants import SortOrder
from app.shared.responses import APIListResponse, APIResponse

try:
    from prisma.models import User
except (ImportError, AttributeError):
    User = Any  # type: ignore

router = APIRouter(prefix="/products", tags=["Products"])


def _get_service(db: Prisma = Depends(get_db)) -> ProductService:
    return ProductService(ProductRepository(db))


# ── GET /products ─────────────────────────────────────────
@router.get(
    "",
    response_model=APIListResponse[ProductResponse],
    summary="List products with filters and pagination",
)
async def list_products(
    service: ProductService = Depends(_get_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search by title or description"),
    is_active: bool | None = Query(default=None, description="Filter active status"),
    owner_id: str | None = Query(default=None, description="Filter by creator ID"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sort direction"),
) -> APIListResponse[ProductResponse]:
    result = await service.get_products(
        page=page,
        size=size,
        search=search,
        is_active=is_active,
        owner_id=owner_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order.value,
    )
    return APIListResponse(
        data=[ProductResponse.model_validate(p) for p in result["items"]],
        total=result["total"],
        page=result["page"],
        size=result["size"],
        total_pages=result["total_pages"],
    )


# ── POST /products ────────────────────────────────────────
@router.post(
    "",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    service: ProductService = Depends(_get_service),
) -> APIResponse[ProductResponse]:
    product = await service.create_product(data=data, owner_id=current_user.id)
    return APIResponse(
        data=ProductResponse.model_validate(product),
        message="Product created successfully",
    )


# ── GET /products/{id} ────────────────────────────────────
@router.get(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Retrieve single product by ID",
)
async def get_product(
    product_id: str,
    service: ProductService = Depends(_get_service),
) -> APIResponse[ProductResponse]:
    product = await service.get_product_by_id(product_id)
    return APIResponse(data=ProductResponse.model_validate(product))


# ── PATCH /products/{id} ──────────────────────────────────
@router.patch(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Update product details (owner or admin only)",
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ProductService = Depends(_get_service),
) -> APIResponse[ProductResponse]:
    current_role = getattr(current_user, "role", "")
    if hasattr(current_role, "value"):
        current_role = current_role.value

    product = await service.update_product(
        product_id=product_id,
        data=data,
        current_user_id=current_user.id,
        current_user_role=current_role,
    )
    return APIResponse(
        data=ProductResponse.model_validate(product),
        message="Product updated successfully",
    )


# ── DELETE /products/{id} ─────────────────────────────────
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product (owner or admin only)",
)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ProductService = Depends(_get_service),
) -> APIResponse[None]:
    current_role = getattr(current_user, "role", "")
    if hasattr(current_role, "value"):
        current_role = current_role.value

    await service.delete_product(
        product_id=product_id,
        current_user_id=current_user.id,
        current_user_role=current_role,
    )
    return APIResponse(message="Product deleted successfully")
