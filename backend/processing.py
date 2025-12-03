from __future__ import annotations

import re
from collections import OrderedDict

# Simple keyword categories for tag classification; order matters for stability.
CATEGORY_KEYWORDS = OrderedDict(
    {
        "dev": ["code", "script", "api", "automation", "bot", "setup"],
        "product": ["idea", "app", "feature", "product", "startup"],
        "pain": ["pain", "annoying", "frustrating", "slow"],
        "snow": ["snow", "ski", "board", "gear"],
    }
)


def create_title(text: str) -> str:
    """Derive a lightweight title from the first sentence."""
    clean_text = (text or "").strip()
    if not clean_text:
        return "Untitled idea"

    # Grab the first sentence-like chunk when possible.
    sentences = re.split(r"[.!?]+", clean_text, maxsplit=1)
    candidate = sentences[0].strip() if sentences else clean_text
    if not candidate:
        candidate = clean_text

    # Normalize capitalization and length.
    candidate = candidate[0].upper() + candidate[1:] if candidate else "Idea"
    if len(candidate) > 60:
        candidate = candidate[:60].rstrip()

    return candidate


def create_summary(text: str) -> str:
    """Return a short summary of the text."""
    clean_text = (text or "").strip()
    if len(clean_text) <= 200:
        return clean_text

    snippet = clean_text[:120].rstrip()
    return f"{snippet}..."


def classify_tags(text: str) -> list[str]:
    """Assign tags based on simple keyword matching."""
    lowered = (text or "").lower()
    tags = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(category)

    return tags or ["misc"]
