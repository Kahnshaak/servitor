from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.agent_client import agent
from services.audit import AuditLogger
from services.wol import send_wol
from utils.embeds import action_result_embed, announcement_embed
from utils.permissions import requires_role

_WAKE_POLL_INTERVAL = 5    # seconds between health checks while waiting for boot
_WAKE_TIMEOUT = 120        # seconds to wait for server to respond after WoL


class ServerCog(commands.Cog):
    """
    /wake, /restart-server, /sleep-server — whole-server power commands.
    """

    def __init__(self, bot: commands.Bot, audit: AuditLogger) -> None:
        self.bot = bot
        self.audit = audit

    async def _get_announcement_channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.announcement_channel_id)

    async def _announce(self, action: str, user: discord.Member) -> None:
        channel = await self._get_announcement_channel()
        if channel:
            ann = announcement_embed(action, "", user)
            await channel.send(embed=ann)

    # ── /wake ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="wake", description="Wake the game server via Wake-on-LAN.")
    @requires_role()
    async def wake(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            send_wol(settings.wol_mac_address, settings.wol_broadcast_address)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to send WoL packet: {e}", ephemeral=True
            )
            return

        await interaction.followup.send(
            "⚡ WoL packet sent! Waiting for the server to come online…",
            ephemeral=True,
        )

        # Poll until the agent responds or we time out
        elapsed = 0
        online = False
        while elapsed < _WAKE_TIMEOUT:
            await asyncio.sleep(_WAKE_POLL_INTERVAL)
            elapsed += _WAKE_POLL_INTERVAL
            if await agent.health():
                online = True
                break

        if online:
            await interaction.followup.send(
                f"✅ Server is online! (took ~{elapsed}s)", ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"⏱️ Server didn't respond within {_WAKE_TIMEOUT}s. "
                "It may still be booting — try `/status` in a moment.",
                ephemeral=True,
            )

        await self._announce("wake", interaction.user)
        self.audit.record(
            discord_user=str(interaction.user),
            discord_user_id=interaction.user.id,
            command="wake",
            args={},
            result="online" if online else "timeout",
        )

    # ── /restart-server ───────────────────────────────────────────────────────

    @app_commands.command(name="restart-server", description="Reboot the entire game server.")
    @requires_role()
    async def restart_server(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        result = await agent.reboot_server()
        success = result is not None and result.get("success", False)
        detail = result.get("message", "") if result else "Agent unreachable."

        embed = action_result_embed("restart-server", "server", interaction.user, success, detail)
        await interaction.followup.send(embed=embed, ephemeral=True)

        if success:
            await self._announce("restart-server", interaction.user)

        self.audit.record(
            discord_user=str(interaction.user),
            discord_user_id=interaction.user.id,
            command="restart-server",
            args={},
            result="success" if success else f"failed: {detail}",
        )

    # ── /sleep-server ─────────────────────────────────────────────────────────

    @app_commands.command(
        name="sleep-server",
        description="Suspend the game server. Use /wake to bring it back.",
    )
    @requires_role()
    async def sleep_server(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        result = await agent.sleep_server()
        success = result is not None and result.get("success", False)
        detail = result.get("message", "") if result else "Agent unreachable."

        embed = action_result_embed("sleep-server", "server", interaction.user, success, detail)
        await interaction.followup.send(embed=embed, ephemeral=True)

        if success:
            await self._announce("sleep-server", interaction.user)

        self.audit.record(
            discord_user=str(interaction.user),
            discord_user_id=interaction.user.id,
            command="sleep-server",
            args={},
            result="success" if success else f"failed: {detail}",
        )


async def setup(bot: commands.Bot, audit: AuditLogger) -> None:
    await bot.add_cog(ServerCog(bot, audit))
