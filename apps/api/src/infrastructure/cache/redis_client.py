"""Redis cache client with typed helpers."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
import structlog
from redis.asyncio import Redis

from ...core.config import settings

logger = structlog.get_logger(__name__)

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis


async def cache_get(key: str) -> Any | None:
    client = await get_redis()
    try:
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception as exc:
        logger.warning("cache.get_failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.redis_ttl_seconds) -> None:
    client = await get_redis()
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("cache.set_failed", key=key, error=str(exc))


async def cache_delete(key: str) -> None:
    client = await get_redis()
    try:
        await client.delete(key)
    except Exception as exc:
        logger.warning("cache.delete_failed", key=key, error=str(exc))


async def cache_invalidate_pattern(pattern: str) -> None:
    client = await get_redis()
    try:
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:
        logger.warning("cache.invalidate_failed", pattern=pattern, error=str(exc))
