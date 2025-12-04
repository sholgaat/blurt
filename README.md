# idea-inbox
A simple tool to help record ideas for new coding projects.

## Setup

### Prerequisites
- Python 3.12 or higher

### 1. Create a Virtual Environment

Create a virtual environment to isolate project dependencies:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Requirements

Install all project dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required for Discord bot
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Required for Telegram bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Backend URL (default: http://localhost:8000)
BACKEND_URL=http://localhost:8000

# Required for backend GitHub integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=your_repository_name

# Required for backend LLM features
GEMINI_API_KEY=your_gemini_api_key

# Optional: Set to "true" to test without creating actual GitHub issues
DRY_RUN=false
```

## Running the Application

### Run the Backend

The backend is a FastAPI application that processes ideas and creates GitHub issues.

Start the backend server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`.

You can check if it's running by visiting `http://localhost:8000/health` or using:

```bash
curl http://localhost:8000/health
```

### Run the Discord Bot

The Discord bot listens for messages in DMs or in channels named `#idea-inbox`.

**Prerequisites:**
- Set `DISCORD_BOT_TOKEN` in your `.env` file
- Ensure the backend is running

Run the Discord bot:

```bash
python -m bot.discord.main
```

### Run the Telegram Bot

The Telegram bot processes messages from authorized users.

**Prerequisites:**
- Set `TELEGRAM_BOT_TOKEN` in your `.env` file
- Ensure the backend is running

Run the Telegram bot:

```bash
python -m bot.telegram.main
```

## Testing

Run the test suite:

```bash
pytest
```

## Architecture

- **Backend** (`backend/`): FastAPI service that processes ideas using LLM and creates GitHub issues
- **Discord Bot** (`bot/discord/`): Discord client that forwards messages to the backend
- **Telegram Bot** (`bot/telegram/`): Telegram client that forwards messages to the backend
