from __future__ import annotations

# pyrefly: ignore [missing-import]
import discord
# pyrefly: ignore [missing-import]
from discord import app_commands
# pyrefly: ignore [missing-import]
from discord.ext import commands

from config import settings
from services.agent_client import agent
from services.audit import AuditLogger
from utils.embeds import action_result_embed, announcement_embed
from utils.permissions import requires_role


class ContainersCog(commands.Cog):
    """
    /restart, /stop, /start commands for individual game services.
    """

    def __init__(self, bot: commands.Bot, audit: AuditLogger) -> None:
        self.bot = bot
        self.audit = audit

    # ── Shared helpers ────────────────────────────────────────────────────────

    async def _get_announcement_channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.announcement_channel_id)

    async def _do_action(
        self,
        interaction: discord.Interaction,
        service: str,
        action: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        action_fns = {
            "restart": agent.restart_service,
            "stop": agent.stop_service,
            "start": agent.start_service,
        }
        result = await action_fns[action](service)
        success = result is not None and result.get("success", False)
        detail = result.get("message", "") if result else "Agent unreachable."

        # Ephemeral confirmation to the user
        embed = action_result_embed(action, service, interaction.user, success, detail)
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Public announcement
        if success:
            channel = await self._get_announcement_channel()
            if channel:
                ann = announcement_embed(action, service, interaction.user)
                await channel.send(embed=ann)

        # Audit log
        self.audit.record(
            discord_user=str(interaction.user),
            discord_user_id=interaction.user.id,
            command=action,
            args={"service": service},
            result="success" if success else f"failed: {detail}",
        )

    # ── Autocomplete helper (reads from status cog's cached list) ─────────────

    async def _service_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        status_cog = self.bot.cogs.get("StatusCog")
        services = getattr(status_cog, "_last_services", None) or []
        return [
            app_commands.Choice(name=s["name"].capitalize(), value=s["name"])
            for s in services
            if current.lower() in s["name"].lower()
        ]

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="restart", description="Restart a game service.")
    @app_commands.describe(service="The game service to restart")
    @requires_role()
    async def restart(self, interaction: discord.Interaction, service: str) -> None:
        await self._do_action(interaction, service, "restart")

    @restart.autocomplete("service")
    async def restart_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await self._service_autocomplete(interaction, current)

    @app_commands.command(name="stop", description="Stop a game service.")
    @app_commands.describe(service="The game service to stop")
    @requires_role()
    async def stop(self, interaction: discord.Interaction, service: str) -> None:
        await self._do_action(interaction, service, "stop")

    @stop.autocomplete("service")
    async def stop_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await self._service_autocomplete(interaction, current)

    @app_commands.command(name="start", description="Start a game service.")
    @app_commands.describe(service="The game service to start")
    @requires_role()
    async def start(self, interaction: discord.Interaction, service: str) -> None:
        await self._do_action(interaction, service, "start")

    @start.autocomplete("service")
    async def start_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await self._service_autocomplete(interaction, current)


async def setup(bot: commands.Bot, audit: AuditLogger) -> None:
    await bot.add_cog(ContainersCog(bot, audit))
