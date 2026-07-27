from __future__ import annotations

# pyrefly: ignore [missing-import]
from pydantic import Field
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API auth
    api_key: str = Field(..., description="Shared secret between bot and agent")

    # Services to track — comma-separated short names matching podman-<name>.service
    tracked_services: list[str] = Field(
        default=["palworld", "valheim"],
        description="Short service names, e.g. 'palworld,valheim'",
    )

    # Network
    host: str = "0.0.0.0"
    port: int = 8420

    # Logging
    log_dir: str = "/var/log/servitor"


settings = Settings()
