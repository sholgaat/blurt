from __future__ import annotations

import re
from collections import OrderedDict
from typing import Iterable, List

PREFIX_PATTERN = re.compile(r"^(pain|idea)\s*:\s*", flags=re.IGNORECASE)

# Simple keyword categories for tag classification; order matters for stability.
CATEGORY_KEYWORDS = OrderedDict(
    {
        "dev": [
            "code",
            "script",
            "api",
            "automation",
            "bot",
            "setup",
            "dev",
            "ci",
            "infra",
        ],
        "product": ["idea", "app", "feature", "product", "startup", "tool"],
        "pain": [
            "pain",
            "annoying",
            "frustrating",
            "slow",
            "hate",
            "irritating",
        ],
        "snow": [
            "snow",
            "ski",
            "board",
            "snowboard",
            "powder",
            "nozawa",
            "resort",
        ],
    }
)


def _strip_known_prefix(text: str) -> str:
    return PREFIX_PATTERN.sub("", text, count=1)


def _clean_text(text: str) -> str:
    return (text or "").strip()


def create_title(text: str) -> str:
    """Derive a lightweight title from the first sentence."""
    clean_text = _clean_text(text)
    if not clean_text:
        return "Untitled idea"

    clean_text = _strip_known_prefix(clean_text).strip() or clean_text

    sentences = re.split(r"[.!?]+", clean_text, maxsplit=1)
    candidate = sentences[0].strip() if sentences else clean_text
    if not candidate:
        candidate = clean_text

    candidate = candidate[0].upper() + candidate[1:] if candidate else "Idea"
    if len(candidate) > 80:
        candidate = candidate[:80].rstrip()

    return candidate or "Untitled idea"


def create_summary(text: str) -> str:
    """Return a short summary of the text."""
    clean_text = _clean_text(text)
    stripped = _strip_known_prefix(clean_text).strip() or clean_text
    if len(stripped) <= 200:
        return stripped

    snippet = stripped[:200].rstrip()
    return f"{snippet}..."


def classify_tags(text: str) -> list[str]:
    """Assign tags based on simple keyword matching."""
    lowered = (text or "").lower()
    tags = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(category)

    return tags


def ensure_default_tag(tags: Iterable[str]) -> List[str]:
    collected = list(tags)
    return collected if collected else ["misc"]
