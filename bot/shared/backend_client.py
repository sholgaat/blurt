from __future__ import annotations

import httpx


class BackendClientError(Exception):
    """Base exception for backend client errors."""


class BackendConnectionError(BackendClientError):
    """Raised when the backend cannot be reached."""


class BackendResponseError(BackendClientError):
    """Raised when the backend responds with an error status."""


class IdeaBackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http_client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(base_url=self.base_url)

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

    async def create_idea(self, text: str, user_id: str, source: str) -> dict:
        if not self.http_client:
            raise BackendConnectionError("HTTP client not initialized.")

        payload = {"text": text, "user_id": user_id, "source": source}

        try:
            response = await self.http_client.post("/ideas", json=payload, timeout=15.0)
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            raise BackendConnectionError("Failed to reach backend.") from exc

        if response.status_code != 200:
            raise BackendResponseError("Backend returned an error status.")

        return response.json()
