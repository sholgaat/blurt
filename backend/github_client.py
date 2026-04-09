from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping

import httpx

from backend.settings import get_backend_settings

logger = logging.getLogger(__name__)

http_client: httpx.AsyncClient | None = None


def _build_issue_body(
    summary: str,
    tags: Iterable[str],
    original_text: str,
    metadata: Mapping[str, str] | None = None,
) -> str:
    quoted = "\n".join(f"> {line}" for line in (original_text or "").splitlines())

    body_sections = [
        "## Summary",
        summary,
        "",
        "## Original Note",
        quoted,
    ]

    metadata_entries = []
    if metadata:
        for key, value in metadata.items():
            if value:
                metadata_entries.append(f"- **{key}**: {value}")

    tag_list = ", ".join(tags)
    if tag_list:
        metadata_entries.append(f"- **tags**: {tag_list}")

    if metadata_entries:
        body_sections.extend(["", "## Metadata", *metadata_entries])

    return "\n".join(body_sections)


def _prepare_labels(
    tags: Iterable[str], metadata: Mapping[str, str] | None
) -> list[str]:
    labels = list(dict.fromkeys(tags or []))
    source = (metadata or {}).get("source", "")
    if isinstance(source, str) and source.strip():
        source_label = f"source:{source.strip().lower()}"
        if source_label not in labels:
            labels.append(source_label)
    return labels


async def create_issue(
    title: str,
    summary: str,
    tags: list[str],
    original_text: str,
    metadata: Mapping[str, str] | None = None,
) -> str:
    cfg = get_backend_settings()
    owner = cfg.github_repo_owner
    repo = cfg.github_repo_name
    token = cfg.github_token
    dry_run = cfg.dry_run

    if not owner or not repo or not token:
        raise RuntimeError(
            "GITHUB_REPO_OWNER, GITHUB_REPO_NAME, and GITHUB_TOKEN must all be set."
        )

    issue_body = _build_issue_body(summary, tags, original_text, metadata)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    labels = _prepare_labels(tags, metadata)
    payload = {
        "title": title,
        "body": issue_body,
        "labels": labels,
    }

    if dry_run:
        logger.info("Dry run enabled - not creating GitHub issue.")
        logger.info("Issue payload: %s", payload)
        return "https://example.com/dry-run-issue"

    if http_client is None:
        raise RuntimeError(
            "GitHub HTTP client not initialized. Is the app lifespan running?"
        )

    response = await http_client.post(url, json=payload, headers=headers, timeout=20.0)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.error(
            "Failed to create GitHub issue (status=%s, body=%s)",
            response.status_code,
            response.text,
        )
        raise

    data = response.json()
    issue_url = data.get("html_url")
    if not issue_url:
        raise RuntimeError("GitHub response missing html_url.")
    logger.info("Created GitHub issue at %s", issue_url)
    return issue_url
