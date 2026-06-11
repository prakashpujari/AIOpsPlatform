"""Agent trace domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


AgentStatus = Literal["idle", "running", "completed", "failed", "waiting_approval"]
StepType = Literal["llm_call", "tool_call", "decision", "human_approval", "memory_read", "memory_write"]
StepStatus = Literal["pending", "running", "completed", "failed"]


class AgentStep(BaseModel):
    id: str
    step_number: int
    name: str
    type: StepType
    status: StepStatus
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


class AgentTrace(BaseModel):
    id: uuid.UUID
    agent_type: str
    session_id: str
    status: AgentStatus
    started_at: datetime
    completed_at: datetime | None = None
    steps: list[AgentStep]
    total_tokens: int
    total_cost_usd: float
    model_used: str
    input_summary: str
    output_summary: str | None = None
    error_message: str | None = None
    requires_approval: bool = False
    approved_by: str | None = None

    model_config = {"from_attributes": True}


class ApproveAgentCommand(BaseModel):
    trace_id: uuid.UUID
    approved_by: str
    approved: bool
    reason: str | None = None
