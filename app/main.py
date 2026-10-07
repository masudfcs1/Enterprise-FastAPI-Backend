"""
Application entrypoint — factory pattern.
No business logic here. Only infrastructure wiring: lifespan, middleware, routers, exception handlers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect_db, disconnect_db, prisma
from app.core.logging import setup_logging
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.shared.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application startup and shutdown lifecycle hooks."""
    try:
        await connect_db()
    except Exception as exc:
        import logging

        logging.getLogger("app.main").warning(
            "Could not connect to database on startup: %s. Continuing...", exc
        )
    yield
    await disconnect_db()


def create_app() -> FastAPI:
    """Application factory — constructs a fully configured FastAPI instance."""

    # ── Logging ───────────────────────────────────────────
    setup_logging(
        level="DEBUG" if settings.DEBUG else "INFO",
        json_output=settings.ENVIRONMENT == "production",
    )

    # ── FastAPI Instance ──────────────────────────────────
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Middleware (outermost first) ───────────────────────
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ────────────────────────────────
    register_exception_handlers(app)

    # ── Feature Routers ───────────────────────────────────
    from app.modules.auth.router import router as auth_router
    from app.modules.products.router import router as products_router
    from app.modules.users.router import router as users_router

    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(users_router, prefix=settings.API_V1_STR)
    app.include_router(products_router, prefix=settings.API_V1_STR)

    # ── Health Check ──────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check() -> JSONResponse:
        db_status = "connected" if prisma.is_connected() else "disconnected"
        return JSONResponse(
            content={
                "status": "ok",
                "database": db_status,
                "environment": settings.ENVIRONMENT,
                "version": settings.VERSION,
            }
        )

    return app


app: FastAPI = create_app()
