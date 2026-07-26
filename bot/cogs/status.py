from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import settings
from services.agent_client import agent
from utils.embeds import server_status_embed, container_detail_embed


class StatusCog(commands.Cog):
    """
    Background presence loop + /status and /inspect commands.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._last_services: list[dict] | None = None
        self._server_online: bool = False
        self.presence_loop.start()

    def cog_unload(self) -> None:
        self.presence_loop.cancel()

    # ── Background task ───────────────────────────────────────────────────────

    @tasks.loop(seconds=settings.status_poll_interval_seconds)
    async def presence_loop(self) -> None:
        online = await agent.health()
        services: list[dict] | None = None

        if online:
            services = await agent.list_services()

        self._server_online = online
        self._last_services = services

        await self._update_presence(online, services)

    @presence_loop.before_loop
    async def before_presence_loop(self) -> None:
        await self.bot.wait_until_ready()

    async def _update_presence(
        self, online: bool, services: list[dict] | None
    ) -> None:
        if not online:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="Server Offline 🔴",
            )
            status = discord.Status.do_not_disturb
        else:
            running = sum(1 for s in (services or []) if s["active_state"] == "active")
            total = len(services) if services else 0
            all_up = running == total and total > 0
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{running}/{total} servers online {'🟢' if all_up else '🟡'}",
            )
            status = discord.Status.online if all_up else discord.Status.idle

        await self.bot.change_presence(activity=activity, status=status)

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="status", description="Show the game server and service status.")
    async def status(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        online = await agent.health()
        services = await agent.list_services() if online else None
        system_info = await agent.system_info() if online else None

        embed = server_status_embed(online, services, system_info)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="inspect",
        description="Show detailed info for a specific game service.",
    )
    @app_commands.describe(service="The game service to inspect (e.g. palworld, valheim)")
    async def inspect(self, interaction: discord.Interaction, service: str) -> None:
        await interaction.response.defer()

        data = await agent.get_service(service)
        if data is None:
            await interaction.followup.send(
                f"❌ Could not retrieve info for **{service}**. "
                "The server may be offline or the service name is incorrect.",
                ephemeral=True,
            )
            return

        embed = container_detail_embed(data)
        await interaction.followup.send(embed=embed)

    @inspect.autocomplete("service")
    async def inspect_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        services = self._last_services or []
        return [
            app_commands.Choice(name=s["name"].capitalize(), value=s["name"])
            for s in services
            if current.lower() in s["name"].lower()
        ]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatusCog(bot))
