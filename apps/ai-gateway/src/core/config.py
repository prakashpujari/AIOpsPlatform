"""AI Gateway configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # PagerDuty integration settings – optional in dev
    pagerduty_api_token: str = ""
    pagerduty_service_id: str = ""

    # Validation for routing configuration
    @field_validator('model_routing_strategy')
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        allowed = {'intent', 'cost', 'latency', 'quality'}
        if v not in allowed:
            raise ValueError(f"model_routing_strategy must be one of {allowed}, got '{v}'")
        return v

    @field_validator('model_routing_max_fallbacks')
    @classmethod
    def validate_max_fallbacks(cls, v: int) -> int:
        if v < 0:
            raise ValueError('model_routing_max_fallbacks must be non‑negative')
        return v

    env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_key: SecretStr = Field(default="changeme")

    # ── Redis ──────────────────────────────────
    redis_url: RedisDsn = Field(default="redis://:changeme@localhost:6379/1")
    semantic_cache_ttl: int = 3600
    semantic_cache_threshold: float = 0.95

    # ── Model Serving Endpoints ────────────────
    vllm_base_url: str = "http://vllm-server:8080"
    ollama_base_url: str = "http://ollama:11434"
    tgi_base_url: str = "http://tgi-server:8081"

    # ── Routing ────────────────────────────────
    default_model: str = "llama3.3-70b"
    max_routing_retries: int = 3
    routing_timeout_seconds: int = 120
    model_routing_strategy: str = "intent"  # options: intent, cost, latency, quality
    model_routing_max_fallbacks: int = 3

    # ── Cost ───────────────────────────────────
    cost_alert_threshold_usd: float = 10.0
    daily_budget_usd: float = 500.0

    # ── Policy ────────────────────────────────
    pii_masking_enabled: bool = True
    prompt_injection_detection_enabled: bool = True
    content_filter_enabled: bool = True
    max_prompt_length: int = 32000
    max_response_length: int = 16000

    # ── Health ─────────────────────────────────
    health_check_interval_seconds: int = 30
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60

    # ── Observability ──────────────────────────
    otel_service_name: str = "ai-gateway"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_enabled: bool = True
    # Groq API key (optional – set to enable Groq provider)
    groq_api_key: SecretStr = Field(default="")

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()


settings = get_settings()
