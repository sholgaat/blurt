from __future__ import annotations

import logging

from bot.backend_client import IdeaBackendClient
from bot.idea_handler import IdeaHandler
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    cfg = get_bot_settings()
    provider = cfg.bot_provider.strip().lower()

    backend_client = IdeaBackendClient(cfg.backend_url)

    if provider == "telegram":
        from bot.connector.telegram_connector import TelegramConnector

        TelegramConnector.validate_config(cfg)

        allowed_user_ids = cfg.telegram_allowed_user_ids

        connector = TelegramConnector(cfg.telegram_bot_token)

    elif provider == "discord":
        from bot.connector.discord_connector import DiscordConnector

        DiscordConnector.validate_config(cfg)

        allowed_user_ids = cfg.discord_allowed_user_ids

        connector = DiscordConnector(
            cfg.discord_bot_token,
            idea_channel_id=cfg.discord_idea_channel_id,
        )
    else:
        raise RuntimeError(
            f"Unsupported BOT_PROVIDER: {provider!r}. Use 'telegram' or 'discord'."
        )
    handler = IdeaHandler(
        backend_client=backend_client,
        allowed_user_ids=allowed_user_ids,
        source=provider,
        backend_timeout=cfg.idea_creation_timeout,
    )
    connector.register_message_handler(handler.handle_message)

    logger.info("%s is running...", connector.__class__.__name__)
    connector.start()


if __name__ == "__main__":
    main()
