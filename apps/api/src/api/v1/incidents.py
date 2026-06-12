"""Incident management API — CRUD + stats + external ticket creation."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AnalystUser, CurrentUser, OperatorUser
from ...domain.incidents.models import (
    CreateIncidentCommand,
    ListIncidentsQuery,
    ResolveIncidentCommand,
    UpdateIncidentCommand,
)
from ...infrastructure.database.session import get_db, get_read_db
from ...services.audit_service import AuditService
from ...services.incident_service import IncidentService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _get_service(db: AsyncSession = Depends(get_db)) -> IncidentService:
    # Primary session for write operations
    return IncidentService(db)

def _get_service_read(db: AsyncSession = Depends(get_read_db)) -> IncidentService:
    """Return a read‑only IncidentService.
    If a replica engine is configured, ``get_read_db`` will provide a session
    bound to that replica; otherwise it falls back to the primary DB.
    """
    return IncidentService(db)


def _get_audit(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get("/stats")
async def get_stats(
    _: CurrentUser,
    svc: IncidentService = Depends(_get_service),
) -> dict:
    stats = await svc.get_stats()
    return stats.model_dump()


@router.get("")
async def list_incidents(
    user: CurrentUser,
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    svc: IncidentService = Depends(_get_service),
) -> dict:
    query = ListIncidentsQuery(
        severity=severity,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        service=service,
        search=search,
        page=page,
        size=size,
    )
    result = await svc.list_incidents(query)
    return result.model_dump(mode="json")


@router.post("", status_code=201)
async def create_incident(
    command: CreateIncidentCommand,
    user: OperatorUser,
    svc: IncidentService = Depends(_get_service),
    audit: AuditService = Depends(_get_audit),
) -> dict:
    incident = await svc.create_incident(command, created_by=user.sub)
    await audit.log_from_request("incidents", str(incident.id), "create", user)
    return incident.model_dump(mode="json")


@router.get("/{incident_id}")
async def get_incident(
    incident_id: uuid.UUID,
    _: CurrentUser,
    svc: IncidentService = Depends(_get_service),
) -> dict:
    incident = await svc.get_incident(incident_id)
    return incident.model_dump(mode="json")


@router.patch("/{incident_id}")
async def update_incident(
    incident_id: uuid.UUID,
    command: UpdateIncidentCommand,
    user: OperatorUser,
    svc: IncidentService = Depends(_get_service),
) -> dict:
    incident = await svc.update_incident(incident_id, command, updated_by=user.sub)
    return incident.model_dump(mode="json")


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: uuid.UUID,
    command: ResolveIncidentCommand,
    user: OperatorUser,
    svc: IncidentService = Depends(_get_service),
) -> dict:
    incident = await svc.resolve_incident(incident_id, command, resolved_by=user.sub)
    return incident.model_dump(mode="json")


@router.post("/{incident_id}/external")
async def create_external_ticket(
    incident_id: uuid.UUID,
    body: dict,
    user: OperatorUser,
    svc: IncidentService = Depends(_get_service),
) -> dict:
    system = body.get("system", "servicenow")
    incident = await svc.get_incident(incident_id)
    # External ticket creation delegated to Phase 9 (ServiceNow/Jira connectors)
    return {
        "external_id": f"AIOPS-{str(incident_id)[:8].upper()}",
        "url": f"https://example.{system}.com/incident/{incident_id}",
        "system": system,
    }
