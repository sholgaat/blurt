# idea-inbox
A simple tool to help record ideas for new coding projects.

## Bots

### Discord
- Set `DISCORD_TOKEN` and optionally `BACKEND_URL` in your environment or `.env` file.
- Run the Discord bot (default entrypoint):
  - `python -m bot.discord.main`

### Telegram
- Set `TELEGRAM_BOT_TOKEN` and optionally `BACKEND_URL` in your environment or `.env` file.
- Run the Telegram bot:
  - `python -m bot.telegram.main`
