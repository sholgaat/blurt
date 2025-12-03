from __future__ import annotations

from typing import Optional
from uuid import uuid4
import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

from backend.processing import classify_tags, create_summary, create_title

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
def create_idea(payload: IdeaRequest) -> IdeaResponse:
    logger.info("Creating idea (user=%s, source=%s): %s", payload.user_id, payload.source, payload.text)
    title = create_title(payload.text)
    summary = create_summary(payload.text)
    tags = classify_tags(payload.text)
    idea_id = uuid4().hex[:10]
    fake_url = f"https://example.com/idea/{idea_id}"
    logger.info(
        "Created idea response (id=%s, title=%s, tags=%s, url=%s)",
        idea_id,
        title,
        tags,
        fake_url,
    )

    return IdeaResponse(title=title, summary=summary, tags=tags, url=fake_url)
