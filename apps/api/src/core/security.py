"""JWT / Keycloak token verification."""

from __future__ import annotations

import httpx
import structlog
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings
from .exceptions import AuthenticationError, AuthorizationError

logger = structlog.get_logger(__name__)

_JWKS_CACHE: dict[str, object] = {}


class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    name: str | None = None
    realm_access: dict[str, list[str]] = {}
    resource_access: dict[str, dict[str, list[str]]] = {}
    preferred_username: str | None = None

    @property
    def roles(self) -> list[str]:
        return self.realm_access.get("roles", [])


async def get_jwks() -> dict[str, object]:
    global _JWKS_CACHE
    if _JWKS_CACHE:
        return _JWKS_CACHE

    jwks_url = (
        f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        "/protocol/openid-connect/certs"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _JWKS_CACHE = response.json()
    return _JWKS_CACHE


async def verify_token(token: str) -> TokenPayload:
    try:
        jwks = await get_jwks()
        header = jwt.get_unverified_header(token)
        key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")),  # type: ignore[union-attr]
            None,
        )
        if key is None:
            raise AuthenticationError("Unknown token key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            options={"verify_exp": True},
        )
        return TokenPayload(**payload)
    except JWTError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc


def require_roles(token: TokenPayload, *roles: str) -> None:
    if not any(r in token.roles for r in roles):
        raise AuthorizationError(
            f"Requires one of: {roles}. Token has: {token.roles}"
        )
