import asyncio
import logging

# pyrefly: ignore [missing-import]
import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands

from config import settings
from services.agent_client import agent
from services.audit import AuditLogger

# Logs go to stdout only — the Pi has no persistent storage.
# Docker captures stdout via `docker logs`.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("servitor.bot")


class ServitorBot(commands.Bot):
    def __init__(self) -> None:
        # Minimal intents — slash commands only need guild access.
        # No privileged intents (message_content, members, presences) required.
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        # Audit entries are buffered purely in memory — no disk writes on the Pi.
        # Entries are shipped to the agent hourly. A crash before the next ship
        # will lose that window of entries; this is an acceptable tradeoff for
        # running on diskless hardware.
        self.audit = AuditLogger(agent, settings.log_ship_interval_seconds)

    async def setup_hook(self) -> None:
        # Load the status cog via extension (no extra dependencies)
        await self.load_extension("cogs.status")

        # Cogs that need the audit logger are loaded manually so it can be injected
        from cogs.containers import setup as containers_setup
        from cogs.server import setup as server_setup

        await containers_setup(self, self.audit)
        await server_setup(self, self.audit)

        # Start the hourly audit log shipping loop
        self.loop.create_task(self.audit.shipping_loop())

        # Sync slash commands. Guild-scoped sync is instant; global takes up to 1 hour.
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info(f"Slash commands synced to guild {settings.guild_id}.")
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally (may take up to 1 hour to propagate).")

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user} ({self.user.id})")


def main() -> None:
    bot = ServitorBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
