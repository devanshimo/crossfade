"""
app/db/session.py
──────────────────
Async SQLAlchemy engine and session factory.

Why it exists:
    FastAPI is async-native.  Using async SQLAlchemy sessions means DB queries
    don't block the event loop, enabling higher concurrency with no extra threads.

How it connects:
    • dependencies/db.py  – yields a per-request AsyncSession from `AsyncSessionLocal`.
    • alembic/env.py      – uses the *sync* URL variant for migration runs (Alembic
                            doesn't support async natively; we swap the driver there).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,  # log SQL in dev, silent in prod
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detect stale connections
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # objects stay usable after commit (important for async)
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    Usage:
        @router.get("/")
        async def handler(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
