from __future__ import annotations

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)

MAX_IDEA_LENGTH = 4096

BACKEND_UNAVAILABLE_MSG = "Couldn't reach the backend right now — please try again shortly."
BACKEND_ERROR_MSG = "Something went wrong saving that idea — please try again."
EMPTY_IDEA_MSG = "Send me your idea as a message and I'll log it."
# Interpolate the length constant so tests and messages stay in sync if the value changes
TOO_LONG_IDEA_MSG = (
    f"That message is too long (max {MAX_IDEA_LENGTH} characters). "
    "Try summarising it a bit."
)


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
    lines.append("")
    if summary:
        lines.append(summary)
    lines.append("")
    if tags:
        lines.append("Tags: " + " · ".join(tags))
    lines.append("")
    lines.append(url)
    return "\n".join(lines)
