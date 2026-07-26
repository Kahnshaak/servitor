from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ServiceStatus:
    name: str
    unit: str
    active_state: str      # active | inactive | failed | activating | deactivating
    sub_state: str         # running | dead | failed | start | stop-sigterm …
    start_timestamp: str   # ISO-ish timestamp from systemd, empty if not started


def _unit_name(short_name: str) -> str:
    return f"podman-{short_name}.service"


def _systemctl_show(unit: str) -> dict[str, str]:
    """Run `systemctl show` and parse key=value output into a dict."""
    result = subprocess.run(
        [
            "systemctl",
            "show",
            unit,
            "--property=ActiveState,SubState,ExecMainStartTimestamp",
            "--no-pager",
        ],
        capture_output=True,
        text=True,
    )
    props: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
    return props


def list_services(tracked_names: list[str]) -> list[ServiceStatus]:
    statuses = []
    for name in tracked_names:
        unit = _unit_name(name)
        props = _systemctl_show(unit)
        statuses.append(
            ServiceStatus(
                name=name,
                unit=unit,
                active_state=props.get("ActiveState", "unknown"),
                sub_state=props.get("SubState", "unknown"),
                start_timestamp=props.get("ExecMainStartTimestamp", ""),
            )
        )
    return statuses


def get_service_status(short_name: str) -> ServiceStatus:
    unit = _unit_name(short_name)
    props = _systemctl_show(unit)
    return ServiceStatus(
        name=short_name,
        unit=unit,
        active_state=props.get("ActiveState", "unknown"),
        sub_state=props.get("SubState", "unknown"),
        start_timestamp=props.get("ExecMainStartTimestamp", ""),
    )


def _systemctl_action(action: str, short_name: str) -> tuple[bool, str]:
    """Run a systemctl action (start/stop/restart) on a service. Returns (success, message)."""
    unit = _unit_name(short_name)
    result = subprocess.run(
        ["systemctl", action, unit],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, f"{action} succeeded for {unit}"
    return False, result.stderr.strip() or f"{action} failed for {unit}"


def restart_service(short_name: str) -> tuple[bool, str]:
    return _systemctl_action("restart", short_name)


def stop_service(short_name: str) -> tuple[bool, str]:
    return _systemctl_action("stop", short_name)


def start_service(short_name: str) -> tuple[bool, str]:
    return _systemctl_action("start", short_name)
