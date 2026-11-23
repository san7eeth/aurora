"""
SQLAlchemy async engine and session factory.
SQLite (aiosqlite) is stored at backend/data/aurora.db unless DATABASE_URL overrides it.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect

from ..core.config import resolve_sqlite_url, settings

DATABASE_URL, DB_PATH = resolve_sqlite_url(settings.database_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create new tables and add Phase 5 columns to existing SQLite databases."""
    from . import models  # noqa: F401 — register models on Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_existing_schema)


def _migrate_existing_schema(connection):
    """Apply small additive migrations for databases created before Phase 5."""
    inspector = inspect(connection)
    memory_columns = {column["name"] for column in inspector.get_columns("memories")}
    document_columns = {column["name"] for column in inspector.get_columns("documents")}
    if "embedding" not in memory_columns:
        connection.exec_driver_sql("ALTER TABLE memories ADD COLUMN embedding JSON")
    if "storage_key" not in document_columns:
        connection.exec_driver_sql("ALTER TABLE documents ADD COLUMN storage_key VARCHAR(512)")


async def get_session() -> AsyncSession:
    """Yield a database session for FastAPI dependencies."""
    async with async_session() as session:
        yield session
