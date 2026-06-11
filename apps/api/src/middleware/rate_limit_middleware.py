"""Sliding-window rate limiter backed by Redis."""

from __future__ import annotations

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ..core.config import settings
from ..infrastructure.cache.redis_client import get_redis

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/health", "/metrics"}

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path.split('/')[2] if len(request.url.path.split('/')) > 2 else 'root'}"

        try:
            redis = await get_redis()
            now = time.time()
            window_start = now - settings.rate_limit_window_seconds

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, settings.rate_limit_window_seconds)
            results = await pipe.execute()
            request_count = results[2]

            limit = settings.rate_limit_requests
            if "/chat" in request.url.path:
                limit = settings.rate_limit_chat_rpm

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count))
            response.headers["X-RateLimit-Reset"] = str(int(now + settings.rate_limit_window_seconds))

            if request_count > limit:
                logger.warning("rate_limit.exceeded", client_ip=client_ip, count=request_count)
                return JSONResponse(
                    status_code=429,
                    content={"error": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"},
                )
            return response
        except Exception as exc:
            logger.warning("rate_limit.redis_error", error=str(exc))
            return await call_next(request)
