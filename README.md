# idea-inbox
A tool to capture ideas from chat, use Gemini to clean them up, and create GitHub issues automatically.

## Quickstart (60 Seconds)

```bash
# 1) Create service env files
cp .env.backend.example .env.backend
cp .env.bot.example .env.bot

# 2) Fill required values
# - .env.backend: GEMINI_API_KEY, GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
# - .env.bot: BOT_PROVIDER + bot token(s)

# 3) Safe first run (no real GitHub issues)
echo "DRY_RUN=true" >> .env.backend

# 4) Start
docker compose up -d --build

# 5) Watch logs
docker compose logs -f backend
docker compose logs -f bot
```

In Docker Compose, backend is internal-only (`http://backend:8000`) and not exposed to host port `8000`.

## Setup

### Prerequisites
- Docker + Docker Compose
- Python 3.12 or higher (only needed for direct/manual runs and local tests)

### 1. Create service env files

Copy the service-specific environment templates:

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
GEMINI_API_KEY=your_gemini_api_key

# Optional: Set to "true" to test without creating actual GitHub issues
DRY_RUN=false
```

### 3. Configure bot runtime (`.env.bot`)

```bash
BOT_PROVIDER=discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_USER_IDS=123456789
BACKEND_URL=http://backend:8000
```

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

- Discord mode listens for DMs and messages in channels named `#idea-inbox`.
- Telegram mode processes only `TELEGRAM_ALLOWED_USER_IDS` (comma-separated IDs).
- Diagram: see `docs/flow.md`.

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
