"""Blurt: Discord/Telegram bot that captures ideas and creates GitHub issues."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("blurt")
except PackageNotFoundError:
    # Package not installed (e.g. running from source without install)
    __version__ = "unknown"
