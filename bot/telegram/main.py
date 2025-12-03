from __future__ import annotations

import logging
from typing import Set

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.config import BACKEND_URL, TELEGRAM_BOT_TOKEN
from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_USER_IDS: Set[int] = {5241294807}

def _get_backend_client(context: ContextTypes.DEFAULT_TYPE) -> IdeaBackendClient:
    backend_client = context.application.bot_data.get("backend_client")
    if not isinstance(backend_client, IdeaBackendClient):
        raise RuntimeError("Backend client not available on application.")
    return backend_client


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    backend_client = _get_backend_client(context)
    text = update.message.text or ""
    user_id = str(update.effective_user.id)
    numeric_id = update.effective_user.id

    if numeric_id not in ALLOWED_USER_IDS:
        logger.warning("Blocked message from unauthorized user_id=%s", numeric_id)
        await update.message.reply_text("Sorry, this bot is restricted to approved users.")
        return

    try:
        data = await backend_client.create_idea(text=text, user_id=user_id, source="telegram")
    except BackendConnectionError:
        await update.message.reply_text("Sorry, I couldn't reach the backend right now.")
        return
    except BackendResponseError:
        await update.message.reply_text("Sorry, I couldn't log that idea (backend error).")
        return

    title = data.get("title", "Untitled")
    url = data.get("url", BACKEND_URL)
    await update.message.reply_text(f"💡 Created issue: {title}\n{url}")


async def _on_startup(application: Application) -> None:
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, IdeaBackendClient):
        await backend_client.start()


async def _on_shutdown(application: Application) -> None:
    backend_client = application.bot_data.get("backend_client")
    if isinstance(backend_client, IdeaBackendClient):
        await backend_client.close()


def build_application(
    *, token: str, backend_client: IdeaBackendClient | None = None
) -> Application:
    backend_client = backend_client or IdeaBackendClient(BACKEND_URL)

    application = (
        Application.builder()
        .token(token)
        .post_init(_on_startup)
        .post_shutdown(_on_shutdown)
        .build()
    )
    application.bot_data["backend_client"] = backend_client
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")

    application = build_application(token=TELEGRAM_BOT_TOKEN)
    logger.info("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
