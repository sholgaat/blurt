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
    @abstractmethod
    def register_message_handler(self, handler: MessageHandler) -> None:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
