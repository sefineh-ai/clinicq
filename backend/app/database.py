from typing import AsyncGenerator, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    Mapped,
    mapped_column,
)
from app.config import settings

# Async Engine for FastAPI
is_sqlite = "sqlite" in settings.async_database_uri
async_engine_kwargs: dict[str, Any] = {"echo": settings.DEBUG}
if not is_sqlite:
    async_engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

async_engine = create_async_engine(
    settings.async_database_uri,
    **async_engine_kwargs,
)
engine = async_engine

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
async_session_factory = AsyncSessionLocal

# Sync Engine for Alembic and Seed scripts
sync_is_sqlite = "sqlite" in settings.sync_database_uri
sync_engine_kwargs: dict[str, Any] = {"echo": settings.DEBUG}
if not sync_is_sqlite:
    sync_engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 5,
        "pool_pre_ping": True,
    })

sync_engine = create_engine(
    settings.sync_database_uri,
    **sync_engine_kwargs,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative model for all database tables."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
