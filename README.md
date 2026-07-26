# Servitor

A two-component Discord bot system for monitoring and managing a NixOS homelab game server.

```
┌──────────────┐    HTTP (LAN)     ┌──────────────────────────────┐
│  Servitor    │ ───────────────►  │  Servitor Agent (FastAPI)    │
│  Bot         │                   │  Main Server — NixOS         │
│  (discord.py)│ ◄─────────────── │  systemctl + podman          │
│  Raspberry Pi│    WoL (UDP)      │  podman-palworld.service     │
└──────────────┘                   │  podman-valheim.service      │
       │                           └──────────────────────────────┘
       │ log ship (hourly)
       └──────────────────────────► /var/log/servitor/audit.log
```

## Components

| Component | Location | Purpose |
|---|---|---|
| **Bot** | `bot/` | Discord slash commands, presence, WoL |
| **Agent** | `agent/` | REST API wrapping systemd/podman on the game server |

---

## Bot Commands

| Command | Permission | Description |
|---|---|---|
| `/status` | Everyone | Server status + all game service states |
| `/inspect <service>` | Everyone | Detailed info: systemd state, image, ports, CPU/mem |
| `/wake` | Role | Send WoL packet and wait for server to come online |
| `/restart <service>` | Role | Restart a game service |
| `/stop <service>` | Role | Stop a game service |
| `/start <service>` | Role | Start a game service |
| `/restart-server` | Role | Reboot the entire server |
| `/sleep-server` | Role | Suspend the server (use `/wake` to bring it back) |

Management commands post a public announcement in the configured channel and log to the audit file.

---

## Setup

### Prerequisites

- Python 3.12+
- Docker (for containerised deployment)
- The agent's service user needs passwordless sudo for specific commands (see below)

### 1. Configure secrets

```bash
cp .env.example .env
# Edit .env with your values
```

### 2. Agent — sudoers

The agent runs as a system user that needs to control systemd services and run podman. Add a sudoers rule:

```
# /etc/sudoers.d/servitor-agent
servitor ALL=(ALL) NOPASSWD: \
  /usr/bin/systemctl start podman-*.service, \
  /usr/bin/systemctl stop podman-*.service, \
  /usr/bin/systemctl restart podman-*.service, \
  /usr/bin/systemctl reboot, \
  /usr/bin/systemctl suspend
```

Then update `agent/services/systemd_service.py` to prefix commands with `sudo` if running as an unprivileged user, or run the agent as a user with the above polkit/sudo policy.

### 3. Development (both on one machine)

```bash
docker compose -f docker-compose.dev.yml up --build
```

### 4. Production deployment

#### Agent (main server)

```bash
cd agent
docker build -t servitor-agent .
docker run -d \
  --name servitor-agent \
  --restart unless-stopped \
  --env-file /path/to/agent.env \
  -p 8420:8420 \
  -v /var/log/servitor:/var/log/servitor \
  servitor-agent
```

#### Bot (Raspberry Pi)

Build on the main server and push to the Pi:

```bash
# On the main server
cd bot
docker buildx build --platform linux/arm64 -t servitor-bot --output type=docker,dest=servitor-bot.tar .
scp servitor-bot.tar pi@<pi-ip>:~/

# On the Pi
docker load < ~/servitor-bot.tar
docker run -d \
  --name servitor-bot \
  --restart unless-stopped \
  --env-file /path/to/bot.env \
  servitor-bot
```

---

## Adding New Game Servers

1. Create the systemd service following the same pattern: `podman-<name>.service`
2. Add the short name to `TRACKED_SERVICES` in the agent's env (comma-separated)
3. Restart the agent — no code changes needed

---

## Configuration Reference

### Bot (`bot/.env`)

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Discord bot token |
| `ANNOUNCEMENT_CHANNEL_ID` | ✅ | Channel ID for public action announcements |
| `AGENT_URL` | ✅ | LAN URL of the agent, e.g. `http://192.168.1.100:8420` |
| `AGENT_API_KEY` | ✅ | Shared secret — must match agent's `API_KEY` |
| `WOL_MAC_ADDRESS` | ✅ | MAC address of the main server |
| `WOL_BROADCAST_ADDRESS` | ✅ | LAN broadcast address, e.g. `192.168.1.255` |
| `REQUIRED_ROLE_NAME` | ✅ | Discord role name required for management commands |
| `LOG_SHIP_INTERVAL_SECONDS` | — | Audit log ship frequency in seconds (default: `3600`) |
| `STATUS_POLL_INTERVAL_SECONDS` | — | Presence poll frequency in seconds (default: `30`) |

### Agent (`agent/.env`)

| Variable | Required | Description |
|---|---|---|
| `API_KEY` | ✅ | Shared secret — must match bot's `AGENT_API_KEY` |
| `TRACKED_SERVICES` | ✅ | Comma-separated short service names, e.g. `palworld,valheim` |
| `LOG_DIR` | — | Where to write audit logs (default: `/var/log/servitor`) |
| `HOST` | — | Bind address (default: `0.0.0.0`) |
| `PORT` | — | Listen port (default: `8420`) |

---

## Audit Logs

Bot audit entries are buffered in memory and shipped hourly to the agent, which writes them to `$LOG_DIR/audit.log` as rotating JSON lines:

```json
{"timestamp": "2026-07-26T22:00:00+00:00", "discord_user": "kahnshaak#0001", "discord_user_id": 123456789, "command": "restart", "args": {"service": "palworld"}, "result": "success", "received_at": "2026-07-26T22:00:05+00:00"}
```

Logs rotate at 10 MB with 5 backups kept (~50 MB max).
