"""Phase 4 — AI Gateway structure tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
GW = ROOT / "apps/ai-gateway"


def _exists(rel: str) -> bool:
    return (GW / rel).exists()


def test_registry_files_exist() -> None:
    for f in [
        "src/registry/__init__.py",
        "src/registry/schemas.py",
        "src/registry/model_registry.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_router_files_exist() -> None:
    for f in [
        "src/router/__init__.py",
        "src/router/routing_engine.py",
        "src/router/strategies/__init__.py",
        "src/router/strategies/intent_strategy.py",
        "src/router/strategies/cost_strategy.py",
        "src/router/strategies/latency_strategy.py",
        "src/router/strategies/failover_strategy.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_policy_files_exist() -> None:
    for f in [
        "src/policy/__init__.py",
        "src/policy/policy_engine.py",
        "src/policy/pii_masker.py",
        "src/policy/prompt_injection_detector.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_health_files_exist() -> None:
    for f in [
        "src/health/__init__.py",
        "src/health/circuit_breaker.py",
        "src/health/health_monitor.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_cost_files_exist() -> None:
    assert _exists("src/cost/__init__.py")
    assert _exists("src/cost/cost_engine.py")


def test_fallback_files_exist() -> None:
    assert _exists("src/fallback/__init__.py")
    assert _exists("src/fallback/fallback_engine.py")


def test_provider_files_exist() -> None:
    for f in [
        "src/providers/__init__.py",
        "src/providers/base.py",
        "src/providers/vllm_provider.py",
        "src/providers/ollama_provider.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_api_files_exist() -> None:
    for f in [
        "src/api/__init__.py",
        "src/api/schemas.py",
        "src/api/chat.py",
        "src/api/gateway_health.py",
    ]:
        assert _exists(f), f"Missing: {f}"


def test_main_app_wires_routers() -> None:
    content = (GW / "src/main.py").read_text()
    assert "chat_router" in content
    assert "health_router" in content
    assert "lifespan" in content
    assert "health_monitor" in content
    assert "generate_latest" in content


def test_model_registry_has_six_models() -> None:
    content = (GW / "src/registry/model_registry.py").read_text()
    model_ids = ["llama3.3-70b", "deepseek-r1", "deepseek-coder", "qwen3-72b", "phi4-14b", "gemma2-9b"]
    for mid in model_ids:
        assert mid in content, f"Model {mid} missing from registry"


def test_gateway_never_calls_llm_directly_from_policy() -> None:
    """Policy layer must not import providers (enforces gateway flow)."""
    policy_dir = GW / "src/policy"
    for py_file in policy_dir.rglob("*.py"):
        content = py_file.read_text()
        assert "vllm_provider" not in content, f"Policy imports vLLM provider: {py_file}"
        assert "ollama_provider" not in content, f"Policy imports Ollama provider: {py_file}"


def test_circuit_breaker_state_machine_documented() -> None:
    content = (GW / "src/health/circuit_breaker.py").read_text()
    assert "CircuitState" in content
    assert "CLOSED" in content
    assert "OPEN" in content
    assert "HALF_OPEN" in content


def test_all_routing_strategies_implemented() -> None:
    strategies_dir = GW / "src/router/strategies"
    required = {"intent_strategy", "cost_strategy", "latency_strategy", "failover_strategy"}
    found = {f.stem for f in strategies_dir.glob("*.py") if not f.stem.startswith("_")}
    assert required.issubset(found), f"Missing strategies: {required - found}"


def test_unit_tests_exist() -> None:
    tests_dir = GW / "tests/unit"
    test_files = list(tests_dir.glob("test_*.py"))
    assert len(test_files) >= 4, f"Expected at least 4 test files, found {len(test_files)}"
