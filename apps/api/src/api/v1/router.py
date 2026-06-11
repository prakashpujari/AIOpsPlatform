"""API v1 root router — mounts all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from .admin import router as admin_router
from .agents import router as agents_router
from .audit import router as audit_router
from .chat import router as chat_router
from .costs import router as costs_router
from .evaluation import router as evaluation_router
from .health import router as health_router
from .incidents import router as incidents_router
from .rca import router as rca_router
from .search import router as search_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(incidents_router)
v1_router.include_router(rca_router)
v1_router.include_router(agents_router)
v1_router.include_router(chat_router)
v1_router.include_router(search_router)
v1_router.include_router(health_router)
v1_router.include_router(costs_router)
v1_router.include_router(evaluation_router)
v1_router.include_router(admin_router)
v1_router.include_router(audit_router)
