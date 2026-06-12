"""Enterprise AI Platform — AI Gateway Entry Point."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .api.chat import router as chat_router
from .api.gateway_health import router as health_router
from .core.config import settings
from .core.tracing import setup_tracing
from .core.exceptions import GatewayError
from .health.health_monitor import health_monitor

logger = logging.getLogger(__name__)

# ── Prometheus metrics ────────────────────────────────────────────────────────
from prometheus_client import Gauge
REQUEST_COUNT = Counter(
    "gateway_requests_total", "Total gateway requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "gateway_request_duration_seconds", "Gateway request latency", ["endpoint"]
)

# RAG request metric – counts RAG endpoint usage
RAG_REQUESTS = Counter(
    "gateway_rag_requests_total", "Total RAG endpoint requests", ["type"]
)
ROUTING_DECISIONS = Counter(
    "gateway_routing_decisions_total", "Routing decisions by strategy and model",
    ["strategy", "model"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    # ── Startup ───────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info("AI Gateway starting (env=%s)", settings.env)
    # Initialise tracing first, then start health monitoring
    setup_tracing(settings.otel_service_name, settings.otel_exporter_otlp_endpoint, settings.otel_enabled)
    await health_monitor.start()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    await health_monitor.stop()
    logger.info("AI Gateway shutdown complete")


app = FastAPI(
    title="AI Gateway",
    description="Internal AI Gateway — Model Routing, Policy, Cost, Circuit Breaker",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
# (Middleware stays unchanged)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observe_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    import time
    t0 = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - t0
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(elapsed)
    response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
    return response


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(GatewayError)
async def gateway_error_handler(request: Request, exc: GatewayError) -> JSONResponse:
    logger.warning("GatewayError: %s", exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(chat_router, prefix="/v1")
app.include_router(health_router, prefix="/v1")


# ── Prometheus scrape endpoint ─────────────────────────────────────────────────

@app.get("/metrics", include_in_schema=False)
async def metrics():  # type: ignore[no-untyped-def]
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": "ai-gateway",
        "env": settings.env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
