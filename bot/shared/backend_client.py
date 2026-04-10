from __future__ import annotations

import httpx


class BackendConnectionError(Exception):
    """Raised when the backend cannot be reached."""


class BackendResponseError(Exception):
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
            await self.start()

        payload = {"text": text, "user_id": user_id, "source": source}

        try:
            response = await self.http_client.post("/ideas", json=payload, timeout=30.0)
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            raise BackendConnectionError("Failed to reach backend.") from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BackendResponseError("Backend returned an error status.") from exc

        return response.json()
