from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.agent_client import AgentClient


@dataclass
class AuditEntry:
    timestamp: str
    discord_user: str
    discord_user_id: int
    command: str
    args: dict
    result: str


class AuditLogger:
    """
    Buffers command audit entries in memory and ships them to the agent
    on a configurable interval (default: hourly).

    If the agent is unreachable, entries are held in the buffer until the
    next successful ship attempt.
    """

    def __init__(self, agent: "AgentClient", ship_interval: int = 3600) -> None:
        self._agent = agent
        self._ship_interval = ship_interval
        self._buffer: list[dict] = []
        self._lock = asyncio.Lock()

    def record(
        self,
        discord_user: str,
        discord_user_id: int,
        command: str,
        args: dict,
        result: str,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_user": discord_user,
            "discord_user_id": discord_user_id,
            "command": command,
            "args": args,
            "result": result,
        }
        # Non-async, safe to call from sync contexts
        self._buffer.append(entry)

    async def _ship(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            # Take a snapshot and clear the buffer optimistically
            to_send = list(self._buffer)
            self._buffer.clear()

        success = await self._agent.ship_logs(to_send)
        if not success:
            # Return entries to the buffer if the agent was unreachable
            async with self._lock:
                self._buffer = to_send + self._buffer

    async def shipping_loop(self) -> None:
        """Long-running coroutine; add to the bot's background tasks."""
        while True:
            await asyncio.sleep(self._ship_interval)
            await self._ship()
