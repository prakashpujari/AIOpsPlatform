"""Initial schema — all core tables.

Revision ID: 001
Revises:
Create Date: 2026-06-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.execute("CREATE SCHEMA IF NOT EXISTS aiops")

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # ── incidents ─────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("service", sa.String(200), nullable=False),
        sa.Column("environment", sa.String(50), nullable=False, server_default="production"),
        sa.Column("assignee", sa.String(200)),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("external_id", sa.String(200)),
        sa.Column("external_system", sa.String(50)),
        sa.Column("evidence", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("timeline", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("rca_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
        schema="core",
    )
    op.create_index("ix_incidents_severity", "incidents", ["severity"], schema="core")
    op.create_index("ix_incidents_status", "incidents", ["status"], schema="core")
    op.create_index("ix_incidents_service", "incidents", ["service"], schema="core")
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"], schema="core")

    # ── rca_reports ───────────────────────────
    op.create_table(
        "rca_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("root_cause", sa.Text, nullable=False),
        sa.Column("contributing_factors", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("timeline", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("affected_services", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("suggested_fix", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_by", sa.String(200)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )

    # ── agent_traces ──────────────────────────
    op.create_table(
        "agent_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("session_id", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="idle"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("steps", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("input_summary", sa.Text, nullable=False),
        sa.Column("output_summary", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("approved_by", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )

    # ── chat_sessions ─────────────────────────
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.String(200), nullable=False),
        sa.Column("title", sa.String(500), nullable=False, server_default="New Chat"),
        sa.Column("messages", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )

    # ── users ─────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(500), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("department", sa.String(200), nullable=False, server_default=""),
        sa.Column("keycloak_id", sa.String(200)),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )

    # ── knowledge_documents ───────────────────
    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("ingested_by", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="core",
    )

    # ── audit_logs ────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.String(200), nullable=False),
        sa.Column("user_name", sa.String(500), nullable=False),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("resource", sa.String(200), nullable=False),
        sa.Column("resource_id", sa.String(200), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("details", postgresql.JSONB),
        schema="audit",
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], schema="audit")
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"], schema="audit")

    # ── cost_records ──────────────────────────
    op.create_table(
        "cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("agent", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        schema="aiops",
    )

    # ── eval_runs ─────────────────────────────
    op.create_table(
        "eval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("run_name", sa.String(200), nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("total_samples", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pass_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("ci_gate_status", sa.String(20), nullable=False, server_default="pass"),
        schema="aiops",
    )


def downgrade() -> None:
    for schema, table in [
        ("aiops", "eval_runs"), ("aiops", "cost_records"),
        ("audit", "audit_logs"),
        ("core", "knowledge_documents"), ("core", "users"),
        ("core", "chat_sessions"), ("core", "agent_traces"),
        ("core", "rca_reports"), ("core", "incidents"),
    ]:
        op.drop_table(table, schema=schema)
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE")
    op.execute("DROP SCHEMA IF EXISTS aiops CASCADE")
