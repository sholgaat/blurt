from __future__ import annotations

import logging
import os
from typing import Iterable, Mapping, Optional

import httpx

logger = logging.getLogger(__name__)


def _get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required for GitHub access.")
    return value


def _build_issue_body(
    summary: str,
    tags: Iterable[str],
    original_text: str,
    metadata: Optional[Mapping[str, Optional[str]]] = None,
) -> str:
    quoted = "\n".join(f"> {line}" for line in (original_text or "").splitlines()) or "> (empty)"
    tag_list = ", ".join(tags) if tags else "none"

    body_sections = [
        "## Summary",
        summary or "(no summary)",
        "",
        "## Tags",
        tag_list,
        "",
        "## Original Note",
        quoted,
    ]

    metadata_entries = []
    if metadata:
        for key, value in metadata.items():
            if value:
                metadata_entries.append(f"- **{key}**: {value}")

    if metadata_entries:
        body_sections.extend(["", "## Metadata", *metadata_entries])

    return "\n".join(body_sections)


async def create_issue(
    title: str,
    summary: str,
    tags: list[str],
    original_text: str,
    metadata: Optional[Mapping[str, Optional[str]]] = None,
) -> str:
    owner = _get_env_var("GITHUB_REPO_OWNER")
    repo = _get_env_var("GITHUB_REPO_NAME")
    token = _get_env_var("GITHUB_TOKEN")

    issue_body = _build_issue_body(summary, tags, original_text, metadata)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "title": title,
        "body": issue_body,
        "labels": tags or [],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=20.0)

    if response.status_code >= 300:
        logger.error(
            "Failed to create GitHub issue (status=%s, body=%s)",
            response.status_code,
            response.text,
        )
        response.raise_for_status()

    data = response.json()
    issue_url = data.get("html_url")
    if not issue_url:
        raise RuntimeError("GitHub response missing html_url.")
    logger.info("Created GitHub issue at %s", issue_url)
    return issue_url
