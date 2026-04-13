from __future__ import annotations

import logging

from bot.connectors.discord_connector import DiscordConnector
from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_handler import IdeaHandler
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    cfg = get_bot_settings()

    if not cfg.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")
    if not cfg.discord_allowed_user_ids:
        raise RuntimeError(
            "DISCORD_ALLOWED_USER_IDS is not set in the environment. "
            "Provide a comma-separated list of Discord user IDs that are allowed to submit ideas."
        )

    backend_client = IdeaBackendClient(cfg.backend_url)
    handler = IdeaHandler(
        backend_client=backend_client,
        allowed_user_ids=cfg.discord_allowed_user_ids,
        source="discord",
        backend_timeout=cfg.idea_creation_timeout,
    )
    connector = DiscordConnector(
        cfg.discord_bot_token,
        idea_channel_id=cfg.discord_idea_channel_id,
    )
    connector.register_message_handler(handler.handle_message)

    if not cfg.discord_idea_channel_id:
        logger.warning(
            "DISCORD_IDEA_CHANNEL_ID is not set. The bot will only respond to Direct Messages."
        )

    logger.info("Discord bot is running...")
    connector.start()


if __name__ == "__main__":
    main()
