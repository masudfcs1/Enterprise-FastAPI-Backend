"""
Tests for products module endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient, mock_prisma: MagicMock):
    mock_prisma.product.find_many.return_value = []
    mock_prisma.product.count.return_value = 0

    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_create_product_authenticated(
    client: AsyncClient, mock_prisma: MagicMock, auth_headers: dict[str, str]
):
    now = datetime.now(timezone.utc)
    current_user = MagicMock(
        id="user-uuid-1",
        email="user@example.com",
        username="normaluser",
        role="USER",
        is_active=True,
    )
    mock_prisma.user.find_unique.return_value = current_user
    mock_prisma.product.find_unique.return_value = None

    created_product = MagicMock(
        id="product-uuid-1",
        title="Gaming Keyboard",
        description="Mechanical keyboard with RGB",
        price=99.99,
        sku="KEY-RGB-001",
        quantity=50,
        is_active=True,
        owner_id="user-uuid-1",
        created_at=now,
        updated_at=now,
    )
    mock_prisma.product.create.return_value = created_product

    payload = {
        "title": "Gaming Keyboard",
        "description": "Mechanical keyboard with RGB",
        "price": 99.99,
        "sku": "KEY-RGB-001",
        "quantity": 50,
    }
    response = await client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Gaming Keyboard"
    assert body["data"]["sku"] == "KEY-RGB-001"
