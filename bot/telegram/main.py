from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.shared.backend_client import IdeaBackendClient
from bot.shared.idea_service import format_issue_reply, submit_idea
from bot.settings import get_bot_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> IdeaBackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, IdeaBackendClient):
        raise RuntimeError("Backend client not available on application.")
    return backend_client


def _get_allowed_user_ids(context: ContextTypes.DEFAULT_TYPE) -> set[int]:
    allowed = context.application.bot_data.get("allowed_user_ids")
    if not isinstance(allowed, set):
        raise RuntimeError("allowed_user_ids not available on application.")
    return allowed


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    backend_client = _get_backend_client(context)
    allowed_user_ids = _get_allowed_user_ids(context)
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


async def _on_startup(application: Application) -> None:
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, IdeaBackendClient):
        await backend_client.start()


async def _on_shutdown(application: Application) -> None:
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, IdeaBackendClient):
        await backend_client.close()


def build_application(
    *,
    token: str,
    backend_client: IdeaBackendClient | None = None,
    allowed_user_ids: set[int] | None = None,
) -> Application:
    cfg = get_bot_settings()
    backend_client = backend_client or IdeaBackendClient(cfg.backend_url)
    allowed_user_ids = allowed_user_ids if allowed_user_ids is not None else cfg.telegram_allowed_user_ids

    application = (
        Application.builder()
        .token(token)
        .post_init(_on_startup)
        .post_shutdown(_on_shutdown)
        .build()
    )
    application.bot_data["backend_client"] = backend_client
    application.bot_data["allowed_user_ids"] = allowed_user_ids
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


def main() -> None:
    cfg = get_bot_settings()

    if not cfg.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")

    application = build_application(token=cfg.telegram_bot_token)
    logger.info("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
