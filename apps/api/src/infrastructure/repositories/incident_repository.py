"""SQLAlchemy implementation of IncidentRepository."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import and_, cast, func, or_, select, update
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.exceptions import NotFoundError
from ...domain.incidents.models import (
    CreateIncidentCommand,
    Incident,
    IncidentStats,
    ListIncidentsQuery,
    PaginatedIncidents,
    UpdateIncidentCommand,
)
from ...domain.incidents.repository import IncidentRepository
from ..database.models import IncidentORM

logger = structlog.get_logger(__name__)


def _orm_to_domain(orm: IncidentORM) -> Incident:
    return Incident.model_validate(orm)


class SQLIncidentRepository(IncidentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, command: CreateIncidentCommand, created_by: str) -> Incident:
        incident = IncidentORM(
            title=command.title,
            description=command.description,
            severity=command.severity,
            service=command.service,
            environment=command.environment,
            assignee=command.assignee,
            tags=command.tags,
            status="open",
            timeline=[{
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": created_by,
                "action": "Incident created",
            }],
        )
        self._session.add(incident)
        await self._session.flush()
        logger.info("incident.created", incident_id=str(incident.id))
        return _orm_to_domain(incident)

    async def get_by_id(self, incident_id: uuid.UUID) -> Incident | None:
        result = await self._session.get(IncidentORM, incident_id)
        return _orm_to_domain(result) if result else None

    async def list(self, query: ListIncidentsQuery) -> PaginatedIncidents:
        stmt = select(IncidentORM)
        conditions = []

        if query.severity:
            conditions.append(IncidentORM.severity == query.severity)
        if query.status:
            conditions.append(IncidentORM.status == query.status)
        if query.service:
            conditions.append(IncidentORM.service.ilike(f"%{query.service}%"))
        if query.search:
            search_term = f"%{query.search}%"
            conditions.append(
                or_(
                    IncidentORM.title.ilike(search_term),
                    IncidentORM.description.ilike(search_term),
                    IncidentORM.service.ilike(search_term),
                )
            )
        if query.from_date:
            conditions.append(IncidentORM.created_at >= query.from_date)
        if query.to_date:
            conditions.append(IncidentORM.created_at <= query.to_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        offset = (query.page - 1) * query.size
        stmt = stmt.order_by(IncidentORM.created_at.desc()).offset(offset).limit(query.size)

        rows = (await self._session.execute(stmt)).scalars().all()
        return PaginatedIncidents(
            items=[_orm_to_domain(r) for r in rows],
            total=total,
            page=query.page,
            size=query.size,
            pages=math.ceil(total / query.size) if total > 0 else 1,
        )

    async def update(self, incident_id: uuid.UUID, command: UpdateIncidentCommand) -> Incident:
        incident = await self._session.get(IncidentORM, incident_id)
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found")

        updates = command.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(incident, key, value)

        await self._session.flush()
        return _orm_to_domain(incident)

    async def delete(self, incident_id: uuid.UUID) -> None:
        incident = await self._session.get(IncidentORM, incident_id)
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found")
        await self._session.delete(incident)

    async def get_stats(self) -> IncidentStats:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        open_count = (
            await self._session.execute(
                select(func.count()).where(
                    and_(IncidentORM.status == "open")
                )
            )
        ).scalar_one()

        critical_count = (
            await self._session.execute(
                select(func.count()).where(
                    and_(IncidentORM.severity == "critical", IncidentORM.status != "closed")
                )
            )
        ).scalar_one()

        resolved_today = (
            await self._session.execute(
                select(func.count()).where(
                    and_(
                        IncidentORM.status == "resolved",
                        IncidentORM.resolved_at >= today_start,
                    )
                )
            )
        ).scalar_one()

        avg_result = (
            await self._session.execute(
                select(
                    func.avg(
                        func.extract(
                            "epoch",
                            IncidentORM.resolved_at - IncidentORM.created_at,
                        )
                        / 3600
                    )
                ).where(
                    and_(IncidentORM.status == "resolved", IncidentORM.resolved_at.is_not(None))
                )
            )
        ).scalar_one()

        return IncidentStats(
            open=open_count,
            critical=critical_count,
            resolved_today=resolved_today,
            avg_resolution_hours=float(avg_result or 0.0),
        )
