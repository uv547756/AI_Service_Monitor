# 🔍 LogWatch — Distributed Log Monitoring & AI Remediation

A production-grade system that monitors Linux server logs in real-time, uses AI to diagnose issues, sends alerts via Telegram with one-tap approve/reject, and executes fix commands — all visible in a sleek dark-mode dashboard.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Docker Deployment](#docker-deployment)
5. [Setting Up the Telegram Bot](#setting-up-the-telegram-bot)
6. [Configuring AI (OpenAI / Gemini)](#configuring-ai-openai--gemini)
7. [Adding a New Machine (Client Agent)](#adding-a-new-machine-client-agent)
8. [How Log Alerts Work](#how-log-alerts-work)
9. [Command Approval & Execution Flow](#command-approval--execution-flow)
10. [Using the Web Dashboard](#using-the-web-dashboard)
11. [API Reference](#api-reference)
12. [Security & Safety](#security--safety)
13. [Configuration Reference](#configuration-reference)
14. [Troubleshooting](#troubleshooting)
15. [Project Structure](#project-structure)

---

## Architecture Overview

```
┌─────────────────────┐         ┌────────────────────────────────────┐         ┌──────────────────────┐
│   Client Agent(s)   │         │         Central Server             │         │    Web Dashboard     │
│   (Linux hosts)     │────────▶│    FastAPI + AI + SQLite + Bot     │◀────────│   React + Tailwind   │
│                     │◀────────│                                    │         │                      │
│ • journalctl tail   │  HTTP   │  POST /agent/report   (logs in)   │  HTTP   │ • Dashboard overview │
│ • system metrics    │         │  POST /agent/result   (results)   │         │ • Machine list/detail│
│ • cmd executor      │         │  GET  /agent/pending  (cmds out)  │         │ • Log viewer         │
│                     │         │  GET  /machines,/logs,/issues,... │         │ • Issues & commands  │
└─────────────────────┘         └──────────┬─────────────────────────┘         └──────────────────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │   Telegram Bot    │
                                  │ ✅ Approve        │
                                  │ ❌ Reject         │
                                  │ 🔇 Ignore         │
                                  └──────────────────┘
```

**Flow:**
1. Client agent tails `journalctl` on a Linux host
2. Detects errors/warnings → sends log context + system metadata to the server
3. Server runs AI analysis (OpenAI or Gemini)
4. Telegram alert sent with diagnosis + suggested fix command
5. Admin taps **Approve** or **Reject** in Telegram
6. Client agent polls for approved commands, executes safely, reports result
7. Dashboard shows everything in real-time

---

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| **Server** | Python 3.12+, pip |
| **Frontend** | Node.js 18+ (20+ recommended), npm |
| **Client Agent** | Python 3.10+, Linux with `journalctl` |
| **Docker** (optional) | Docker 24+, Docker Compose v2 |
| **AI** | OpenAI API key **or** Google Gemini API key |
| **Telegram** (optional) | Telegram account + Bot Token |

---

## Quick Start (Local Development)

### Step 1: Clone and enter the project

```bash
cd /path/to/logwatch
```

### Step 2: Set up environment variables

```bash
cp .env.example backend/.env
```

Edit `backend/.env`:

```env
# Required — pick one AI provider
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
# OR
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-key-here

# Required for security
API_KEY=your-secret-api-key-here

# Optional — Telegram (see Telegram section below)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Database (default is fine for dev)
DATABASE_URL=sqlite+aiosqlite:///./logwatch.db
```

### Step 3: Start the backend server

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# Seed sample data (optional, for testing)
python -m app.seed

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server is now running at `http://localhost:8000`.

Test it:
```bash
curl -H "X-API-Key: your-secret-api-key-here" http://localhost:8000/health
# → {"status":"ok","service":"logwatch-server"}
```

### Step 4: Start the frontend dashboard

In a new terminal:

```bash
cd frontend
npm install

# Set API URL (for dev, the Vite proxy handles this automatically)
npm run dev
```

Open `http://localhost:5173` in your browser.

> **Note:** The Vite dev server proxies `/api/*` requests to `http://localhost:8000` automatically. If your backend runs on a different port, edit `vite.config.js`.

---

## Docker Deployment

For production or single-command setup:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 2. Build and launch
docker compose up -d --build

# 3. Seed sample data (optional)
docker compose exec backend python -m app.seed
```

| Service | URL |
|---------|-----|
| Dashboard | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |

To stop:
```bash
docker compose down
```

---

## Setting Up the Telegram Bot

### Step 1: Create a bot with BotFather

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "LogWatch Alerts")
4. Choose a username (e.g., `logwatch_alerts_bot`)
5. **Copy the bot token** — it looks like `7123456789:AAH...`

### Step 2: Get your Chat ID

**Option A — Personal alerts:**

1. Send any message to your new bot
2. Open this URL in a browser (replace YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Find `"chat":{"id":123456789}` — that number is your Chat ID

**Option B — Group alerts:**

1. Create a Telegram group
2. Add your bot to the group
3. Send a message in the group
4. Use the `getUpdates` URL above — the group chat ID is negative (e.g., `-1001234567890`)

### Step 3: Configure LogWatch

Add to your `.env`:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAHxxx...
TELEGRAM_CHAT_ID=123456789
```

Restart the backend server.

### Step 4: Set up the webhook (for button responses)

For the **Approve/Reject/Ignore** buttons to work, Telegram needs to send callbacks to your server:

```bash
# Replace with your bot token and your server's public URL
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-server.com/telegram/webhook"}'
```

> **For local development:** Use [ngrok](https://ngrok.com/) to expose your local server:
> ```bash
> ngrok http 8000
> # Then set webhook to: https://your-ngrok-url.ngrok.io/telegram/webhook
> ```

### What Telegram alerts look like

When an issue is detected, you'll receive:

```
🔴 LogWatch Alert

Machine: web-prod-01
Severity: CRITICAL
Summary: PostgreSQL connection pool exhausted

Suggested command:
sudo -u postgres psql -c 'SELECT pg_terminate_backend(pid) ...'

[✅ Approve]  [❌ Reject]  [🔇 Ignore]
```

- **Approve**: Command is queued for execution on the client machine
- **Reject**: Command is marked as rejected, no action taken
- **Ignore**: Alert is dismissed

After execution, you get a follow-up:

```
✅ Command Executed

Machine: web-prod-01
Command: sudo systemctl restart nginx
Exit code: 0

Output:
● nginx.service - A high performance web server
   Active: active (running)
```

---

## Configuring AI (OpenAI / Gemini)

### OpenAI (default)

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxx
OPENAI_MODEL=gpt-4o-mini        # default, cost-effective
# Or use: gpt-4o for better analysis (more expensive)
```

Get an API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

### Google Gemini

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash    # default, fast and free tier
# Or use: gemini-1.5-pro for better analysis
```

Get an API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### AI analysis output

The AI produces a structured diagnosis for every detected issue:

```json
{
  "severity": "critical",
  "confidence": 0.91,
  "summary": "PostgreSQL connection pool exhausted",
  "root_cause": "All available connections are in use. A connection leak...",
  "recommended_command": "sudo -u postgres psql -c '...'",
  "safe_to_auto_execute": false
}
```

---

## Adding a New Machine (Client Agent)

### Method 1: Direct installation (recommended)

On each Linux machine you want to monitor:

```bash
# 1. Copy the client-agent directory to the target machine
scp -r client-agent/ user@target-host:/opt/logwatch-agent/

# 2. SSH into the machine
ssh user@target-host

# 3. Install dependencies
cd /opt/logwatch-agent
pip3 install -r requirements.txt

# 4. Configure the agent
```

Edit `config.py`:

```python
class AgentConfig:
    SERVER_URL: str = "http://your-server-ip:8000"   # ← your central server
    API_KEY: str = "your-secret-api-key-here"         # ← must match server's API_KEY
    POLL_INTERVAL: int = 30      # how often to check for commands (seconds)
    LOG_CHECK_INTERVAL: int = 5  # how often to scan for new errors (seconds)
```

```bash
# 5. Start the agent
python3 agent.py
```

The agent will:
- Automatically register itself with the server (hostname-based)
- Begin monitoring `journalctl` immediately
- Appear in the dashboard within seconds

### Method 2: Systemd service (production)

Create `/etc/systemd/system/logwatch-agent.service`:

```ini
[Unit]
Description=LogWatch Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/logwatch-agent
ExecStart=/usr/bin/python3 /opt/logwatch-agent/agent.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable logwatch-agent
sudo systemctl start logwatch-agent

# Check status
sudo systemctl status logwatch-agent
journalctl -u logwatch-agent -f    # view agent logs
```

### Method 3: Docker

```bash
docker run -d \
  --name logwatch-agent \
  --restart unless-stopped \
  -e SERVER_URL=http://your-server-ip:8000 \
  -e API_KEY=your-secret-api-key \
  -v /var/log/journal:/var/log/journal:ro \
  logwatch-agent
```

### Verifying a new machine is connected

1. **Dashboard**: Go to the Machines page — the new host should appear
2. **API**: `curl -H "X-API-Key: ..." http://your-server:8000/machines`
3. **Logs**: The agent prints `LogWatch Agent starting on <hostname>` on startup

---

## How Log Alerts Work

### What gets detected

The agent monitors `journalctl -f` and flags lines matching these patterns:

| Severity | Patterns |
|----------|----------|
| **Error** | `error`, `failed`, `fatal`, `critical`, `exception`, `oom`, `killed`, `segfault`, `timeout`, `refused` |
| **Warning** | `warning`, `warn`, `deprecated`, `retry`, `slow` |

### What gets sent to the server

When a match is found, the agent sends:

- **Trigger log line**: The specific line that matched
- **Log context**: The surrounding ~200 lines for AI analysis
- **Service name**: Extracted from the journalctl line (e.g., `nginx`, `docker`)
- **System metadata**: hostname, OS, CPU, RAM, disk usage, uptime, IP address

### Debouncing

To avoid alert storms, the agent waits at least **10 seconds** between reports. You can adjust this in `agent.py`:

```python
self._min_report_interval = 10  # seconds
```

### Customizing monitored services

Edit `config.py` to adjust which services are monitored and what patterns trigger alerts:

```python
MONITORED_SERVICES = ["nginx", "docker", "sshd", "postgresql", "mysql", ...]
ERROR_PATTERNS = [r"error", r"failed", r"fatal", ...]
WARNING_PATTERNS = [r"warning", r"warn", ...]
```

---

## Command Approval & Execution Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ AI       │     │ Telegram │     │ Admin    │     │ Server   │     │ Agent    │
│ suggests │────▶│ alert    │────▶│ approves │────▶│ queues   │────▶│ executes │
│ command  │     │ sent     │     │ or       │     │ command  │     │ safely   │
│          │     │          │     │ rejects  │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └─────┬────┘
                                                                          │
                                                     Result sent back ◀───┘
                                                     Telegram notified
                                                     Dashboard updated
```

### Safety checks

Before any command is executed, it passes through multiple safety layers:

1. **Server-side blocklist**: Commands containing `rm -rf /`, `mkfs`, `dd if=`, or fork bombs are blocked
2. **Pattern check**: Additional dangerous patterns like `chmod 777`, `> /dev/sda`, `eval` are flagged
3. **Agent-side blocklist**: The client agent has its own blocklist as a second barrier
4. **Execution timeout**: Commands are killed after 120 seconds (configurable)
5. **Output capture**: stdout/stderr are captured and limited to 4KB

### Command statuses

| Status | Meaning |
|--------|---------|
| `pending` | AI suggested, awaiting Telegram approval |
| `approved` | Admin approved, waiting for agent to pick up |
| `rejected` | Admin rejected, no action taken |

### Execution statuses

| Status | Meaning |
|--------|---------|
| `pending` | Approved, not yet picked up by agent |
| `running` | Agent is executing |
| `success` | Completed with exit code 0 |
| `failed` | Completed with non-zero exit code |

---

## Using the Web Dashboard

### Dashboard (Home Page)

Overview with 4 stats cards:
- **Total Machines** — number of registered hosts
- **Active Issues** — open issues requiring attention
- **Critical Alerts** — high-priority issues
- **Pending Commands** — commands awaiting approval

Plus recent issues and machine status panels.

### Machines Page

Lists all monitored machines as cards showing:
- Hostname, OS, IP address
- Uptime and disk usage percentage
- Status indicator (🟢 healthy / 🟡 warning / 🔴 critical)
- Last seen timestamp

**Click a machine** → detailed view with system specs, recent logs, and issue counts.

### Log Viewer

Terminal-style log display with:
- **Color coding**: errors in red, warnings in yellow
- **Service filter**: filter by nginx, docker, sshd, etc.
- **Severity filter**: show only errors, warnings, or all
- **Line limit**: 50, 100, 200, or 500 lines
- Auto-refreshes every 5 seconds

### Issues & Alerts

Sortable table with:
- Severity badge (LOW / MEDIUM / HIGH / CRITICAL)
- Service name, summary, status, timestamp

**Click an issue** → detailed view with:
- Full AI analysis (summary + root cause)
- Confidence score bar
- Suggested command with approval status
- Execution results (if any)
- Full log context (100–200 lines)

### Commands Page

Track all commands through their lifecycle:
- Command text in monospace
- Approval status badge
- Who approved and when
- Execution output (green for success, red for errors)

### Real-time updates

The dashboard polls all endpoints every **5 seconds** automatically. No manual refresh needed.

---

## API Reference

All endpoints require the `X-API-Key` header (except `/health` and `/telegram/webhook`).

```bash
# Header for all requests
-H "X-API-Key: your-secret-api-key"
```

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

### Dashboard Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/machines` | List all machines |
| GET | `/machines/{id}` | Machine detail + recent logs + issue counts |
| GET | `/logs?service=nginx&severity=error&limit=100` | Query logs with filters |
| GET | `/issues?severity=critical&status=open&limit=50` | Query issues with filters |
| GET | `/issues/{id}` | Full issue detail (AI analysis + commands + executions) |
| GET | `/commands?approval_status=pending&limit=50` | Query commands with filters |

### Agent Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agent/report` | Agent sends detected error/warning |
| POST | `/agent/result` | Agent sends command execution result |
| GET | `/agent/pending/{machine_id}` | Agent polls for approved commands |

### Telegram Webhook

| Method | Path | Description |
|--------|------|-------------|
| POST | `/telegram/webhook` | Telegram callback handler |

---

## Security & Safety

### Authentication
- All API endpoints require the `X-API-Key` header
- Use a strong, unique API key in production (not the default `changeme-dev-key`)
- The same key is shared between server and all client agents

### Command blocklist

These patterns are **always blocked** from execution:

```
rm -rf /          — full filesystem deletion
mkfs              — disk formatting
dd if=            — raw disk writes
:(){ :|:& };:    — fork bomb
chmod 777         — overly permissive permissions
> /dev/sda        — raw device writes
eval              — arbitrary code execution
exec              — process replacement
```

Customize in `.env`:
```env
COMMAND_BLOCKLIST=rm -rf /,mkfs,dd if=,:(){ :|:& };:
```

### HTTPS

For production, place the server behind a reverse proxy (nginx/Caddy) with TLS:

```nginx
server {
    listen 443 ssl;
    server_name logwatch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/logwatch.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/logwatch.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;  # frontend
    }
    location /api/ {
        proxy_pass http://localhost:8000/;  # backend
    }
    location /telegram/ {
        proxy_pass http://localhost:8000/telegram/;
    }
}
```

---

## Configuration Reference

### Server (`.env`)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_KEY` | Shared auth key | `changeme-dev-key` | ✅ Change in prod |
| `AI_PROVIDER` | `openai` or `gemini` | `openai` | ✅ |
| `OPENAI_API_KEY` | OpenAI key | — | If using OpenAI |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` | No |
| `GEMINI_API_KEY` | Gemini key | — | If using Gemini |
| `GEMINI_MODEL` | Gemini model | `gemini-1.5-flash` | No |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — | For alerts |
| `TELEGRAM_CHAT_ID` | Alert destination | — | For alerts |
| `DATABASE_URL` | SQLAlchemy DB URL | `sqlite+aiosqlite:///./logwatch.db` | No |
| `COMMAND_BLOCKLIST` | Comma-separated blocked patterns | (see above) | No |
| `AUTO_EXECUTE_SAFE` | Auto-run safe commands | `false` | No |

### Client Agent (`config.py`)

| Setting | Description | Default |
|---------|-------------|---------|
| `SERVER_URL` | Central server URL | `http://localhost:8000` |
| `API_KEY` | Must match server's `API_KEY` | `changeme-dev-key` |
| `POLL_INTERVAL` | Command poll interval (seconds) | `30` |
| `LOG_CHECK_INTERVAL` | Log scan interval (seconds) | `5` |
| `COMMAND_TIMEOUT` | Max command runtime (seconds) | `120` |
| `MONITORED_SERVICES` | Services to watch | nginx, docker, sshd, ... |
| `ERROR_PATTERNS` | Regex patterns for errors | error, failed, fatal, ... |
| `WARNING_PATTERNS` | Regex patterns for warnings | warning, warn, ... |

---

## Troubleshooting

### "Invalid or missing API key" (403)

The `X-API-Key` header doesn't match. Ensure the same `API_KEY` value is set in:
- `backend/.env`
- `client-agent/config.py`
- `frontend/src/api/client.js` (or `VITE_API_KEY` env var)

### Agent not appearing in dashboard

1. Check the agent is running: `systemctl status logwatch-agent`
2. Check the agent can reach the server: `curl http://your-server:8000/health`
3. The agent only registers after its **first error report** — trigger a test error on the machine

### Telegram buttons not working

1. Ensure the webhook is set: `curl https://api.telegram.org/botTOKEN/getWebhookInfo`
2. The webhook URL must be **publicly accessible** (HTTPS required by Telegram)
3. Check server logs for Telegram callback errors

### AI analysis says "unavailable"

1. Check your API key is valid and has credits
2. Check the `AI_PROVIDER` matches the key you provided
3. View server logs: `docker compose logs backend` or check terminal output

### Frontend shows no data

1. Verify the backend is running: `curl http://localhost:8000/health`
2. Check browser DevTools → Network tab for failed requests
3. In dev mode, ensure the Vite proxy is configured in `vite.config.js`
4. Seed sample data: `python -m app.seed`

### Database reset

```bash
# Delete the SQLite database and re-seed
cd backend
rm logwatch.db
python -m app.seed
```

---

## Project Structure

```
logwatch/
├── backend/                     # FastAPI server
│   ├── app/
│   │   ├── main.py              # App entry, CORS, lifespan
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models.py            # ORM: machines, logs, issues, commands, executions
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── security.py          # API key auth + command blocklist
│   │   ├── seed.py              # Sample data seeder
│   │   ├── routers/
│   │   │   ├── machines.py      # GET /machines, /machines/{id}
│   │   │   ├── logs.py          # GET /logs (with filters)
│   │   │   ├── issues.py        # GET /issues, /issues/{id}
│   │   │   ├── commands.py      # GET /commands
│   │   │   ├── agent.py         # POST /agent/report, /agent/result
│   │   │   └── telegram.py      # Telegram webhook callback
│   │   └── services/
│   │       ├── ai_engine.py     # OpenAI + Gemini analysis
│   │       ├── telegram_bot.py  # Alert sending + callback handling
│   │       └── command_exec.py  # Command safety validation
│   ├── requirements.txt
│   └── Dockerfile
├── client-agent/                # Linux monitoring agent
│   ├── agent.py                 # Main orchestrator loop
│   ├── log_monitor.py           # journalctl follower + detection
│   ├── system_info.py           # CPU, RAM, disk, uptime collector
│   ├── api_client.py            # HTTP client with retry
│   ├── executor.py              # Safe command execution
│   ├── config.py                # Agent configuration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # React + TailwindCSS dashboard
│   ├── src/
│   │   ├── api/client.js        # Axios API client
│   │   ├── hooks/usePolling.js  # Auto-refresh hook (5s)
│   │   ├── components/          # Layout, StatusBadge, StatsCard, LogLine
│   │   └── pages/               # Dashboard, Machines, Logs, Issues, Commands
│   ├── vite.config.js           # Vite + Tailwind + API proxy
│   ├── nginx.conf               # Production nginx config
│   ├── Dockerfile               # Multi-stage build
│   └── package.json
├── docker-compose.yml           # All services
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## License

MIT
