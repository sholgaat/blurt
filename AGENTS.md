# idea-inbox — AGENTS

This project uses two agents/components:

## 1. Backend (FastAPI)
- Location: backend/
- Responsibilities (v0 only):
  - Provide GET /health → {"status": "ok"}.
  - Provide POST /ideas → accept {text, user_id, source}.
  - Run simple heuristics:
    - create_title()
    - create_summary()
    - classify_tags()
  - Return {title, summary, tags, url} where url is a FAKE placeholder.
- No GitHub integration yet.
- No LLM usage yet.

## 2. Discord Bot (discord.py)
- Location: bot/
- Responsibilities (v0 only):
  - Listen for DMs and messages in #idea-inbox.
  - POST message content to backend /ideas.
  - Reply with the processed title + fake URL.
- No GitHub integration yet.
- No LLM usage yet.

## Scope boundaries for v0
- Backend and bot must remain minimal.
- No external APIs except bot→backend.
- Real GitHub issue creation and LLM polishing will be implemented in v1.
