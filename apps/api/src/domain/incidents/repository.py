"""Abstract incident repository — port in hexagonal architecture."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from .models import (
    CreateIncidentCommand,
    Incident,
    IncidentStats,
    ListIncidentsQuery,
    PaginatedIncidents,
    UpdateIncidentCommand,
)


class IncidentRepository(ABC):
    @abstractmethod
    async def create(self, command: CreateIncidentCommand, created_by: str) -> Incident: ...

    @abstractmethod
    async def get_by_id(self, incident_id: uuid.UUID) -> Incident | None: ...

    @abstractmethod
    async def list(self, query: ListIncidentsQuery) -> PaginatedIncidents: ...

    @abstractmethod
    async def update(self, incident_id: uuid.UUID, command: UpdateIncidentCommand) -> Incident: ...

    @abstractmethod
    async def delete(self, incident_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def get_stats(self) -> IncidentStats: ...
