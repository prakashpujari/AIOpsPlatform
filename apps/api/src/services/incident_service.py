"""Incident application service — orchestrates domain + infra."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError
from ..domain.incidents.models import (
    CreateIncidentCommand,
    Incident,
    IncidentStats,
    ListIncidentsQuery,
    PaginatedIncidents,
    ResolveIncidentCommand,
    UpdateIncidentCommand,
)
from ..infrastructure.cache.redis_client import (
    cache_delete,
    cache_get,
    cache_invalidate_pattern,
    cache_set,
)
from ..infrastructure.kafka.producer import publish_incident_event
from ..infrastructure.repositories.incident_repository import SQLIncidentRepository

logger = structlog.get_logger(__name__)

CACHE_TTL = 60
STATS_TTL = 30


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SQLIncidentRepository(session)

    async def create_incident(
        self, command: CreateIncidentCommand, created_by: str
    ) -> Incident:
        incident = await self._repo.create(command, created_by)
        await cache_invalidate_pattern("incidents:*")
        await publish_incident_event(
            "incident.created",
            str(incident.id),
            incident.model_dump(mode="json"),
        )
        logger.info("incident_service.created", incident_id=str(incident.id))
        return incident

    async def get_incident(self, incident_id: uuid.UUID) -> Incident:
        cache_key = f"incidents:{incident_id}"
        cached = await cache_get(cache_key)
        if cached:
            return Incident.model_validate(cached)

        incident = await self._repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found")

        await cache_set(cache_key, incident.model_dump(mode="json"), CACHE_TTL)
        return incident

    async def list_incidents(self, query: ListIncidentsQuery) -> PaginatedIncidents:
        cache_key = f"incidents:list:{query.model_dump_json()}"
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedIncidents.model_validate(cached)

        result = await self._repo.list(query)
        await cache_set(cache_key, result.model_dump(mode="json"), CACHE_TTL)
        return result

    async def update_incident(
        self,
        incident_id: uuid.UUID,
        command: UpdateIncidentCommand,
        updated_by: str,
    ) -> Incident:
        incident = await self._repo.update(incident_id, command)
        await cache_delete(f"incidents:{incident_id}")
        await cache_invalidate_pattern("incidents:list:*")
        await publish_incident_event(
            "incident.updated",
            str(incident_id),
            {"updated_by": updated_by, **command.model_dump(exclude_none=True)},
        )
        return incident

    async def resolve_incident(
        self,
        incident_id: uuid.UUID,
        command: ResolveIncidentCommand,
        resolved_by: str,
    ) -> Incident:
        incident = await self._repo.update(
            incident_id,
            UpdateIncidentCommand(status="resolved"),
        )
        await cache_delete(f"incidents:{incident_id}")
        await cache_invalidate_pattern("incidents:list:*")
        await publish_incident_event(
            "incident.resolved",
            str(incident_id),
            {"resolved_by": resolved_by, "resolution": command.resolution},
        )
        logger.info("incident_service.resolved", incident_id=str(incident_id))
        return incident

    async def get_stats(self) -> IncidentStats:
        cache_key = "incidents:stats"
        cached = await cache_get(cache_key)
        if cached:
            return IncidentStats.model_validate(cached)

        stats = await self._repo.get_stats()
        await cache_set(cache_key, stats.model_dump(), STATS_TTL)
        return stats
