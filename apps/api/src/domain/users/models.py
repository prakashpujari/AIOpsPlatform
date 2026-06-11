"""User domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal["admin", "operator", "analyst", "viewer", "compliance"]


class User(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    roles: list[Role]
    department: str
    keycloak_id: str | None = None
    last_login: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateUserCommand(BaseModel):
    email: str = Field(min_length=3)
    name: str = Field(min_length=1, max_length=500)
    roles: list[Role] = ["viewer"]
    department: str = ""
    keycloak_id: str | None = None


class UpdateUserCommand(BaseModel):
    name: str | None = None
    roles: list[Role] | None = None
    department: str | None = None
    is_active: bool | None = None


class PaginatedUsers(BaseModel):
    items: list[User]
    total: int
    page: int
    size: int
    pages: int
