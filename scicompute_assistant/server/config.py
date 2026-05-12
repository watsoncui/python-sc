"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCICOMP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Mode: "server" (default) or "desktop" (used by Tauri sidecar).
    mode: str = "server"

    # LLM
    server_api_key: str = ""
    server_base_url: str = "https://api.openai.com/v1"
    server_default_model: str = "gpt-4o-mini"
    server_rpm_limit: int = 60
    server_burst: int = 10

    # Local provider defaults (only meaningful when mode == "desktop")
    local_default_endpoint: str = "deepseek"
    local_default_model: str = "deepseek-chat"

    # Sandbox / compute
    sandbox_timeout_sec: float = 5.0
    sandbox_restricted: bool = True

    # Knowledge corpus root
    courseware_root: Path = Field(
        default=Path(__file__).resolve().parents[1] / "assets" / "courseware"
    )

    # Encrypted-file fallback (desktop mode w/o Tauri bridge)
    fallback_store_path: Path = Field(
        default=Path.home() / ".scicompute" / "keys.enc.json"
    )
    fallback_passphrase: str = ""

    # CORS
    cors_origins: list[str] = ["*"]

    # Disable outbound LLM calls (used by CI / smoke tests)
    disable_outbound_llm: bool = False

    # HTTP rate limit (per-IP, per minute)
    http_rpm_limit: int = 60

    # Observability
    json_logs: bool = False
    slack_webhook_url: str = ""
    pagerduty_routing_key: str = ""


def load_settings() -> ServerSettings:
    return ServerSettings()
