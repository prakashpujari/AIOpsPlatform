"""Agent traces API."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AnalystUser, OperatorUser
from ...infrastructure.database.models import AgentTraceORM
from ...infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


def _trace_to_dict(t: AgentTraceORM) -> dict:
    return {
        "id": str(t.id),
        "agent_type": t.agent_type,
        "session_id": t.session_id,
        "status": t.status,
        "started_at": t.started_at.isoformat(),
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "steps": t.steps,
        "total_tokens": t.total_tokens,
        "total_cost_usd": t.total_cost_usd,
        "model_used": t.model_used,
        "input_summary": t.input_summary,
        "output_summary": t.output_summary,
        "error_message": t.error_message,
        "requires_approval": t.requires_approval,
        "approved_by": t.approved_by,
    }


@router.get("/traces")
async def list_traces(
    _: AnalystUser,
    agent_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(AgentTraceORM).order_by(AgentTraceORM.started_at.desc())
    if agent_type:
        stmt = stmt.where(AgentTraceORM.agent_type == agent_type)
    if status:
        stmt = stmt.where(AgentTraceORM.status == status)
    stmt = stmt.offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_trace_to_dict(r) for r in rows]}


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: uuid.UUID,
    _: AnalystUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    t = await db.get(AgentTraceORM, trace_id)
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")
    return _trace_to_dict(t)


@router.post("/traces/{trace_id}/approve")
async def approve_trace(
    trace_id: uuid.UUID,
    body: dict,
    user: OperatorUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    t = await db.get(AgentTraceORM, trace_id)
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")
    if body.get("approved"):
        t.approved_by = user.sub
        t.status = "running"
    else:
        t.status = "failed"
        t.error_message = f"Rejected by {user.sub}: {body.get('reason', '')}"
    await db.flush()
    return {"status": t.status, "approved_by": t.approved_by}
