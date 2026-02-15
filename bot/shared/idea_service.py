from __future__ import annotations

from dataclasses import dataclass

from bot.shared.backend_client import (
    BackendConnectionError,
    BackendResponseError,
    IdeaBackendClient,
)


BACKEND_UNAVAILABLE_MSG = "Sorry, I couldn't reach the backend right now."
BACKEND_ERROR_MSG = "Sorry, I couldn't log that idea (backend error)."


@dataclass
class IdeaSubmissionResult:
    title: str
    url: str


async def submit_idea(
    backend_client: IdeaBackendClient,
    *,
    text: str,
    user_id: str,
    source: str,
) -> tuple[IdeaSubmissionResult | None, str | None]:
    try:
        data = await backend_client.create_idea(text=text, user_id=user_id, source=source)
    except BackendConnectionError:
        return None, BACKEND_UNAVAILABLE_MSG
    except BackendResponseError:
        return None, BACKEND_ERROR_MSG

    title = data.get("title", "Untitled")
    url = data.get("url", "(no URL returned)")
    return IdeaSubmissionResult(title=title, url=url), None


def format_issue_reply(result: IdeaSubmissionResult, *, bold_title: bool = False) -> str:
    title = result.title or "Untitled"
    if bold_title:
        title = f"**{title}**"
    return f"💡 Created issue: {title}\n{result.url}"
