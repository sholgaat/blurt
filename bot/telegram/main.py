from __future__ import annotations

import asyncio
import logging
from functools import partial

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_service import (
    EMPTY_IDEA_MSG,
    MAX_IDEA_LENGTH,
    TOO_LONG_IDEA_MSG,
    submit_idea,
)
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_message(
    backend_client: IdeaBackendClient,
    allowed_user_ids: set[str],
    update: Update,
    idea_creation_timeout: int = 30,
) -> None:
    if not update.message or not update.effective_user:
        return

    text = update.message.text or ""
    user_id = str(update.effective_user.id)

    if user_id not in allowed_user_ids:
        logger.warning("Blocked message from unauthorized user_id=%s", user_id)
        await update.message.reply_text(
            f"This bot is private — you're not on the approved list. "
            f"Ask the owner to add your user ID: {user_id}"
        )
        return

    if not text.strip():
        await update.message.reply_text(EMPTY_IDEA_MSG)
        return
    if len(text) > MAX_IDEA_LENGTH:
        await update.message.reply_text(TOO_LONG_IDEA_MSG)
        return

    await update.message.reply_text("📝 Got it, processing your idea...")
    asyncio.create_task(
        process_and_send_update(
            backend_client=backend_client,
            update=update,
            text=text,
            user_id=user_id,
            timeout=idea_creation_timeout,
        )
    )


async def process_and_send_update(
    *,
    backend_client: IdeaBackendClient,
    update: Update,
    text: str,
    user_id: str,
    timeout: int,
) -> None:
    try:
        reply = await submit_idea(
            backend_client,
            text=text,
            user_id=user_id,
            source="telegram",
            timeout=timeout,
        )
        await update.message.reply_text(reply)
    except Exception:
        logger.exception("Failed to process or send Telegram idea update")


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

    async def _close_backend(_app: Application) -> None:
        await backend_client.close()

    application = (
        Application.builder()
        .token(cfg.telegram_bot_token)
        .post_shutdown(_close_backend)
        .build()
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            partial(
                handle_message,
                backend_client,
                cfg.telegram_allowed_user_ids,
                idea_creation_timeout=cfg.idea_creation_timeout,
            ),
        )
    )

    logger.info("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
