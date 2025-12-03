from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from fastapi import Body, FastAPI
from pydantic import BaseModel, Field

from backend.processing import (
    classify_tags,
    create_summary,
    create_title,
    ensure_default_tag,
)
from backend.github_client import create_issue
from backend.llm import LlmError, call_ai_cleanup

# Basic logger for the backend module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Idea Inbox Backend", version="0.0.1")


class IdeaRequest(BaseModel):
    text: str = Field(..., description="Raw idea text from the user")
    user_id: Optional[str] = Field(
        None, description="User identifier if available from the source"
    )
    source: str = Field(
        "discord", description="Origin of the idea submission (default: discord)"
    )


class IdeaResponse(BaseModel):
    title: str
    summary: str
    tags: list[str]
    url: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ideas", response_model=IdeaResponse)
async def create_idea(ai: int = 1, payload: IdeaRequest = Body(...)) -> IdeaResponse:
    logger.info(
        "Creating idea (user=%s, source=%s): %s",
        payload.user_id,
        payload.source,
        payload.text,
    )
    raw_text = payload.text or ""

    title: str
    summary: str
    tags: list[str]

    if ai == 1:
        try:
            llm_result = await call_ai_cleanup(raw_text)
            title = llm_result.get("title") or create_title(raw_text)
            summary = llm_result.get("summary") or create_summary(raw_text)
            tags = ensure_default_tag(llm_result.get("tags") or [])
        except LlmError as exc:
            logger.warning("LLM cleanup failed; falling back to heuristics: %s", exc)
            title = create_title(raw_text)
            summary = create_summary(raw_text)
            tags = ensure_default_tag(classify_tags(raw_text))
    else:
        title = create_title(raw_text)
        summary = create_summary(raw_text)
        tags = ensure_default_tag(classify_tags(raw_text))
    idea_id = uuid4().hex[:10]
    metadata = {"source": payload.source, "user_id": payload.user_id}

    try:
        issue_url = await create_issue(
            title=title,
            summary=summary,
            tags=tags,
            original_text=payload.text,
            metadata=metadata,
        )
    except Exception as exc:
        logger.exception("Failed to create GitHub issue: %s", exc)
        return

    logger.info(
        "Created idea response (id=%s, title=%s, tags=%s, url=%s)",
        idea_id,
        title,
        tags,
        issue_url,
    )

    return IdeaResponse(title=title, summary=summary, tags=tags, url=issue_url)
