"""Audit log API."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import ComplianceUser
from ...domain.audit.models import AuditQuery
from ...infrastructure.database.session import get_db
from ...services.audit_service import AuditService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
async def list_audit_logs(
    _: ComplianceUser,
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    resource: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AuditService(db)
    result = await svc.query(
        AuditQuery(
            search=search,
            status=status,  # type: ignore[arg-type]
            resource=resource,
            page=page,
            size=size,
        )
    )
    return result.model_dump(mode="json")
