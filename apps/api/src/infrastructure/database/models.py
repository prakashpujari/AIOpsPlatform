"""SQLAlchemy ORM models — all tables in one file for Alembic autogenerate."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ── Incidents ──────────────────────────────────────────────────────────────
class IncidentORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_service", "service"),
        Index("ix_incidents_created_at", "created_at"),
        {"schema": "core"},
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    service: Mapped[str] = mapped_column(String(200), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), nullable=False, default="production")
    assignee: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    timeline: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    rca_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


# ── RCA ────────────────────────────────────────────────────────────────────
class RCAORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rca_reports"
    __table_args__ = (
        Index("ix_rca_incident_id", "incident_id"),
        {"schema": "core"},
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    contributing_factors: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    timeline: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    affected_services: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Agent Traces ───────────────────────────────────────────────────────────
class AgentTraceORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_traces"
    __table_args__ = (
        Index("ix_agent_traces_agent_type", "agent_type"),
        Index("ix_agent_traces_session_id", "session_id"),
        Index("ix_agent_traces_started_at", "started_at"),
        {"schema": "core"},
    )

    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    session_id: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="idle")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    steps: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)


# ── Chat Sessions ──────────────────────────────────────────────────────────
class ChatSessionORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
        {"schema": "core"},
    )

    user_id: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="New Chat")
    messages: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)


# ── Users ──────────────────────────────────────────────────────────────────
class UserORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email", "email"),
        {"schema": "core"},
    )

    email: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    department: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    keycloak_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# ── Audit Logs ─────────────────────────────────────────────────────────────
class AuditLogORM(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_resource", "resource"),
        {"schema": "audit"},
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(200), nullable=False)
    user_name: Mapped[str] = mapped_column(String(500), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(200), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ── Cost Records ───────────────────────────────────────────────────────────
class CostRecordORM(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "cost_records"
    __table_args__ = (
        Index("ix_cost_records_date", "date"),
        Index("ix_cost_records_model", "model"),
        {"schema": "aiops"},
    )

    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    agent: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


# ── Evaluation Runs ────────────────────────────────────────────────────────
class EvalRunORM(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "eval_runs"
    __table_args__ = (
        Index("ix_eval_runs_timestamp", "timestamp"),
        {"schema": "aiops"},
    )

    run_name: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ci_gate_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pass")


# ── Knowledge Documents ────────────────────────────────────────────────────
class KnowledgeDocumentORM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_documents_source", "source"),
        {"schema": "core"},
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    doc_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ingested_by: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
