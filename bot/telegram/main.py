from __future__ import annotations

import logging
from functools import partial

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

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
    allowed_user_ids: set[int],
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message or not update.effective_user:
        return

    text = update.message.text or ""
    user_id = str(update.effective_user.id)
    numeric_id = update.effective_user.id

    if numeric_id not in allowed_user_ids:
        logger.warning("Blocked message from unauthorized user_id=%s", numeric_id)
        await update.message.reply_text(
            f"This bot is private — you're not on the approved list. "
            f"Ask the owner to add your user ID: {numeric_id}"
        )
        return

    if not text.strip():
        await update.message.reply_text(EMPTY_IDEA_MSG)
        return
    if len(text) > MAX_IDEA_LENGTH:
        await update.message.reply_text(TOO_LONG_IDEA_MSG)
        return

    reply = await submit_idea(
        backend_client,
        text=text,
        user_id=user_id,
        source="telegram",
    )
    await update.message.reply_text(reply)


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
            partial(handle_message, backend_client, cfg.telegram_allowed_user_ids),
        )
    )

    logger.info("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
