from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from blurt.backend import github_client
from blurt.backend.github_client import create_issue
from blurt.backend.llm import LlmError, call_ai_cleanup
from blurt.backend.settings import get_backend_settings, validate_github_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_IDEA_LENGTH = 4096


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    validate_github_config(get_backend_settings())
    github_client.http_client = httpx.AsyncClient()
    try:
        yield
    finally:
        if github_client.http_client:
            await github_client.http_client.aclose()
            github_client.http_client = None


app = FastAPI(title="Blurt Backend", version=os.getenv("APP_VERSION", "0.0.0"), lifespan=lifespan)


class IdeaRequest(BaseModel):
    text: str = Field(
        ...,
        description="Raw idea text from the user",
        min_length=1,
        max_length=MAX_IDEA_LENGTH,
    )
    user_id: str | None = Field(
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
async def create_idea_endpoint(payload: IdeaRequest) -> IdeaResponse:
    logger.info(
        "Creating idea (user=%s, source=%s)",
        payload.user_id,
        payload.source,
    )

    try:
        llm_result = await call_ai_cleanup(payload.text)
    except LlmError as exc:
        logger.error("LLM cleanup failed; returning error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Idea processing is temporarily unavailable. Please try again later.",
        ) from exc

    title = llm_result.title
    summary = llm_result.summary
    tags = llm_result.tags
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
        raise HTTPException(
            status_code=502,
            detail="Failed to create GitHub issue. Please try again later.",
        ) from exc

    logger.info(
        "Created idea (title=%s, tags=%s, url=%s)",
        title,
        tags,
        issue_url,
    )

    return IdeaResponse(title=title, summary=summary, tags=tags, url=issue_url)
