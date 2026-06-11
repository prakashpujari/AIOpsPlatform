"""Application configuration — all settings sourced from environment."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────
    env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    secret_key: SecretStr = Field(default="changeme-32char-secret-key-here!!")
    allowed_origins: list[str] = ["http://localhost:3000"]
    api_prefix: str = "/api/v1"
    debug: bool = False

    # ── Database ───────────────────────────────
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://aiops:changeme@localhost:5432/aiops_platform"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    # ── Redis ──────────────────────────────────
    redis_url: RedisDsn = Field(default="redis://:changeme@localhost:6379/0")
    redis_ttl_seconds: int = 3600
    cache_ttl_chat: int = 300
    cache_ttl_search: int = 600

    # ── Kafka ──────────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_incidents: str = "aiops.incidents"
    kafka_topic_rca: str = "aiops.rca"
    kafka_topic_alerts: str = "aiops.alerts"
    kafka_topic_audit: str = "aiops.audit"

    # ── Milvus ─────────────────────────────────
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_knowledge: str = "knowledge_base"
    milvus_collection_incidents: str = "incidents"

    # ── Vault ──────────────────────────────────
    vault_addr: AnyHttpUrl = Field(default="http://localhost:8200")
    vault_token: SecretStr = Field(default="dev-root-token")
    vault_mount: str = "secret"

    # ── Keycloak ───────────────────────────────
    keycloak_url: AnyHttpUrl = Field(default="http://localhost:8080")
    keycloak_realm: str = "aiops-platform"
    keycloak_client_id: str = "api-client"
    keycloak_client_secret: SecretStr = Field(default="changeme")

    # ── AI Gateway ─────────────────────────────
    ai_gateway_url: AnyHttpUrl = Field(default="http://localhost:8001")
    ai_gateway_api_key: SecretStr = Field(default="changeme")
    ai_gateway_timeout: int = 120

    # ── ServiceNow ─────────────────────────────
    servicenow_instance: str = ""
    servicenow_user: str = ""
    servicenow_password: SecretStr = Field(default="")

    # ── Jira ───────────────────────────────────
    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: SecretStr = Field(default="")
    jira_project_key: str = "AIOPS"

    # ── OpenTelemetry ──────────────────────────
    otel_service_name: str = "aiops-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_enabled: bool = True

    # ── Rate Limiting ──────────────────────────
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 60
    rate_limit_chat_rpm: int = 60

    # ── Pagination ─────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def db_url_str(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
