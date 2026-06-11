"""Cost tracking API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AnalystUser
from ...infrastructure.database.models import CostRecordORM
from ...infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/costs", tags=["Costs"])


@router.get("/summary")
async def get_cost_summary(
    _: AnalystUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=30)

    total_result = await db.execute(
        select(func.sum(CostRecordORM.cost_usd)).where(CostRecordORM.date >= since)
    )
    total = float(total_result.scalar_one() or 0.0)

    model_result = await db.execute(
        select(CostRecordORM.model, func.sum(CostRecordORM.cost_usd).label("cost"))
        .where(CostRecordORM.date >= since)
        .group_by(CostRecordORM.model)
        .order_by(func.sum(CostRecordORM.cost_usd).desc())
        .limit(5)
    )
    top_models = [{"model": r.model, "cost_usd": float(r.cost)} for r in model_result.all()]

    agent_result = await db.execute(
        select(CostRecordORM.agent, func.sum(CostRecordORM.cost_usd).label("cost"))
        .where(CostRecordORM.date >= since)
        .group_by(CostRecordORM.agent)
        .order_by(func.sum(CostRecordORM.cost_usd).desc())
        .limit(5)
    )
    top_agents = [{"agent": r.agent, "cost_usd": float(r.cost)} for r in agent_result.all()]

    trend_result = await db.execute(
        select(
            func.date_trunc("day", CostRecordORM.date).label("day"),
            func.sum(CostRecordORM.cost_usd).label("cost"),
        )
        .where(CostRecordORM.date >= since)
        .group_by(func.date_trunc("day", CostRecordORM.date))
        .order_by(func.date_trunc("day", CostRecordORM.date))
    )
    trend = [
        {"date": r.day.isoformat(), "cost_usd": float(r.cost)}
        for r in trend_result.all()
    ]

    return {
        "total_cost_usd": total,
        "daily_avg_usd": total / 30,
        "top_models": top_models,
        "top_agents": top_agents,
        "trend": trend,
    }
