# idea-inbox
A tool to capture ideas from chat, use Gemini to clean them up, and create GitHub issues automatically.

## Setup

### Prerequisites
- Docker + Docker Compose
- Python 3.12 or higher (only needed for direct/manual runs and local tests)

### 1. Configure Environment Variables

Copy the service-specific environment templates:

```bash
cp .env.backend.example .env.backend
cp .env.bot.example .env.bot
```

Edit `.env.backend` with backend credentials:

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

Edit `.env.bot` with bot-only runtime values:

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

Start services:

```bash
docker compose up -d --build
```

This starts:
- `backend` on `http://localhost:8000`
- `bot` with provider selected by `BOT_PROVIDER` (`discord` or `telegram`)

Check status:

```bash
docker compose ps
docker compose logs -f
```

Stop services:

```bash
docker compose down
```

### Advanced: Run Without Docker (Direct Python)

Use this only if you want manual process control.

#### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Run backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Run bot runtime

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


## Testing

Run the test suite:

```bash
pytest
```

## Architecture

- **Backend** (`backend/`): FastAPI service that uses Gemini to structure ideas and creates GitHub issues
- **Bot runtime** (`bot/main.py`): provider switch (`discord` or `telegram`) based on `BOT_PROVIDER`
- **Discord bot** (`bot/discord/`): Discord client that forwards messages to the backend
- **Telegram bot** (`bot/telegram/`): Telegram client that forwards messages to the backend
