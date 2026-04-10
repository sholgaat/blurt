# idea-inbox
A tool to capture ideas from chat, use a configured LLM provider to clean them up, and create GitHub issues automatically.

## Quickstart (60 Seconds)

```bash
# 1) Run the interactive setup script
./scripts/setup.sh

# 2) Start
docker compose up -d --build

# 3) Watch logs
docker compose logs -f backend
docker compose logs -f bot
```

The setup script copies the example env files, prompts for every required value with a short explanation, and writes them in place. It defaults `DRY_RUN=true` so no real GitHub issues are created on the first run.

In Docker Compose, the backend is internal-only (`http://backend:8000`) and not exposed to the host. See the comment in `docker-compose.yml` for details.

## Setup

### Prerequisites
- Docker + Docker Compose
- Python 3.12 or higher (only needed for direct/manual runs and local tests)

### 1. Create service env files

Either run the interactive script (recommended):

```bash
./scripts/setup.sh
```

Or copy the templates manually and fill them in:

```bash
cp .env.backend.example .env.backend
cp .env.bot.example .env.bot
```

### 2. Configure backend secrets (`.env.backend`)

```bash
# Required for backend GitHub integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=your_repository_name

# Required for backend LLM features
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=llama3.2
MODEL_TIMEOUT_SECONDS=30

# Optional: Set to "false" once you have verified your setup works
DRY_RUN=true
```

### 3. Configure bot runtime (`.env.bot`)

```bash
BOT_PROVIDER=telegram

# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_ALLOWED_USER_IDS=123456789
DISCORD_IDEA_CHANNEL_ID=

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_USER_IDS=123456789

BACKEND_URL=http://backend:8000
```

## Configuration Reference

### Backend (`.env.backend`)

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | No | LLM provider to use for structuring ideas (`gemini`, `openai`, `anthropic`, `ollama`). Defaults to `gemini`. |
| `GEMINI_API_KEY` | Yes (Gemini) | API key for Google Gemini, used to structure ideas into title/summary/tags. Get one at [Google AI Studio](https://aistudio.google.com/). |
| `OPENAI_API_KEY` | Yes (OpenAI) | API key for OpenAI, used to structure ideas into title/summary/tags. |
| `ANTHROPIC_API_KEY` | Yes (Anthropic) | API key for Anthropic, used to structure ideas into title/summary/tags. |
| `OLLAMA_API_BASE` | No | Base URL for the Ollama API (default `http://localhost:11434`). |
| `OLLAMA_MODEL` | No | Ollama model name to use (default `llama3.2`). |
| `MODEL_TIMEOUT_SECONDS` | No | Global model timeout in seconds (default `30`). |
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token used to create issues. Classic token needs `repo` scope. Fine-grained token needs Issues (read/write) and Labels (read/write) on the target repo. |
| `GITHUB_REPO_OWNER` | Yes | GitHub username or organisation that owns the target repository. |
| `GITHUB_REPO_NAME` | Yes | Repository name where ideas will be filed as issues. |
| `DRY_RUN` | No | Set to `true` (default) to skip real issue creation. Set to `false` when ready for production. |

### Bot runtime (`.env.bot`)

| Variable | Required | Description |
|---|---|---|
| `BOT_PROVIDER` | Yes | Which bot to run: `telegram` or `discord`. |
| `BACKEND_URL` | No | URL the bot uses to reach the backend. Default (`http://backend:8000`) is correct for Docker Compose. Change to `http://localhost:8000` for direct runs. |

#### Discord variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Yes (Discord) | Token for your Discord bot application. Create one at [Discord Developer Portal](https://discord.com/developers/applications). The bot needs the **Message Content** privileged intent enabled (Bot > Privileged Gateway Intents) and permissions to read and send messages. |
| `DISCORD_ALLOWED_USER_IDS` | Yes (Discord) | Comma-separated numeric Discord user IDs that are permitted to submit ideas. Find a user ID by enabling Developer Mode in Discord (Settings > Advanced), then right-clicking a user and choosing "Copy User ID". |
| `DISCORD_IDEA_CHANNEL_ID` | No | Numeric ID of a guild channel where the bot should also accept ideas. If unset, the bot only responds to Direct Messages. Right-click the channel and choose "Copy Channel ID" (requires Developer Mode). |

#### Telegram variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes (Telegram) | Token for your Telegram bot. Create a bot and get the token via [@BotFather](https://t.me/botfather). |
| `TELEGRAM_ALLOWED_USER_IDS` | Yes (Telegram) | Comma-separated numeric Telegram user IDs that are permitted to submit ideas. Find your ID by messaging [@userinfobot](https://t.me/userinfobot). |

## Running the Application

### Recommended: Run with Docker Compose

The recommended way to run the full stack is Docker Compose.

Start (or rebuild) services:

```bash
docker compose up -d --build
```

This starts:
- `backend` on the internal Compose network (`http://backend:8000`)
- `bot` with provider selected by `BOT_PROVIDER` (`discord` or `telegram`)

Note:
- Backend is intentionally internal-only in Compose (not published to host port `8000`).
- Set `DRY_RUN=true` in `.env.backend` if you want to test without creating real GitHub issues.

Check status:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f bot
```

Stop services:

```bash
docker compose down
```

### Optional: One-step deploy to GCP VM

If you want a low-manual cloud setup, use the deploy script:

```bash
./scripts/deploy_gcp.sh
```

What it does:
- prompts for required config/secrets (`GEMINI_API_KEY`, GitHub, Discord/Telegram),
- creates or reuses a GCE VM,
- installs Docker + Compose on the VM,
- uploads this repo and writes `.env.backend` / `.env.bot`,
- runs `docker compose up -d --build` remotely.

Prerequisites for script:
- `gcloud` CLI installed locally
- an authenticated account (`gcloud auth login`)
- project access with permission to create/modify Compute Engine resources

Health check from inside the backend container:

```bash
docker compose exec backend curl -fsS http://localhost:8000/health
```

### Advanced: Run Without Docker (Direct Python)

Use this only if you want manual process control.

#### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure env files for direct mode

For direct runs, use host-local backend URL in `.env.bot`:

```bash
BACKEND_URL=http://localhost:8000
```

#### 3. Run backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Run bot runtime

Set one of:
- `BOT_PROVIDER=discord`
- `BOT_PROVIDER=telegram`

Run:

```bash
python -m bot.main
```

#### Provider notes

- Discord mode responds to Direct Messages and, if `DISCORD_IDEA_CHANNEL_ID` is set, to messages in that guild channel.
- Telegram mode processes only users in `TELEGRAM_ALLOWED_USER_IDS`.

## Testing

Run the test suite:

```bash
python -m pytest
```

## Architecture

- **Backend** (`backend/`): FastAPI service that uses Gemini to structure ideas and creates GitHub issues
- **Bot runtime** (`bot/main.py`): provider switch (`discord` or `telegram`) based on `BOT_PROVIDER`
- **Discord bot** (`bot/discord/`): Discord client that forwards messages to the backend
- **Telegram bot** (`bot/telegram/`): Telegram client that forwards messages to the backend
