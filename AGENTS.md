# idea-inbox — AGENTS

This project uses two agents/components:

## 1. Backend (FastAPI)
- Location: backend/
- Responsibilities (current):
  - Provide GET /health → {"status": "ok"}.
  - Provide POST /ideas → accept {text, user_id, source}.
  - Use Gemini to generate:
    - title
    - summary
    - tags
  - Create a GitHub issue and return {title, summary, tags, url}.
  - Support `DRY_RUN=true` for testing without creating a real issue.

## 2. Bot Runtime (Discord + Telegram)
- Location: bot/
- Responsibilities (current):
  - Run either Discord or Telegram bot based on `BOT_PROVIDER`.
  - Discord: listen for DMs and messages in #idea-inbox.
  - Telegram: listen for messages from allowed user IDs.
  - POST message content to backend /ideas.
  - Reply with the processed title + returned issue URL.

## Current scope boundaries
- Bots call only the backend service directly.
- Backend integrations are limited to Gemini (cleanup/structuring) and GitHub Issues creation.
- No OAuth flow or advanced authentication yet.
