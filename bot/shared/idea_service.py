from __future__ import annotations

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

BACKEND_UNAVAILABLE_MSG = "Couldn't reach the backend right now — please try again shortly."
BACKEND_ERROR_MSG = "Something went wrong saving that idea — please try again."


async def submit_idea(
    backend_client: IdeaBackendClient,
    *,
    text: str,
    user_id: str,
    source: str,
) -> str:
    """Submit an idea and return a formatted reply string."""
    try:
        data = await backend_client.create_idea(text=text, user_id=user_id, source=source)
    except BackendConnectionError:
        return BACKEND_UNAVAILABLE_MSG
    except BackendResponseError:
        return BACKEND_ERROR_MSG

    title = data.get("title") or "Untitled"
    url = data.get("url") or "(no URL returned)"
    summary = data.get("summary") or ""
    tags = data.get("tags") or []

    lines = [f"Idea captured — {title}"]
    if summary:
        lines.append(summary)
    if tags:
        lines.append("Tags: " + " · ".join(tags))
    lines.append(url)
    return "\n".join(lines)
