from __future__ import annotations

from bot.settings import get_bot_settings


def main() -> None:
    provider = get_bot_settings().bot_provider.strip().lower()

    if provider == "telegram":
        from bot.telegram.main import main as telegram_main

        telegram_main()
        return

    if provider == "discord":
        from bot.discord.main import main as discord_main

        discord_main()
        return

    raise RuntimeError(
        f"Unsupported BOT_PROVIDER: {provider!r}. Use 'telegram' or 'discord'."
    )


if __name__ == "__main__":
    main()
