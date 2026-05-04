# Public Release Readiness — Implementation Plan

This document tracks the 8-item action plan to prepare blurt for public release. Each item will be implemented sequentially, reviewed, committed, then marked complete.

## Overview

| # | Item | Status | Priority |
|---|---|---|---|
| 1 | Rotate secrets (manual step) | ⏳ | HIGH |
| 2 | Add CI test workflow + update publish.yml | ⏳ | HIGH |
| 3 | Migrate to pyproject.toml + update Dockerfiles | ⏳ | HIGH |
| 4 | Add non-root user to Dockerfiles | ⏳ | HIGH |
| 5 | Remove DRY_RUN references | ⏳ | MEDIUM |
| 6 | Fix Anthropic get_total_tokens | ⏳ | MEDIUM |
| 7 | Add startup validation for github_token/repo | ⏳ | MEDIUM |
| 8 | Discord DM-only default + optional channel IDs | ⏳ | MEDIUM |

---

## Item 1: Rotate secrets (manual step — user handles)

**Status:** Awaiting user action

**What:** User rotates all live credentials that were present in `.env.backend` and `.env.bot`:
- GitHub Personal Access Token (ghp_...)
- Gemini API key
- Telegram bot token
- Discord bot token

**Then:** Run `git log --all -- .env.backend .env.bot` to check if these files appear in git history. If they do, use `git filter-repo` or BFG Repo Cleaner to purge before public release.

**Commit:** None (manual action)

---

## Item 2: Add CI test workflow + update publish.yml

**Status:** Pending implementation

**Files to create:**
- `.github/workflows/test.yml` — runs pytest on push to main + all PRs

**Files to update:**
- `.github/workflows/publish.yml` — add `needs: test` dependency; add inline test job

**Changes:**
- New workflow triggers on: push to `main`, all pull requests
- Runs: checkout → install dev deps → pytest
- Publish workflow only pushes images if test job succeeds

---

## Item 3: Migrate to pyproject.toml + update Dockerfiles

**Status:** Pending implementation

**Files to create:**
- `pyproject.toml` (root) — dev tools, pytest config
- `backend/pyproject.toml` — backend package + all LLM SDKs as regular dependencies
- `bot/pyproject.toml` — bot package

**Files to delete:**
- `requirements.txt` (root)
- `backend/requirements.txt`
- `bot/requirements.txt`
- `pytest.ini`

**Files to update:**
- `backend/Dockerfile` — change pip install to use `./backend`
- `bot/Dockerfile` — change pip install to use `./bot`
- `docker-compose.override.yml` — if needed
- `README.md` — update setup instructions

**Details:**
- All LLM SDKs (google-genai, openai, anthropic, ollama) installed as plain dependencies, not optional extras
- Version bounds: reasonable lower bounds on major packages (fastapi>=0.115, httpx>=0.27, etc.)
- pytest config moves from `pytest.ini` to `[tool.pytest.ini_options]` in root `pyproject.toml`

---

## Item 4: Add non-root user to both Dockerfiles

**Status:** Pending implementation

**Files to update:**
- `backend/Dockerfile`
- `bot/Dockerfile`

**Changes:**
- Add `RUN adduser --disabled-password --gecos "" appuser` after `pip install`
- Add `USER appuser` before `CMD`

**Reason:** Security hardening — containers run as unprivileged user instead of root.

---

## Item 5: Remove DRY_RUN references

**Status:** Pending implementation

**Files to update:**
- `.env.backend.example` — remove `DRY_RUN=false` line
- `AGENTS.md` — remove "Support `DRY_RUN=true` for testing" from backend responsibilities

**Reason:** DRY_RUN was never implemented; removing it eliminates confusion.

---

## Item 6: Fix Anthropic get_total_tokens

**Status:** Pending implementation

**Files to update:**
- `backend/llm/providers/anthropic.py`

**Changes:**
- Replace `get_total_tokens` method to derive total from `input_tokens + output_tokens` instead of calling `getattr(usage, "total_tokens", None)` which always returns None.

---

## Item 7: Add startup validation for github_token/repo

**Status:** Pending implementation

**Files to update:**
- `backend/settings.py`

**Changes:**
- Add Pydantic `@model_validator(mode="after")` to `BackendSettings`
- Validates that `github_token` and `github_repo` are non-empty at startup
- Raises clear error message if either is missing, causing app to fail-fast

---

## Item 8: Discord DM-only by default + optional channel IDs

**Status:** Pending implementation

**Files to update:**
- `bot/settings.py` — add `discord_channel_ids: set[int]` field
- `bot/connector/discord_connector.py` — add message filter logic
- `.env.bot.example` — add commented `DISCORD_CHANNEL_IDS` explanation

**Changes:**
- By default: bot only responds to DMs
- If `DISCORD_CHANNEL_IDS` is set (comma-separated channel IDs), bot also accepts messages in those specific channels
- No separate `DISCORD_DM_ONLY` flag needed

---

## Workflow

For each pending item:
1. Implement all file changes
2. Show diffs for user review
3. Await user approval (or request modifications)
4. Commit changes with clear message
5. Mark item as ✅ DONE
6. Move to next item

---

**Last updated:** Implementation starting
