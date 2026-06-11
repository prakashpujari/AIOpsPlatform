"""User administration API."""

from __future__ import annotations

import math
import uuid

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import AdminUser, ComplianceUser
from ...domain.users.models import CreateUserCommand, UpdateUserCommand
from ...infrastructure.database.models import UserORM
from ...infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Administration"])


def _user_to_dict(u: UserORM) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "name": u.name,
        "roles": u.roles,
        "department": u.department,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat(),
        "updated_at": u.updated_at.isoformat(),
    }


@router.get("/users")
async def list_users(
    _: ComplianceUser,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(UserORM).where(UserORM.is_active == True)
    if search:
        term = f"%{search}%"
        from sqlalchemy import or_
        stmt = stmt.where(or_(UserORM.name.ilike(term), UserORM.email.ilike(term)))
    stmt = stmt.order_by(UserORM.name).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return [_user_to_dict(r) for r in rows]


@router.post("/users", status_code=201)
async def create_user(
    command: CreateUserCommand,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = UserORM(**command.model_dump())
    db.add(user)
    await db.flush()
    return _user_to_dict(user)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    command: UpdateUserCommand,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await db.get(UserORM, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in command.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    await db.flush()
    return _user_to_dict(user)


@router.delete("/users/{user_id}", status_code=204)
async def deactivate_user(
    user_id: uuid.UUID,
    _: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await db.get(UserORM, user_id)
    if user:
        user.is_active = False
        await db.flush()
