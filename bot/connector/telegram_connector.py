from __future__ import annotations

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.connector.bot_connector import BotConnector, MessageEnvelope


class TelegramConnector(BotConnector):
    @classmethod
    def validate_config(cls, cfg) -> None:
        if not cfg.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in the environment.")
        if not cfg.telegram_allowed_user_ids:
            raise RuntimeError(
                "TELEGRAM_ALLOWED_USER_IDS is not set in the environment. "
                "Provide a comma-separated list of Telegram user IDs that are allowed to submit ideas."
            )

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
