from __future__ import annotations

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from blurt.bot.connector.bot_connector import BotConnector, MessageEnvelope, MessageHandler as MessageHandlerType


class TelegramConnector(BotConnector):
    def __init__(self, token: str, handler: MessageHandlerType):
        super().__init__(handler)
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")
        self._token = token
        self._application = Application.builder().token(token).build()
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._normalise_message)
        )

    def start(self) -> None:
        self._application.run_polling()

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

        await self._message_handler(envelope)
