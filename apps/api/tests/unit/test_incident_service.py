"""Unit tests for IncidentService."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import NotFoundError
from src.domain.incidents.models import (
    CreateIncidentCommand,
    Incident,
    IncidentStats,
    ListIncidentsQuery,
    PaginatedIncidents,
    UpdateIncidentCommand,
)
from src.services.incident_service import IncidentService


def _mock_incident(overrides: dict | None = None) -> Incident:
    base = {
        "id": uuid.uuid4(),
        "title": "Payment service down",
        "description": "Payment service returning 503 errors",
        "severity": "critical",
        "status": "open",
        "service": "payment-service",
        "environment": "production",
        "tags": ["payment", "503"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "evidence": [],
        "timeline": [],
    }
    if overrides:
        base.update(overrides)
    return Incident(**base)


@pytest.mark.asyncio
class TestIncidentService:
    @patch("src.services.incident_service.SQLIncidentRepository")
    @patch("src.services.incident_service.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("src.services.incident_service.cache_set", new_callable=AsyncMock)
    @patch("src.services.incident_service.cache_invalidate_pattern", new_callable=AsyncMock)
    @patch("src.services.incident_service.publish_incident_event", new_callable=AsyncMock)
    async def test_create_incident(
        self, mock_publish, mock_invalidate, mock_set, mock_get, mock_repo_cls
    ):
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo
        expected = _mock_incident()
        mock_repo.create.return_value = expected

        svc = IncidentService(MagicMock())
        command = CreateIncidentCommand(
            title="Payment service down",
            description="Payment service returning 503 errors",
            severity="critical",
            service="payment-service",
        )
        result = await svc.create_incident(command, created_by="user-1")

        assert result.severity == "critical"
        mock_repo.create.assert_called_once()
        mock_invalidate.assert_called_once()
        mock_publish.assert_called_once()

    @patch("src.services.incident_service.SQLIncidentRepository")
    @patch("src.services.incident_service.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("src.services.incident_service.cache_set", new_callable=AsyncMock)
    async def test_get_incident_not_found(self, mock_set, mock_get, mock_repo_cls):
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_by_id.return_value = None

        svc = IncidentService(MagicMock())
        with pytest.raises(NotFoundError):
            await svc.get_incident(uuid.uuid4())

    @patch("src.services.incident_service.SQLIncidentRepository")
    @patch("src.services.incident_service.cache_get", new_callable=AsyncMock)
    async def test_get_incident_uses_cache(self, mock_get, mock_repo_cls):
        incident = _mock_incident()
        mock_get.return_value = incident.model_dump(mode="json")
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        svc = IncidentService(MagicMock())
        result = await svc.get_incident(incident.id)

        assert result.id == incident.id
        mock_repo.get_by_id.assert_not_called()

    @patch("src.services.incident_service.SQLIncidentRepository")
    @patch("src.services.incident_service.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("src.services.incident_service.cache_set", new_callable=AsyncMock)
    async def test_list_incidents_paginated(self, mock_set, mock_get, mock_repo_cls):
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.list.return_value = PaginatedIncidents(
            items=[_mock_incident()], total=1, page=1, size=20, pages=1
        )

        svc = IncidentService(MagicMock())
        result = await svc.list_incidents(ListIncidentsQuery())

        assert result.total == 1
        assert len(result.items) == 1

    @patch("src.services.incident_service.SQLIncidentRepository")
    @patch("src.services.incident_service.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("src.services.incident_service.cache_set", new_callable=AsyncMock)
    async def test_get_stats(self, mock_set, mock_get, mock_repo_cls):
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_stats.return_value = IncidentStats(
            open=5, critical=2, resolved_today=3, avg_resolution_hours=4.5
        )

        svc = IncidentService(MagicMock())
        stats = await svc.get_stats()

        assert stats.open == 5
        assert stats.critical == 2
