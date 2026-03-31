from __future__ import annotations

import logging
from functools import partial

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_service import format_issue_reply, submit_idea
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
        await update.message.reply_text("Sorry, this bot is restricted to approved users.")
        return

    result, error = await submit_idea(
        backend_client,
        text=text,
        user_id=user_id,
        source="telegram",
    )
    if error:
        await update.message.reply_text(error)
        return

    await update.message.reply_text(format_issue_reply(result))


def main() -> None:
    cfg = get_bot_settings()

    if not cfg.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")

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
