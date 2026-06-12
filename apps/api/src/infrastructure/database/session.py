"""Async SQLAlchemy session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ...core.config import settings

logger = structlog.get_logger(__name__)

engine = create_async_engine(
    settings.db_url_str,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=settings.db_pool_pre_ping,
    echo=settings.db_echo,
    future=True,
)

# Optional read‑replica engine
if settings.use_replica and settings.replica_database_url:
    replica_engine = create_async_engine(
        str(settings.replica_database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=settings.db_pool_pre_ping,
        echo=settings.db_echo,
        future=True,
    )
    ReplicaSessionLocal = async_sessionmaker(
        bind=replica_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
else:
    replica_engine = None
    ReplicaSessionLocal = None

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


from prometheus_client import Counter

# Counter for read‑replica usage
db_read_replica_queries_total = Counter(
    "db_read_replica_queries_total",
    "Number of queries routed to the read‑replica database",
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session bound to the primary engine (write session)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Read‑replica session
async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session bound to the replica engine if configured, otherwise fall back to primary.
    Increments the `db_read_replica_queries_total` metric when the replica is used.
    """
    if ReplicaSessionLocal:
        db_read_replica_queries_total.inc()
        async with ReplicaSessionLocal() as session:
            try:
                yield session
                # No commit for read‑only session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        # Fallback to primary engine
        async with AsyncSessionLocal() as session:
            try:
                yield session
                # No commit for read‑only session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
