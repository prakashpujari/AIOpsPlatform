"""FastAPI dependency injection — auth, db, cache, services."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .exceptions import AuthenticationError, AuthorizationError
from .security import TokenPayload, verify_token

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenPayload:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        return await verify_token(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenPayload | None:
    if not credentials:
        return None
    try:
        return await verify_token(credentials.credentials)
    except AuthenticationError:
        return None


def require_role(*roles: str):  # type: ignore[no-untyped-def]
    async def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if not any(r in user.roles for r in roles):
            raise HTTPException(
                status_code=403,
                detail=f"Role required: {', '.join(roles)}",
            )
        return user

    return _check


# ── Typed annotated deps ───────────────────
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser = Annotated[TokenPayload, Depends(require_role("admin"))]
OperatorUser = Annotated[TokenPayload, Depends(require_role("admin", "operator"))]
AnalystUser = Annotated[TokenPayload, Depends(require_role("admin", "operator", "analyst"))]
ComplianceUser = Annotated[TokenPayload, Depends(require_role("admin", "compliance"))]
