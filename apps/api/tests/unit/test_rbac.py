"""Unit tests for security / RBAC."""

from __future__ import annotations

import pytest

from src.core.exceptions import AuthorizationError
from src.core.security import TokenPayload, require_roles


class TestRequireRoles:
    def _make_token(self, *roles: str) -> TokenPayload:
        return TokenPayload(
            sub="user-1",
            email="user@bank.com",
            realm_access={"roles": list(roles)},
        )

    def test_admin_passes_all_checks(self):
        token = self._make_token("admin")
        require_roles(token, "admin")
        require_roles(token, "admin", "operator")
        require_roles(token, "viewer", "admin")

    def test_viewer_fails_admin_check(self):
        token = self._make_token("viewer")
        with pytest.raises(AuthorizationError):
            require_roles(token, "admin")

    def test_operator_passes_operator_check(self):
        token = self._make_token("operator")
        require_roles(token, "admin", "operator")

    def test_empty_roles_fails(self):
        token = self._make_token()
        with pytest.raises(AuthorizationError):
            require_roles(token, "viewer")

    def test_token_roles_property(self):
        token = self._make_token("admin", "compliance")
        assert "admin" in token.roles
        assert "compliance" in token.roles
        assert "viewer" not in token.roles
