"""
Pytest configuration, fixtures, and mock Prisma client setup.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app


class DummyModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self, *args, **kwargs):
        return self.__dict__


@pytest.fixture
def mock_prisma() -> MagicMock:
    """Mock Prisma database client for fast unit and integration tests."""
    mock = MagicMock()
    mock.is_connected = MagicMock(return_value=True)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()

    # User delegate
    mock.user = MagicMock()
    mock.user.find_unique = AsyncMock(return_value=None)
    mock.user.find_first = AsyncMock(return_value=None)
    mock.user.find_many = AsyncMock(return_value=[])
    mock.user.count = AsyncMock(return_value=0)
    mock.user.create = AsyncMock(return_value=None)
    mock.user.update = AsyncMock(return_value=None)
    mock.user.delete = AsyncMock(return_value=None)

    # RefreshToken delegate
    mock.refreshtoken = MagicMock()
    mock.refreshtoken.find_unique = AsyncMock(return_value=None)
    mock.refreshtoken.create = AsyncMock(return_value=None)
    mock.refreshtoken.update = AsyncMock(return_value=None)
    mock.refreshtoken.update_many = AsyncMock(return_value=None)

    # Product delegate
    mock.product = MagicMock()
    mock.product.find_unique = AsyncMock(return_value=None)
    mock.product.find_many = AsyncMock(return_value=[])
    mock.product.count = AsyncMock(return_value=0)
    mock.product.create = AsyncMock(return_value=None)
    mock.product.update = AsyncMock(return_value=None)
    mock.product.delete = AsyncMock(return_value=None)

    return mock


@pytest_asyncio.fixture
async def client(mock_prisma: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with mocked database dependency."""
    async def override_get_db():
        yield mock_prisma

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def normal_user_token() -> str:
    return create_access_token(
        subject="user-uuid-1",
        extra_claims={"role": "USER"},
    )


@pytest.fixture
def admin_user_token() -> str:
    return create_access_token(
        subject="admin-uuid-1",
        extra_claims={"role": "ADMIN"},
    )


@pytest.fixture
def auth_headers(normal_user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture
def admin_headers(admin_user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_user_token}"}
