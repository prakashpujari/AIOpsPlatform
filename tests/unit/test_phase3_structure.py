"""Phase 3 — Backend structure tests."""

from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).parents[2]
API = ROOT / "apps/api"


def _exists(rel: str) -> bool:
    return (API / rel).exists()


def test_core_files_exist() -> None:
    for f in ["src/core/config.py", "src/core/exceptions.py",
              "src/core/logging.py", "src/core/tracing.py",
              "src/core/security.py", "src/core/dependencies.py"]:
        assert _exists(f), f"Missing: {f}"


def test_infrastructure_files_exist() -> None:
    for f in [
        "src/infrastructure/database/base.py",
        "src/infrastructure/database/session.py",
        "src/infrastructure/database/models.py",
        "src/infrastructure/cache/redis_client.py",
        "src/infrastructure/kafka/producer.py",
        "src/infrastructure/repositories/incident_repository.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_domain_models_exist() -> None:
    for domain in ["incidents", "rca", "agents", "chat", "users", "audit", "costs", "evaluation"]:
        assert _exists(f"src/domain/{domain}/models.py"), f"Missing domain model: {domain}"


def test_service_layer_exists() -> None:
    for f in ["src/services/incident_service.py",
              "src/services/chat_service.py",
              "src/services/audit_service.py"]:
        assert _exists(f), f"Missing service: {f}"


def test_api_routers_exist() -> None:
    for router in ["incidents", "rca", "agents", "chat", "health",
                   "costs", "evaluation", "admin", "audit", "search", "router"]:
        assert _exists(f"src/api/v1/{router}.py"), f"Missing router: {router}"


def test_middleware_exists() -> None:
    for f in ["src/middleware/logging_middleware.py",
              "src/middleware/rate_limit_middleware.py",
              "src/middleware/error_handler.py"]:
        assert _exists(f), f"Missing middleware: {f}"


def test_alembic_setup() -> None:
    assert _exists("alembic.ini")
    assert _exists("alembic/env.py")
    assert _exists("alembic/versions/001_initial_schema.py")


def test_main_app_has_all_routers_wired() -> None:
    content = (API / "src/main.py").read_text()
    assert "v1_router" in content
    assert "CORSMiddleware" in content
    assert "RequestLoggingMiddleware" in content
    assert "RateLimitMiddleware" in content
    assert "register_exception_handlers" in content
    assert "metrics" in content


def test_clean_architecture_separation() -> None:
    domain_path = API / "src/domain"
    for domain_file in domain_path.rglob("*.py"):
        content = domain_file.read_text()
        # Domain should not import from infrastructure
        assert "from ...infrastructure" not in content, \
            f"Domain leaks into infrastructure: {domain_file}"
        assert "from sqlalchemy" not in content, \
            f"Domain imports SQLAlchemy: {domain_file}"


def test_repository_pattern() -> None:
    repo = (API / "src/domain/incidents/repository.py").read_text()
    assert "ABC" in repo
    assert "abstractmethod" in repo


def test_pydantic_models_have_validators() -> None:
    content = (API / "src/domain/incidents/models.py").read_text()
    assert "Field" in content
    assert "min_length" in content or "ge=" in content


def test_settings_uses_pydantic() -> None:
    content = (API / "src/core/config.py").read_text()
    assert "BaseSettings" in content
    assert "lru_cache" in content


def test_unit_tests_exist() -> None:
    for f in ["tests/unit/test_domain_models.py",
              "tests/unit/test_incident_service.py",
              "tests/unit/test_rbac.py"]:
        assert _exists(f), f"Missing test: {f}"
