"""RCA domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RCATimelineNode(BaseModel):
    timestamp: datetime
    event: str
    service: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    is_root_cause: bool = False


class RCA(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    root_cause: str
    contributing_factors: list[str]
    timeline: list[RCATimelineNode]
    affected_services: list[str]
    suggested_fix: str
    confidence: float
    generated_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None

    model_config = {"from_attributes": True}


class GenerateRCACommand(BaseModel):
    incident_id: uuid.UUID
    additional_context: str | None = None


class ApproveRCACommand(BaseModel):
    approved_by: str
