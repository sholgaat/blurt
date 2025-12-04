from __future__ import annotations

from idea_inbox import settings

settings.ensure_env_loaded()

DISCORD_BOT_TOKEN = settings.get_discord_bot_token()
DISCORD_TOKEN = DISCORD_BOT_TOKEN  # Backwards compatibility for discord client.
TELEGRAM_BOT_TOKEN = settings.get_telegram_bot_token()
TELEGRAM_ALLOWED_USER_IDS = settings.get_telegram_allowed_user_ids()
BACKEND_URL = settings.get_backend_url()
