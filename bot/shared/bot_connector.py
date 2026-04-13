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
    def __init__(self) -> None:
        self._message_handler: MessageHandler | None = None

    def register_message_handler(self, handler: MessageHandler) -> None:
        self._message_handler = handler

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
