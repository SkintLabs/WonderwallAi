"""Async SQLAlchemy engine — SQLite for dev, PostgreSQL for production."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from server.config import get_settings
from server.db.models import Base
logger = logging.getLogger("wonderwallai.server.db")
_engine = None
_session_factory = None
def _get_database_url() -> str:
    url = get_settings().database_url
    # Auto-fix Railway PostgreSQL URLs
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url
async def init_db() -> None:
    """Create engine, session factory, and all tables."""
    global _engine, _session_factory
    url = _get_database_url()
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    _engine = create_async_engine(url, connect_args=connect_args, echo=False)
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Lightweight column migrations (create_all won't ALTER existing tables)
    await _migrate_add_missing_columns()
    logger.info(f"Database initialized ({url.split('://')[0]})")
async def _migrate_add_missing_columns() -> None:
    """
    Add columns intr
