from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(slots=True)
class MessageEnvelope:
    user_id: str
    text: str
    reply: Callable[[str], Awaitable[None]]


MessageHandler = Callable[[MessageEnvelope], Awaitable[None]]


class BotConnector(ABC):
    def __init__(self, handler: MessageHandler) -> None:
        self._message_handler = handler

    @abstractmethod
    def start(self) -> None:
        """Start the bot. This is a blocking call that runs until the bot exits."""
        raise NotImplementedError
