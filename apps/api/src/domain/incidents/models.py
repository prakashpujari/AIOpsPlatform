"""Incident domain models and DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["critical", "high", "medium", "low", "info"]
IncidentStatus = Literal["open", "in_progress", "resolved", "closed"]
ExternalSystem = Literal["servicenow", "jira"]


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["log", "metric", "trace", "screenshot"]
    content: str
    timestamp: datetime
    source: str


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    actor: str
    action: str
    details: str | None = None


class Incident(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    service: str
    environment: str
    assignee: str | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    external_id: str | None = None
    external_system: ExternalSystem | None = None
    rca_id: uuid.UUID | None = None
    evidence: list[Evidence] = []
    timeline: list[TimelineEvent] = []

    model_config = {"from_attributes": True}


# ── Commands ──────────────────────────────
class CreateIncidentCommand(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    description: str = Field(min_length=10)
    severity: Severity
    service: str = Field(min_length=1, max_length=200)
    environment: str = "production"
    assignee: str | None = None
    tags: list[str] = []


class UpdateIncidentCommand(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=500)
    description: str | None = None
    severity: Severity | None = None
    status: IncidentStatus | None = None
    assignee: str | None = None
    tags: list[str] | None = None


class ResolveIncidentCommand(BaseModel):
    resolution: str = Field(min_length=10)


# ── Queries ───────────────────────────────
class ListIncidentsQuery(BaseModel):
    severity: Severity | None = None
    status: IncidentStatus | None = None
    service: str | None = None
    search: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class IncidentStats(BaseModel):
    open: int
    critical: int
    resolved_today: int
    avg_resolution_hours: float


class PaginatedIncidents(BaseModel):
    items: list[Incident]
    total: int
    page: int
    size: int
    pages: int
