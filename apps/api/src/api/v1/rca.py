"""RCA API."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AnalystUser, OperatorUser
from ...infrastructure.database.session import get_db
from ...infrastructure.database.models import RCAORM
from sqlalchemy import select

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/rca", tags=["RCA"])


@router.get("")
async def list_rca(
    _: AnalystUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(RCAORM).order_by(RCAORM.generated_at.desc()).limit(50)
    )
    rows = result.scalars().all()
    items = []
    for r in rows:
        items.append({
            "id": str(r.id),
            "incident_id": str(r.incident_id),
            "root_cause": r.root_cause,
            "contributing_factors": r.contributing_factors,
            "timeline": r.timeline,
            "affected_services": r.affected_services,
            "suggested_fix": r.suggested_fix,
            "confidence": r.confidence,
            "generated_at": r.generated_at.isoformat(),
            "approved_by": r.approved_by,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
        })
    return {"items": items}


@router.get("/{rca_id}")
async def get_rca(
    rca_id: uuid.UUID,
    _: AnalystUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    r = await db.get(RCAORM, rca_id)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="RCA not found")
    return {
        "id": str(r.id),
        "incident_id": str(r.incident_id),
        "root_cause": r.root_cause,
        "contributing_factors": r.contributing_factors,
        "timeline": r.timeline,
        "affected_services": r.affected_services,
        "suggested_fix": r.suggested_fix,
        "confidence": r.confidence,
        "generated_at": r.generated_at.isoformat(),
        "approved_by": r.approved_by,
        "approved_at": r.approved_at.isoformat() if r.approved_at else None,
    }


@router.post("/{rca_id}/approve")
async def approve_rca(
    rca_id: uuid.UUID,
    user: OperatorUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import datetime, timezone
    r = await db.get(RCAORM, rca_id)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="RCA not found")
    r.approved_by = user.sub
    r.approved_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "approved", "approved_by": user.sub}
