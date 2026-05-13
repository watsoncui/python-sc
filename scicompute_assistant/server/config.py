"""Runtime configuration loaded from environment variables.

All settings are grouped into three nested models to prevent the
single-flat-class anti-pattern from growing unboundedly:

    LLMConfig           — provider keys, base URLs, rate limits
    SandboxConfig       — execution timeout, restriction level
    ObservabilityConfig — logging, alert webhook URLs
    KnowledgeConfig     — courseware root, embedding model, Chroma path
    SecurityConfig      — encrypted-file fallback (desktop mode)

The outer :class:`ServerSettings` owns the mode flag and CORS list, then
re-exposes each nested group as an attribute.

Environment variable convention
---------------------------------
Every field maps to ``SCICOMP_<SECTION>_<FIELD>`` via pydantic-settings'
``env_nested_delimiter="__"`` feature:

    SCICOMP_LLM__SERVER_API_KEY=sk-...
    SCICOMP_SANDBOX__TIMEOUT_SEC=10
    SCICOMP_OBSERVABILITY__JSON_LOGS=true
    SCICOMP_KNOWLEDGE__EMBEDDING_MODEL=all-MiniLM-L6-v2

For *backwards compatibility* the old flat names (e.g.
``SCICOMP_SERVER_API_KEY``) are supported via ``validation_alias`` so
existing ``.env`` files keep working.  The aliases will be removed in v1.0.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------------------------------------------------------------------- #
# Nested config groups
# --------------------------------------------------------------------------- #
class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_LLM__",
        extra="ignore",
    )

    # Server (teacher-managed)
    server_api_key: str = Field(
        default="",
        validation_alias="SCICOMP_SERVER_API_KEY",
    )
    server_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="SCICOMP_SERVER_BASE_URL",
    )
    server_default_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="SCICOMP_SERVER_DEFAULT_MODEL",
    )
    server_rpm_limit: int = Field(
        default=60,
        validation_alias="SCICOMP_SERVER_RPM_LIMIT",
    )
    server_burst: int = Field(
        default=10,
        validation_alias="SCICOMP_SERVER_BURST",
    )
    max_retries: int = 3

    # Local (student-provided, desktop mode)
    local_default_endpoint: str = Field(
        default="deepseek",
        validation_alias="SCICOMP_LOCAL_DEFAULT_ENDPOINT",
    )
    local_default_model: str = Field(
        default="deepseek-chat",
        validation_alias="SCICOMP_LOCAL_DEFAULT_MODEL",
    )

    # CI / smoke tests: skip real outbound calls
    disable_outbound: bool = Field(
        default=False,
        validation_alias="SCICOMP_DISABLE_OUTBOUND_LLM",
    )


class SandboxConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_SANDBOX__",
        extra="ignore",
    )

    timeout_sec: float = Field(
        default=5.0,
        validation_alias="SCICOMP_SANDBOX_TIMEOUT_SEC",
    )
    restricted: bool = Field(
        default=True,
        validation_alias="SCICOMP_SANDBOX_RESTRICTED",
    )


class ObservabilityConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_OBSERVABILITY__",
        extra="ignore",
    )

    json_logs: bool = Field(
        default=False,
        validation_alias="SCICOMP_JSON_LOGS",
    )
    slack_webhook_url: str = Field(
        default="",
        validation_alias="SCICOMP_SLACK_WEBHOOK_URL",
    )
    pagerduty_routing_key: str = Field(
        default="",
        validation_alias="SCICOMP_PAGERDUTY_ROUTING_KEY",
    )
    http_rpm_limit: int = Field(
        default=60,
        validation_alias="SCICOMP_HTTP_RPM_LIMIT",
    )


class KnowledgeConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_KNOWLEDGE__",
        extra="ignore",
    )

    courseware_root: Path = Field(
        default=Path(__file__).resolve().parents[1] / "assets" / "courseware",
        validation_alias="SCICOMP_COURSEWARE_ROOT",
    )
    chroma_persist_dir: str | None = None
    embedding_model: str = "all-MiniLM-L6-v2"
    force_bow: bool = Field(
        default=False,
        description="Skip ChromaDB even when installed (unit tests, offline CI).",
    )


class SecurityConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_SECURITY__",
        extra="ignore",
    )

    fallback_store_path: Path = Field(
        default=Path.home() / ".scicompute" / "keys.enc.json",
        validation_alias="SCICOMP_FALLBACK_STORE_PATH",
    )
    fallback_passphrase: str = Field(
        default="",
        validation_alias="SCICOMP_FALLBACK_PASSPHRASE",
    )


# --------------------------------------------------------------------------- #
# Top-level settings
# --------------------------------------------------------------------------- #
class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mode: str = "server"
    cors_origins: list[str] = ["*"]

    llm: LLMConfig = Field(default_factory=LLMConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # ------------------------------------------------------------------ #
    # Back-compat shims: keep the old flat names so existing .env files,
    # tests and SCICOMP_* env vars still work until v1.0.
    # ------------------------------------------------------------------ #
    @model_validator(mode="before")
    @classmethod
    def _promote_flat_env(cls, data: dict) -> dict:
        """Fold old SCICOMP_SERVER_API_KEY-style flat keys into sub-models.

        pydantic-settings passes the *merged* env dict here, so we just
        look for the old keys and forward them to the nested defaults.
        The old keys are removed so they don't trigger 'extra=forbid'.
        """
        mapping = {
            # LLM
            "server_api_key": ("llm", "server_api_key"),
            "server_base_url": ("llm", "server_base_url"),
            "server_default_model": ("llm", "server_default_model"),
            "server_rpm_limit": ("llm", "server_rpm_limit"),
            "server_burst": ("llm", "server_burst"),
            "local_default_endpoint": ("llm", "local_default_endpoint"),
            "local_default_model": ("llm", "local_default_model"),
            "disable_outbound_llm": ("llm", "disable_outbound"),
            # Sandbox
            "sandbox_timeout_sec": ("sandbox", "timeout_sec"),
            "sandbox_restricted": ("sandbox", "restricted"),
            # Observability
            "json_logs": ("observability", "json_logs"),
            "slack_webhook_url": ("observability", "slack_webhook_url"),
            "pagerduty_routing_key": ("observability", "pagerduty_routing_key"),
            "http_rpm_limit": ("observability", "http_rpm_limit"),
            # Knowledge
            "courseware_root": ("knowledge", "courseware_root"),
            # Security
            "fallback_store_path": ("security", "fallback_store_path"),
            "fallback_passphrase": ("security", "fallback_passphrase"),
        }
        for flat_key, (section, nested_key) in mapping.items():
            if flat_key in data:
                section_data = data.setdefault(section, {})
                if isinstance(section_data, dict) and nested_key not in section_data:
                    section_data[nested_key] = data.pop(flat_key)
        return data


def load_settings() -> ServerSettings:
    return ServerSettings()
