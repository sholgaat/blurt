from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.shared.bot_connector import (
    BotConnector,
    MessageEnvelope,
    MessageHandler as EnvelopeHandler,
)

logger = logging.getLogger(__name__)


class TelegramConnector(BotConnector):
    def __init__(self, token: str):
        self._token = token
        self._message_handler: EnvelopeHandler | None = None
        self._application = Application.builder().token(token).build()
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_update)
        )

    def register_message_handler(self, handler: EnvelopeHandler) -> None:
        self._message_handler = handler

    def start(self) -> None:
        if not self._token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")
        self._application.run_polling()

    def stop(self) -> None:
        self._application.stop_running()

    async def _handle_update(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.effective_user:
            return
        if self._message_handler is None:
            logger.warning("No Telegram message handler registered")
            return

        envelope = MessageEnvelope(
            user_id=str(update.effective_user.id),
            text=update.message.text or "",
            reply=update.message.reply_text,
        )
        await self._message_handler(envelope)
