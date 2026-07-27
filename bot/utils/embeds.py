from __future__ import annotations

# pyrefly: ignore [missing-import]
import discord


# ── Colour palette ────────────────────────────────────────────────────────────
COLOUR_ONLINE = 0x57F287   # Discord green
COLOUR_DEGRADED = 0xFEE75C  # Discord yellow
COLOUR_OFFLINE = 0xED4245  # Discord red
COLOUR_INFO = 0x5865F2     # Discord blurple
COLOUR_ACTION = 0x7289DA   # Softer blurple for action confirmations

STATE_EMOJI = {
    "active": "🟢",
    "inactive": "🔴",
    "failed": "🔴",
    "activating": "🟡",
    "deactivating": "🟡",
    "unknown": "⚪",
}


def _state_emoji(active_state: str) -> str:
    return STATE_EMOJI.get(active_state, "⚪")


def server_status_embed(
    server_online: bool,
    services: list[dict] | None,
    system_info: dict | None,
) -> discord.Embed:
    """
    Top-level status embed shown by /status.
    Shows server availability, system uptime, and a row per game service.
    """
    if not server_online:
        embed = discord.Embed(
            title="🔴 Game Server — Offline",
            description="The server is unreachable or powered off.",
            colour=COLOUR_OFFLINE,
        )
        return embed

    all_running = services and all(s["active_state"] == "active" for s in services)
    colour = COLOUR_ONLINE if all_running else COLOUR_DEGRADED
    running_count = sum(1 for s in (services or []) if s["active_state"] == "active")
    total_count = len(services) if services else 0

    embed = discord.Embed(
        title="🟢 Game Server — Online",
        colour=colour,
    )

    # System uptime
    if system_info:
        uptime_s = system_info.get("uptime_seconds", 0)
        h, rem = divmod(uptime_s, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s"
        load = system_info.get("load_avg", {})
        disk = system_info.get("disk", {})
        embed.add_field(
            name="System",
            value=(
                f"**Uptime:** {uptime_str}\n"
                f"**Load:** {load.get('1m', '?')} / {load.get('5m', '?')} / {load.get('15m', '?')}\n"
                f"**Disk:** {disk.get('used_gb', '?')} GB / {disk.get('total_gb', '?')} GB"
            ),
            inline=False,
        )

    # Per-service rows
    if services:
        rows = []
        for svc in services:
            emoji = _state_emoji(svc["active_state"])
            rows.append(f"{emoji} **{svc['name'].capitalize()}** — {svc['sub_state']}")
        embed.add_field(
            name=f"Game Services ({running_count}/{total_count} running)",
            value="\n".join(rows),
            inline=False,
        )
    else:
        embed.add_field(name="Game Services", value="No services tracked.", inline=False)

    return embed


def container_detail_embed(service_data: dict) -> discord.Embed:
    """
    Detailed embed for /inspect <service>.
    Shows systemd state, container image, ports, and live resource usage.
    """
    name = service_data.get("name", "unknown").capitalize()
    active_state = service_data.get("active_state", "unknown")
    sub_state = service_data.get("sub_state", "unknown")
    start_ts = service_data.get("start_timestamp", "")
    container = service_data.get("container") or {}
    stats = service_data.get("stats")

    emoji = _state_emoji(active_state)
    colour = COLOUR_ONLINE if active_state == "active" else COLOUR_OFFLINE

    embed = discord.Embed(
        title=f"{emoji} {name}",
        colour=colour,
    )

    embed.add_field(
        name="systemd",
        value=(
            f"**State:** {active_state} ({sub_state})\n"
            f"**Unit:** `{service_data.get('unit', '?')}`\n"
            f"**Started:** {start_ts or 'N/A'}"
        ),
        inline=False,
    )

    image = container.get("image") or "N/A"
    ports = container.get("ports") or []
    embed.add_field(
        name="Container",
        value=(
            f"**Image:** `{image}`\n"
            f"**Ports:** {', '.join(ports) if ports else 'None'}"
        ),
        inline=False,
    )

    if stats:
        embed.add_field(
            name="Resources",
            value=(
                f"**CPU:** {stats.get('cpu_percent', 'N/A')}\n"
                f"**Memory:** {stats.get('mem_usage', 'N/A')} / {stats.get('mem_limit', 'N/A')} "
                f"({stats.get('mem_percent', 'N/A')})"
            ),
            inline=False,
        )

    return embed


def action_result_embed(
    action: str,
    target: str,
    user: discord.Member,
    success: bool,
    detail: str = "",
) -> discord.Embed:
    """Compact embed for action confirmations (sent ephemerally to the user)."""
    if success:
        embed = discord.Embed(
            title=f"✅ {action.capitalize()} — {target.capitalize()}",
            description=detail or f"{action.capitalize()} succeeded.",
            colour=COLOUR_ACTION,
        )
    else:
        embed = discord.Embed(
            title=f"❌ {action.capitalize()} failed — {target.capitalize()}",
            description=detail or "Something went wrong. Check the agent logs.",
            colour=COLOUR_OFFLINE,
        )
    embed.set_footer(text=f"Requested by {user.display_name}")
    return embed


def announcement_embed(
    action: str,
    target: str,
    user: discord.Member,
) -> discord.Embed:
    """
    Public announcement embed posted to the announcement channel.
    e.g. "@user restarted Palworld"
    """
    action_labels = {
        "restart": "🔧 restarted",
        "stop": "🛑 stopped",
        "start": "▶️ started",
        "wake": "⚡ woke up the server",
        "restart-server": "🔄 rebooted the server",
        "sleep-server": "💤 put the server to sleep",
    }
    verb = action_labels.get(action, action)
    target_str = f"**{target.capitalize()}**" if target else ""

    embed = discord.Embed(
        description=f"{user.mention} {verb} {target_str}".strip(),
        colour=COLOUR_INFO,
    )
    return embed
