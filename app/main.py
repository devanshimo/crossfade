"""
app/main.py
────────────
FastAPI application factory and startup/shutdown lifecycle hooks.

Why it exists:
    The entry point for the ASGI server (uvicorn).  It creates the FastAPI
    instance, registers middleware, mounts routers, and wires up lifespan events
    (DB connection pool warm-up, logging init).

How it connects:
    • Imports api_router from api/v1/router.py.
    • Calls configure_logging() once at startup.
    • Exposes `app` which uvicorn/gunicorn bind to.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import engine

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Async context manager for startup / shutdown logic.

    On startup:  log that the server is ready (DB pool warms lazily on first
                 query, which is intentional – no blocking init).
    On shutdown: dispose of the connection pool cleanly.
    """
    logger.info(
        "crossfade_starting",
        env=settings.app_env,
        log_level=settings.log_level,
    )
    yield
    await engine.dispose()
    logger.info("crossfade_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Crossfade API",
        description="Cross-platform playlist sync service – Spotify ↔ Apple Music",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Tighten allow_origins in production to your actual frontend origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/health", tags=["ops"], include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
