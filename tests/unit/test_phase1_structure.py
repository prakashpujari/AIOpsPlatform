"""Phase 1 — Project structure tests.

Verifies that every required directory and key file exists.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).parents[2]


def _exists(rel: str) -> bool:
    return (ROOT / rel).exists()


REQUIRED_DIRS = [
    "apps/web/src",
    "apps/api/src",
    "apps/ai-gateway/src",
    "apps/ingestion/src",
    "agents/intent-agent/src",
    "agents/search-agent/src",
    "agents/rca-agent/src",
    "agents/remediation-agent/src",
    "agents/incident-agent/src",
    "agents/evaluation-agent/src",
    "agents/compliance-agent/src",
    "agents/escalation-agent/src",
    "infrastructure/terraform",
    "infrastructure/kubernetes",
    "infrastructure/helm",
    "infrastructure/argocd",
    "observability/prometheus",
    "observability/grafana/dashboards",
    "observability/grafana/datasources",
    "observability/loki",
    "observability/jaeger",
    "observability/opentelemetry",
    "docs/architecture",
    "docs/runbooks",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "tests/load",
    "tests/security",
    "scripts/setup",
    "scripts/migrate",
    ".github/workflows",
]

REQUIRED_FILES = [
    "README.md",
    "CLAUDE.md",
    ".gitignore",
    ".env.example",
    "docker-compose.yml",
    "pyproject.toml",
    "package.json",
    "apps/api/Dockerfile",
    "apps/api/pyproject.toml",
    "apps/api/src/main.py",
    "apps/ai-gateway/Dockerfile",
    "apps/ai-gateway/src/main.py",
    "apps/ingestion/Dockerfile",
    "apps/ingestion/src/main.py",
    "apps/web/Dockerfile",
    "observability/prometheus/prometheus.yml",
    "observability/grafana/datasources/datasources.yml",
    "observability/opentelemetry/otel-collector.yml",
    "scripts/setup/local-dev.sh",
    "scripts/migrate/init.sql",
    ".github/workflows/ci.yml",
]


def test_required_directories_exist() -> None:
    missing = [d for d in REQUIRED_DIRS if not _exists(d)]
    assert not missing, f"Missing directories:\n" + "\n".join(missing)


def test_required_files_exist() -> None:
    missing = [f for f in REQUIRED_FILES if not _exists(f)]
    assert not missing, f"Missing files:\n" + "\n".join(missing)


def test_python_packages_have_init() -> None:
    python_src_dirs = [
        "apps/api/src",
        "apps/ai-gateway/src",
        "apps/ingestion/src",
        "agents/intent-agent/src",
        "agents/search-agent/src",
        "agents/rca-agent/src",
        "agents/remediation-agent/src",
        "agents/incident-agent/src",
        "agents/evaluation-agent/src",
        "agents/compliance-agent/src",
        "agents/escalation-agent/src",
    ]
    missing = [d for d in python_src_dirs if not _exists(f"{d}/__init__.py")]
    assert not missing, f"Missing __init__.py in:\n" + "\n".join(missing)


def test_dockerfiles_have_multistage_builds() -> None:
    for service in ["api", "ai-gateway", "ingestion", "web"]:
        content = (ROOT / f"apps/{service}/Dockerfile").read_text()
        assert "AS development" in content, f"apps/{service}/Dockerfile missing development stage"
        assert "AS production" in content, f"apps/{service}/Dockerfile missing production stage"


def test_env_example_has_required_keys() -> None:
    content = (ROOT / ".env.example").read_text()
    for key in ["POSTGRES_", "REDIS_", "KAFKA_", "VAULT_", "KEYCLOAK_", "AI_GATEWAY_"]:
        assert key in content, f".env.example missing section: {key}"


def test_docker_compose_has_all_services() -> None:
    content = (ROOT / "docker-compose.yml").read_text()
    for service in ["postgres", "redis", "kafka", "milvus", "keycloak", "vault",
                    "prometheus", "grafana", "jaeger", "api", "ai-gateway", "web"]:
        assert service in content, f"docker-compose.yml missing service: {service}"


def test_ci_workflow_has_required_jobs() -> None:
    content = (ROOT / ".github/workflows/ci.yml").read_text()
    for job in ["python-quality", "python-tests", "frontend", "docker-build", "security-scan"]:
        assert job in content, f"CI workflow missing job: {job}"
