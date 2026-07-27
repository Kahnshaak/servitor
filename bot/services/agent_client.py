from __future__ import annotations

from typing import Any

# pyrefly: ignore [missing-import]
import aiohttp

from config import settings


class AgentClient:
    """Async HTTP client for the Servitor Agent API."""

    def __init__(self) -> None:
        self._base = settings.agent_url.rstrip("/")
        self._headers = {"X-API-Key": settings.agent_api_key}

    async def _get(self, path: str) -> Any | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base}{path}",
                    headers=self._headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except Exception:
            return None

    async def _post(self, path: str, payload: Any = None) -> Any | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._base}{path}",
                    headers=self._headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
        except Exception:
            return None

    async def health(self) -> bool:
        result = await self._get("/health")
        return result is not None

    async def list_services(self) -> list[dict] | None:
        return await self._get("/services")

    async def get_service(self, name: str) -> dict | None:
        return await self._get(f"/services/{name}")

    async def restart_service(self, name: str) -> dict | None:
        return await self._post(f"/services/{name}/restart")

    async def stop_service(self, name: str) -> dict | None:
        return await self._post(f"/services/{name}/stop")

    async def start_service(self, name: str) -> dict | None:
        return await self._post(f"/services/{name}/start")

    async def system_info(self) -> dict | None:
        return await self._get("/system/info")

    async def reboot_server(self) -> dict | None:
        return await self._post("/system/reboot")

    async def sleep_server(self) -> dict | None:
        return await self._post("/system/sleep")

    async def ship_logs(self, entries: list[dict]) -> bool:
        result = await self._post("/logs/ingest", entries)
        return result is not None


# Singleton used by cogs
agent = AgentClient()
