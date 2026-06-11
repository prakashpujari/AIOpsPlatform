"""Service health and platform health check APIs."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import CurrentUser
from ...infrastructure.cache.redis_client import get_redis
from ...infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["Health"])

# Synthetic service health data — replaced by real Prometheus scrape in Phase 14
MOCK_SERVICES = [
    {"id": "payment-service", "name": "payment-service", "namespace": "production",
     "status": "healthy", "replicas": {"ready": 3, "desired": 3},
     "cpu": 45.2, "memory": 62.1, "error_rate": 0.02, "p95_latency_ms": 145, "alerts": 0},
    {"id": "mortgage-api", "name": "mortgage-api", "namespace": "production",
     "status": "healthy", "replicas": {"ready": 2, "desired": 2},
     "cpu": 31.5, "memory": 48.7, "error_rate": 0.0, "p95_latency_ms": 89, "alerts": 0},
    {"id": "account-service", "name": "account-service", "namespace": "production",
     "status": "degraded", "replicas": {"ready": 1, "desired": 3},
     "cpu": 88.4, "memory": 91.2, "error_rate": 3.4, "p95_latency_ms": 2140, "alerts": 2},
    {"id": "notification-svc", "name": "notification-svc", "namespace": "production",
     "status": "healthy", "replicas": {"ready": 2, "desired": 2},
     "cpu": 12.3, "memory": 22.1, "error_rate": 0.0, "p95_latency_ms": 55, "alerts": 0},
    {"id": "fraud-detection", "name": "fraud-detection", "namespace": "production",
     "status": "unhealthy", "replicas": {"ready": 0, "desired": 2},
     "cpu": 0.0, "memory": 0.0, "error_rate": 100.0, "p95_latency_ms": 0, "alerts": 5},
    {"id": "kyc-service", "name": "kyc-service", "namespace": "production",
     "status": "healthy", "replicas": {"ready": 1, "desired": 1},
     "cpu": 28.9, "memory": 41.3, "error_rate": 0.1, "p95_latency_ms": 210, "alerts": 0},
]


@router.get("/health/services")
async def get_service_health(_: CurrentUser) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [{**s, "last_checked": now} for s in MOCK_SERVICES]


@router.get("/health")
async def platform_health(db: AsyncSession = Depends(get_db)) -> dict:
    checks: dict[str, str] = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
