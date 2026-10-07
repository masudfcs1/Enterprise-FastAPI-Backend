"""
Product repository — data access layer using Prisma Client.
Handles querying, filtering, pagination, and persistence for products.
"""

from typing import Any

from prisma import Prisma

try:
    from prisma.models import Product
except (ImportError, AttributeError):
    Product = Any  # type: ignore


class ProductRepository:
    def __init__(self, db: Prisma) -> None:
        self.db = db

    async def get_by_id(self, product_id: str) -> Product | None:
        """Find product by unique ID."""
        return await self.db.product.find_unique(where={"id": product_id})

    async def get_by_sku(self, sku: str) -> Product | None:
        """Find product by SKU."""
        return await self.db.product.find_unique(where={"sku": sku})

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        owner_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        """
        List products with filtering, search, pricing range, and pagination.
        """
        where: dict[str, Any] = {}

        if search:
            where["OR"] = [
                {"title": {"contains": search, "mode": "insensitive"}},
                {"description": {"contains": search, "mode": "insensitive"}},
            ]

        if is_active is not None:
            where["is_active"] = is_active

        if owner_id:
            where["owner_id"] = owner_id

        if min_price is not None or max_price is not None:
            price_filter: dict[str, float] = {}
            if min_price is not None:
                price_filter["gte"] = min_price
            if max_price is not None:
                price_filter["lte"] = max_price
            where["price"] = price_filter

        order = {sort_by: sort_order}

        products = await self.db.product.find_many(
            where=where,
            skip=offset,
            take=limit,
            order=order,
        )
        total = await self.db.product.count(where=where)
        return products, total

    async def create(self, data: dict[str, Any]) -> Product:
        """Persist a new product record."""
        return await self.db.product.create(data=data)

    async def update(self, product_id: str, data: dict[str, Any]) -> Product:
        """Update an existing product record."""
        return await self.db.product.update(where={"id": product_id}, data=data)

    async def delete(self, product_id: str) -> None:
        """Delete a product by ID."""
        await self.db.product.delete(where={"id": product_id})
