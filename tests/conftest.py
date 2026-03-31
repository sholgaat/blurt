from __future__ import annotations

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

TEST_BACKEND_URL = "http://example.com"


class BaseMockBackend(IdeaBackendClient):
    """Base class for mock backend implementations used across bot tests."""

    def __init__(self):
        super().__init__(base_url=TEST_BACKEND_URL)

    async def start(self) -> None:  # pragma: no cover - no-op for tests
        pass

    async def close(self) -> None:  # pragma: no cover - no-op for tests
        pass


class DummyBackend(BaseMockBackend):
    """Mock backend that returns a canned success response."""

    def __init__(self):
        super().__init__()
        self.called_with: tuple | None = None

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        self.called_with = (text, user_id, source)
        return {"title": "Test Idea", "url": "http://example.com/idea"}


class BackendRaisesConnectionError(BaseMockBackend):
    """Mock backend that raises BackendConnectionError."""

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        raise BackendConnectionError("Failed to reach backend.")


class BackendRaisesResponseError(BaseMockBackend):
    """Mock backend that raises BackendResponseError."""

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        raise BackendResponseError("Backend returned an error status.")
