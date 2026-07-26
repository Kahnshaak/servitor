from __future__ import annotations

import subprocess
import time

import psutil


def get_system_info() -> dict:
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)

    load1, load5, load15 = psutil.getloadavg()

    disk = psutil.disk_usage("/")

    return {
        "uptime_seconds": uptime_seconds,
        "load_avg": {
            "1m": round(load1, 2),
            "5m": round(load5, 2),
            "15m": round(load15, 2),
        },
        "disk": {
            "total_gb": round(disk.total / 1e9, 1),
            "used_gb": round(disk.used / 1e9, 1),
            "free_gb": round(disk.free / 1e9, 1),
            "percent": disk.percent,
        },
    }


def _run_power_command(args: list[str]) -> tuple[bool, str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        return True, "Command dispatched"
    return False, result.stderr.strip() or "Command failed"


def reboot() -> tuple[bool, str]:
    return _run_power_command(["systemctl", "reboot"])


def sleep() -> tuple[bool, str]:
    return _run_power_command(["systemctl", "suspend"])
