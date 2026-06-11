"""Unit tests for domain model validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.domain.incidents.models import (
    CreateIncidentCommand,
    Incident,
    ListIncidentsQuery,
    UpdateIncidentCommand,
)
from src.domain.users.models import CreateUserCommand
from src.domain.chat.models import SearchQuery, SendMessageCommand


class TestIncidentModels:
    def test_create_command_valid(self):
        cmd = CreateIncidentCommand(
            title="Database connection timeout",
            description="PostgreSQL connection pool exhausted causing 503s",
            severity="high",
            service="account-service",
        )
        assert cmd.severity == "high"
        assert cmd.environment == "production"

    def test_create_command_title_too_short(self):
        with pytest.raises(ValidationError):
            CreateIncidentCommand(
                title="AB",
                description="short",
                severity="low",
                service="svc",
            )

    def test_create_command_invalid_severity(self):
        with pytest.raises(ValidationError):
            CreateIncidentCommand(
                title="Valid incident title here",
                description="Valid description for the incident",
                severity="extreme",  # invalid
                service="some-service",
            )

    def test_list_query_defaults(self):
        q = ListIncidentsQuery()
        assert q.page == 1
        assert q.size == 20
        assert q.severity is None

    def test_list_query_page_ge_1(self):
        with pytest.raises(ValidationError):
            ListIncidentsQuery(page=0)

    def test_list_query_size_max(self):
        with pytest.raises(ValidationError):
            ListIncidentsQuery(size=200)

    def test_update_command_partial(self):
        cmd = UpdateIncidentCommand(severity="critical")
        assert cmd.severity == "critical"
        assert cmd.title is None
        assert cmd.status is None


class TestUserModels:
    def test_create_user_defaults_viewer(self):
        cmd = CreateUserCommand(email="user@bank.com", name="John Doe")
        assert cmd.roles == ["viewer"]

    def test_create_user_multiple_roles(self):
        cmd = CreateUserCommand(
            email="ops@bank.com",
            name="Ops User",
            roles=["operator", "analyst"],
        )
        assert "operator" in cmd.roles

    def test_create_user_invalid_role(self):
        with pytest.raises(ValidationError):
            CreateUserCommand(email="x@bank.com", name="X", roles=["superadmin"])


class TestChatModels:
    def test_send_message_valid(self):
        cmd = SendMessageCommand(message="What caused the P1 incident?")
        assert len(cmd.message) > 0

    def test_send_message_empty(self):
        with pytest.raises(ValidationError):
            SendMessageCommand(message="")

    def test_search_query_defaults(self):
        q = SearchQuery(query="kafka consumer lag")
        assert q.top_k == 5

    def test_search_query_top_k_bounds(self):
        with pytest.raises(ValidationError):
            SearchQuery(query="test", top_k=25)
