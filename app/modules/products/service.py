"""
Product service — domain business logic layer for product operations.
Enforces business invariants, SKU uniqueness, and ownership rules.
"""

from typing import Any

from app.modules.products.repository import ProductRepository
from app.modules.products.schema import ProductCreate, ProductUpdate
from app.shared.constants import UserRole
from app.shared.exceptions import (
    AuthorizationException,
    DuplicateException,
    NotFoundException,
)

try:
    from prisma.models import Product
except (ImportError, AttributeError):
    Product = Any  # type: ignore


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    async def create_product(self, data: ProductCreate, owner_id: str) -> Product:
        """Create a new product ensuring unique SKU."""
        if await self.repo.get_by_sku(data.sku):
            raise DuplicateException(field="sku")

        product_data = {
            "title": data.title,
            "description": data.description,
            "price": data.price,
            "sku": data.sku,
            "quantity": data.quantity,
            "owner_id": owner_id,
            "is_active": True,
        }
        return await self.repo.create(product_data)

    async def get_product_by_id(self, product_id: str) -> Product:
        """Fetch product by ID or raise NotFoundException."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(resource="Product", resource_id=product_id)
        return product

    async def get_products(
        self,
        *,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        owner_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Fetch paginated products with filtering options."""
        offset = (page - 1) * size
        products, total = await self.repo.get_all(
            offset=offset,
            limit=size,
            search=search,
            is_active=is_active,
            owner_id=owner_id,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total_pages = (total + size - 1) // size if total > 0 else 0
        return {
            "items": products,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }

    async def update_product(
        self,
        product_id: str,
        data: ProductUpdate,
        current_user_id: str,
        current_user_role: str,
    ) -> Product:
        """Update a product; requires ownership or admin privileges."""
        product = await self.get_product_by_id(product_id)

        # Ownership authorization check
        if product.owner_id != current_user_id and current_user_role not in (
            UserRole.ADMIN.value,
            UserRole.SUPER_ADMIN.value,
        ):
            raise AuthorizationException()

        # SKU conflict check if updating SKU
        if data.sku and data.sku != product.sku:
            existing = await self.repo.get_by_sku(data.sku)
            if existing:
                raise DuplicateException(field="sku")

        update_payload = data.model_dump(exclude_unset=True)
        if not update_payload:
            return product

        return await self.repo.update(product_id, update_payload)

    async def delete_product(
        self,
        product_id: str,
        current_user_id: str,
        current_user_role: str,
    ) -> None:
        """Delete a product; requires ownership or admin privileges."""
        product = await self.get_product_by_id(product_id)

        if product.owner_id != current_user_id and current_user_role not in (
            UserRole.ADMIN.value,
            UserRole.SUPER_ADMIN.value,
        ):
            raise AuthorizationException()

        await self.repo.delete(product_id)
