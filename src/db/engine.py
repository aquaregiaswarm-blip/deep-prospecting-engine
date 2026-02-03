"""Database connection management for async (FastAPI) and sync (LangGraph pipeline) access."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base


def _get_base_url():
    """Build the base database URL from environment variables."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    
    # Build from individual env vars (Cloud SQL friendly)
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASS", "dpe-aquaregia-2026")
    db_name = os.environ.get("DB_NAME", "dpe")
    
    # Cloud SQL Unix socket (used by Cloud Run)
    instance_connection = os.environ.get("INSTANCE_CONNECTION_NAME")
    if instance_connection:
        return f"postgresql://{user}:{password}@/{db_name}?host=/cloudsql/{instance_connection}"
    
    # Direct TCP (local dev or public IP)
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def _get_async_url():
    url = _get_base_url()
    if "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def _get_sync_url():
    url = _get_base_url()
    if "psycopg2" not in url and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://")
    elif "asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")
    return url


engine = create_async_engine(_get_async_url(), echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(_get_sync_url(), echo=False, pool_size=5)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
