"""
Tests for authentication module endpoints and token lifecycle.
"""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

from app.core.security import hash_password, verify_password


def test_password_hashing():
    raw = "SuperSecretPassword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, mock_prisma: MagicMock):
    created_user = MagicMock(
        id="user-uuid-1",
        email="test@example.com",
        username="testuser",
        role="USER",
        is_active=True,
    )
    mock_prisma.user.find_unique.return_value = None
    mock_prisma.user.create.return_value = created_user

    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "StrongPassword123!",
        "first_name": "Test",
        "last_name": "User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, mock_prisma: MagicMock):
    hashed = hash_password("ValidPassword123!")
    user = MagicMock(
        id="user-uuid-1",
        email="test@example.com",
        username="testuser",
        password_hash=hashed,
        role="USER",
        is_active=True,
    )
    mock_prisma.user.find_unique.return_value = user

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "ValidPassword123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, mock_prisma: MagicMock):
    hashed = hash_password("CorrectPassword123!")
    user = MagicMock(
        id="user-uuid-1",
        email="test@example.com",
        username="testuser",
        password_hash=hashed,
        role="USER",
        is_active=True,
    )
    mock_prisma.user.find_unique.return_value = user

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTHENTICATION_ERROR"
