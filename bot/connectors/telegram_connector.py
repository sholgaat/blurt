from __future__ import annotations

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.shared.bot_connector import BotConnector, MessageEnvelope


class TelegramConnector(BotConnector):
    def __init__(self, token: str):
        super().__init__()
        self._token = token
        self._application = Application.builder().token(token).build()
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._normalise_message)
        )

    def start(self) -> None:
        if not self._token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")
        self._application.run_polling()

    def stop(self) -> None:
        self._application.stop_running()

    async def _normalise_message(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.effective_user:
            return

        envelope = MessageEnvelope(
            user_id=str(update.effective_user.id),
            text=update.message.text or "",
            reply=update.message.reply_text,
        )

        if self._message_handler is None:
            return
        await self._message_handler(envelope)
