from __future__ import annotations

# pyrefly: ignore [missing-import]
from pydantic import Field
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Discord
    discord_token: str = Field(..., description="Discord bot token")
    announcement_channel_id: int = Field(
        ..., description="Channel ID to post action announcements"
    )

    # Agent connection
    agent_url: str = Field(
        ..., description="Base URL of the servitor agent, e.g. http://192.168.1.100:8420"
    )
    agent_api_key: str = Field(..., description="Shared secret for agent API auth")

    # Wake-on-LAN
    wol_mac_address: str = Field(
        ..., description="MAC address of the main server, e.g. AA:BB:CC:DD:EE:FF"
    )
    wol_broadcast_address: str = Field(
        ..., description="Broadcast address of the LAN, e.g. 192.168.1.255"
    )

    # Permissions
    required_role_name: str = Field(
        ..., description="Name of the Discord role required to run management commands"
    )

    # Log shipping
    log_ship_interval_seconds: int = Field(
        default=3600, description="How often (seconds) to ship buffered logs to the agent"
    )

    # Status polling
    status_poll_interval_seconds: int = Field(
        default=30, description="How often (seconds) to poll the agent for server status"
    )

    # Optional: set to your Discord guild (server) ID for instant slash command sync.
    # Global sync (default when unset) can take up to 1 hour to propagate.
    guild_id: int | None = Field(
        default=None,
        description="Discord guild ID for guild-scoped slash command sync (instant). Leave unset for global sync.",
    )


settings = Settings()
