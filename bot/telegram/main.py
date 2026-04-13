from __future__ import annotations

import logging

from bot.connectors.telegram_connector import TelegramConnector
from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_handler import IdeaHandler
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    cfg = get_bot_settings()

    if not cfg.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")
    if not cfg.telegram_allowed_user_ids:
        raise RuntimeError(
            "TELEGRAM_ALLOWED_USER_IDS is not set in the environment. "
            "Provide a comma-separated list of Telegram user IDs that are allowed to submit ideas."
        )

    backend_client = IdeaBackendClient(cfg.backend_url)
    handler = IdeaHandler(
        backend_client=backend_client,
        allowed_user_ids=cfg.telegram_allowed_user_ids,
        source="telegram",
        backend_timeout=cfg.idea_creation_timeout,
    )
    connector = TelegramConnector(cfg.telegram_bot_token)
    connector.register_message_handler(handler.handle_message)

    logger.info("Telegram bot is running...")
    connector.start()


if __name__ == "__main__":
    main()
