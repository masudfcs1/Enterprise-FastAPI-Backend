"""
Database connection management and Prisma Client lifecycle.
Provides connection hooks for FastAPI lifespan and dependency injection for routes/services.
"""

from collections.abc import AsyncGenerator

from prisma import Prisma

# Global singleton Prisma client
prisma: Prisma = Prisma(auto_register=True)


async def connect_db() -> None:
    """Establish database connection on application startup."""
    if not prisma.is_connected():
        await prisma.connect()


async def disconnect_db() -> None:
    """Gracefully terminate database connection on application shutdown."""
    if prisma.is_connected():
        await prisma.disconnect()


async def get_db() -> AsyncGenerator[Prisma, None]:
    """
    FastAPI dependency providing the connected Prisma client.
    Ensures connection is established if called independently.
    """
    if not prisma.is_connected():
        await prisma.connect()
    yield prisma
