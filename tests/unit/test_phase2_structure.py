"""Phase 2 — Frontend structure tests."""

from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).parents[2]
WEB = ROOT / "apps/web"


def _exists(rel: str) -> bool:
    return (WEB / rel).exists()


def test_config_files_exist() -> None:
    for f in ["package.json", "tsconfig.json", "next.config.ts",
              "tailwind.config.ts", "postcss.config.js", ".eslintrc.json",
              "jest.config.ts", "jest.setup.ts"]:
        assert _exists(f), f"Missing: apps/web/{f}"


def test_all_10_dashboard_pages_exist() -> None:
    pages = [
        "src/app/(dashboard)/chat/page.tsx",
        "src/app/(dashboard)/incidents/page.tsx",
        "src/app/(dashboard)/rca/page.tsx",
        "src/app/(dashboard)/agents/page.tsx",
        "src/app/(dashboard)/search/page.tsx",
        "src/app/(dashboard)/health/page.tsx",
        "src/app/(dashboard)/costs/page.tsx",
        "src/app/(dashboard)/evaluation/page.tsx",
        "src/app/(dashboard)/admin/page.tsx",
        "src/app/(dashboard)/audit/page.tsx",
    ]
    missing = [p for p in pages if not _exists(p)]
    assert not missing, f"Missing pages: {missing}"


def test_auth_files_exist() -> None:
    for f in ["src/lib/auth/config.ts", "src/lib/auth/index.ts",
              "src/lib/rbac.ts", "src/middleware.ts",
              "src/app/(auth)/login/page.tsx",
              "src/app/api/auth/[...nextauth]/route.ts"]:
        assert _exists(f), f"Missing: {f}"


def test_all_components_exist() -> None:
    components = [
        "src/components/layout/Sidebar.tsx",
        "src/components/layout/Header.tsx",
        "src/components/auth/LoginForm.tsx",
        "src/components/common/StatusBadge.tsx",
        "src/components/common/MetricCard.tsx",
        "src/components/common/LoadingSpinner.tsx",
        "src/components/chat/ChatInterface.tsx",
        "src/components/incidents/IncidentDashboard.tsx",
        "src/components/rca/RCADashboard.tsx",
        "src/components/agents/AgentTraceDashboard.tsx",
        "src/components/search/KnowledgeSearch.tsx",
        "src/components/health/ServiceHealthDashboard.tsx",
        "src/components/costs/CostDashboard.tsx",
        "src/components/evaluation/EvaluationDashboard.tsx",
        "src/components/admin/UserAdminDashboard.tsx",
        "src/components/audit/AuditDashboard.tsx",
    ]
    missing = [c for c in components if not _exists(c)]
    assert not missing, f"Missing components: {missing}"


def test_rbac_covers_all_roles() -> None:
    content = (WEB / "src/lib/rbac.ts").read_text()
    for role in ["admin", "operator", "analyst", "viewer", "compliance"]:
        assert role in content, f"RBAC missing role: {role}"


def test_keycloak_auth_configured() -> None:
    content = (WEB / "src/lib/auth/index.ts").read_text()
    assert "KeycloakProvider" in content


def test_streaming_chat_api_exists() -> None:
    content = (WEB / "src/lib/api/chat.ts").read_text()
    assert "streamChat" in content
    assert "EventSource" in content or "fetch" in content


def test_zustand_stores_exist() -> None:
    for f in ["src/store/chatStore.ts", "src/store/uiStore.ts"]:
        assert _exists(f), f"Missing store: {f}"


def test_package_json_has_required_deps() -> None:
    import json
    pkg = json.loads((WEB / "package.json").read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    required = ["next", "react", "next-auth", "zustand", "@tanstack/react-query",
                "recharts", "tailwindcss", "@mui/material", "typescript"]
    for dep in required:
        assert dep in deps, f"package.json missing dependency: {dep}"


def test_middleware_has_route_protection() -> None:
    content = (WEB / "src/middleware.ts").read_text()
    assert "/admin" in content
    assert "/audit" in content
    assert "redirect" in content


def test_tests_exist() -> None:
    for f in ["src/__tests__/rbac.test.ts",
              "src/__tests__/StatusBadge.test.tsx",
              "src/__tests__/MetricCard.test.tsx"]:
        assert _exists(f), f"Missing test: {f}"
