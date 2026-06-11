"""Enterprise AI Platform — FastAPI application entry point."""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .api.v1.router import v1_router
from .core.config import settings
from .core.logging import configure_logging
from .core.tracing import setup_tracing
from .infrastructure.kafka.producer import close_producer
from .middleware.error_handler import register_exception_handlers
from .middleware.logging_middleware import RequestLoggingMiddleware
from .middleware.rate_limit_middleware import RateLimitMiddleware

configure_logging(
    log_level=settings.log_level,
    json_logs=settings.is_production,
)
logger = structlog.get_logger(__name__)

setup_tracing(
    service_name=settings.otel_service_name,
    endpoint=settings.otel_exporter_otlp_endpoint,
    enabled=settings.otel_enabled,
)

app = FastAPI(
    title="Enterprise AI Platform API",
    description="Banking AI Support Copilot & AIOps Platform — Production API",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ── CORS ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit",
                    "X-RateLimit-Remaining"],
)

# ── Custom middleware (order matters — outermost = last added) ──
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ── Exception handlers ─────────────────────
register_exception_handlers(app)

# ── Routers ────────────────────────────────
app.include_router(v1_router)

# ── Prometheus metrics endpoint ────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "aiops-api", "version": "1.0.0"}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("api.startup", env=settings.env)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_producer()
    logger.info("api.shutdown")
