from __future__ import annotations

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

TEST_BACKEND_URL = "http://example.com"

SUCCESS_RESPONSE = {"title": "Test Idea", "url": "http://example.com/idea"}


class FakeBackend(IdeaBackendClient):
    """Configurable mock backend for tests.

    Pass a dict for a success response, or an Exception instance to raise.
    """

    def __init__(self, response: dict | Exception | None = None):
        super().__init__(base_url=TEST_BACKEND_URL)
        self.response: dict | Exception = response if response is not None else SUCCESS_RESPONSE
        self.called_with: tuple | None = None

    async def start(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        self.called_with = (text, user_id, source)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response
