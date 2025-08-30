from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


# ---- Create ONE engine per process ----
_settings = get_settings()
engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,        # tune to your workload
    max_overflow=10,    # extra above pool_size
    pool_timeout=30,
    pool_recycle=1800,  # recycle stale conns (secs)
)

# ---- Create ONE sessionmaker tied to that engine ----
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


# Dependency/helper to get a session (FastAPI-friendly)
async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


# Optional: call at shutdown/lifespan to cleanly close pool
async def dispose_engine() -> None:
    await engine.dispose()


# Simple connectivity check (does NOT create a new engine)
async def test_connection() -> str:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        result = await conn.execute(text("SHOW server_version"))
        row = result.first()
        return row[0] if row else "unknown"


# Backwards-compat shim for old imports
def get_engine():
    return engine

# Backwards-compat shim for old imports
def get_sessionmaker():
    return async_session_maker
