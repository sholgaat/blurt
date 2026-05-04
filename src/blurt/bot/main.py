from __future__ import annotations

import logging

from blurt.bot.backend_client import IdeaBackendClient
from blurt.bot.idea_handler import IdeaHandler
from blurt.bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    cfg = get_bot_settings()
    provider = cfg.bot_provider.strip().lower()

    backend_client = IdeaBackendClient(cfg.backend_url)

    handler = IdeaHandler(
        backend_client=backend_client,
        allowed_user_ids=cfg.allowed_user_ids,
        source=provider,
        backend_timeout=cfg.idea_creation_timeout,
    )

    if provider == "telegram":
        from bot.connector.telegram_connector import TelegramConnector

        connector = TelegramConnector(cfg.telegram_bot_token, handler.handle_message)

    elif provider == "discord":
        from bot.connector.discord_connector import DiscordConnector

        connector = DiscordConnector(
            cfg.discord_bot_token,
            handler.handle_message,
        )
    else:
        raise RuntimeError(
            f"Unsupported BOT_PROVIDER: {provider!r}. Use 'telegram' or 'discord'."
        )

    logger.info("%s is running...", connector.__class__.__name__)
    connector.start()


if __name__ == "__main__":
    main()
