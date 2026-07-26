from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class ContainerDetails:
    name: str
    image: str
    status: str
    created: str
    ports: list[str] = field(default_factory=list)


@dataclass
class ContainerStats:
    cpu_percent: str
    mem_usage: str
    mem_limit: str
    mem_percent: str


def _container_name(short_name: str) -> str:
    """Podman container names typically match the short service name."""
    return short_name


def get_container_details(short_name: str) -> ContainerDetails | None:
    """Return container inspect data for a given short service name."""
    name = _container_name(short_name)
    result = subprocess.run(
        ["podman", "inspect", "--format", "json", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)
        if not data:
            return None
        c = data[0]

        # Parse port bindings into human-readable strings
        ports: list[str] = []
        port_bindings = c.get("HostConfig", {}).get("PortBindings", {})
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for hb in host_bindings:
                    ports.append(f"{hb.get('HostPort', '?')} -> {container_port}")

        return ContainerDetails(
            name=name,
            image=c.get("Image", "unknown"),
            status=c.get("State", {}).get("Status", "unknown"),
            created=c.get("Created", ""),
            ports=ports,
        )
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def get_container_stats(short_name: str) -> ContainerStats | None:
    """Return live CPU/memory stats for a container (non-streaming)."""
    name = _container_name(short_name)
    result = subprocess.run(
        ["podman", "stats", "--no-stream", "--format", "json", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)
        if not data:
            return None
        s = data[0]
        return ContainerStats(
            cpu_percent=s.get("CPU", "0%"),
            mem_usage=s.get("MemUsage", "0B"),
            mem_limit=s.get("MemLimit", "0B"),
            mem_percent=s.get("MemPerc", "0%"),
        )
    except (json.JSONDecodeError, KeyError, IndexError):
        return None
