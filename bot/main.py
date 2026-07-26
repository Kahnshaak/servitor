from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from config import settings
from services.agent_client import agent
from services.audit import AuditLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("servitor.bot")


class ServitorBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.audit = AuditLogger(agent, settings.log_ship_interval_seconds)

    async def setup_hook(self) -> None:
        # Load cogs — containers and server cogs receive the audit logger
        await self.load_extension("cogs.status")

        # Cogs that need the audit logger are loaded manually
        from cogs.containers import setup as containers_setup
        from cogs.server import setup as server_setup

        await containers_setup(self, self.audit)
        await server_setup(self, self.audit)

        # Start the audit log shipping loop
        self.loop.create_task(self.audit.shipping_loop())

        # Sync slash commands globally (only needed on first run or after command changes)
        await self.tree.sync()
        log.info("Slash commands synced.")

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user} ({self.user.id})")


def main() -> None:
    bot = ServitorBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
