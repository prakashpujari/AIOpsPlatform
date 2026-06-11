"""Audit log service — writes are fire-and-forget via Kafka."""

from __future__ import annotations

import math
import uuid
from datetime import datetime

import structlog
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.audit.models import (
    AuditLog,
    AuditQuery,
    CreateAuditLogCommand,
    PaginatedAuditLogs,
)
from ..infrastructure.database.models import AuditLogORM
from ..infrastructure.kafka.producer import publish_audit_event

logger = structlog.get_logger(__name__)


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def log(self, command: CreateAuditLogCommand) -> None:
        entry = AuditLogORM(**command.model_dump())
        self._db.add(entry)
        # Best-effort Kafka publish — don't fail the request on Kafka errors
        try:
            await publish_audit_event(command.model_dump())
        except Exception as exc:
            logger.warning("audit.kafka_publish_failed", error=str(exc))

    async def query(self, q: AuditQuery) -> PaginatedAuditLogs:
        stmt = select(AuditLogORM)
        conditions = []

        if q.user_id:
            conditions.append(AuditLogORM.user_id == q.user_id)
        if q.resource:
            conditions.append(AuditLogORM.resource == q.resource)
        if q.action:
            conditions.append(AuditLogORM.action.ilike(f"%{q.action}%"))
        if q.status:
            conditions.append(AuditLogORM.status == q.status)
        if q.search:
            term = f"%{q.search}%"
            conditions.append(
                or_(
                    AuditLogORM.user_name.ilike(term),
                    AuditLogORM.action.ilike(term),
                    AuditLogORM.resource.ilike(term),
                )
            )
        if q.from_date:
            conditions.append(AuditLogORM.timestamp >= q.from_date)
        if q.to_date:
            conditions.append(AuditLogORM.timestamp <= q.to_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        offset = (q.page - 1) * q.size
        stmt = stmt.order_by(AuditLogORM.timestamp.desc()).offset(offset).limit(q.size)
        rows = (await self._db.execute(stmt)).scalars().all()

        return PaginatedAuditLogs(
            items=[AuditLog.model_validate(r) for r in rows],
            total=total,
            page=q.page,
            size=q.size,
            pages=math.ceil(total / q.size) if total > 0 else 1,
        )
