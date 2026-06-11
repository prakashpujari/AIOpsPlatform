"""Audit log domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: str
    user_name: str
    action: str
    resource: str
    resource_id: str
    ip_address: str
    user_agent: str
    status: Literal["success", "failure"]
    details: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class CreateAuditLogCommand(BaseModel):
    user_id: str
    user_name: str
    action: str
    resource: str
    resource_id: str
    ip_address: str
    user_agent: str
    status: Literal["success", "failure"] = "success"
    details: dict[str, Any] | None = None


class AuditQuery(BaseModel):
    user_id: str | None = None
    resource: str | None = None
    action: str | None = None
    status: Literal["success", "failure"] | None = None
    search: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=25, ge=1, le=100)


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLog]
    total: int
    page: int
    size: int
    pages: int
