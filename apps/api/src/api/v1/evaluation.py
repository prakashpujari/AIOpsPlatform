"""Evaluation runs API."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AnalystUser
from ...infrastructure.database.models import EvalRunORM
from ...infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/runs")
async def list_eval_runs(
    _: AnalystUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(EvalRunORM).order_by(EvalRunORM.timestamp.desc()).limit(50)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "run_name": r.run_name,
            "agent_type": r.agent_type,
            "timestamp": r.timestamp.isoformat(),
            "metrics": r.metrics,
            "total_samples": r.total_samples,
            "pass_rate": r.pass_rate,
            "ci_gate_status": r.ci_gate_status,
        }
        for r in rows
    ]
