"""
Tests for user management endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user_profile(
    client: AsyncClient, mock_prisma: MagicMock, auth_headers: dict[str, str]
):
    now = datetime.now(timezone.utc)
    current_user = MagicMock(
        id="user-uuid-1",
        email="user@example.com",
        username="normaluser",
        first_name="Normal",
        last_name="User",
        role="USER",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_prisma.user.find_unique.return_value = current_user

    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "user@example.com"
    assert body["data"]["id"] == "user-uuid-1"


@pytest.mark.asyncio
async def test_list_users_forbidden_for_regular_user(
    client: AsyncClient, mock_prisma: MagicMock, auth_headers: dict[str, str]
):
    current_user = MagicMock(
        id="user-uuid-1",
        email="user@example.com",
        username="normaluser",
        role="USER",
        is_active=True,
    )
    mock_prisma.user.find_unique.return_value = current_user

    response = await client.get("/api/v1/users", headers=auth_headers)
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTHORIZATION_ERROR"
