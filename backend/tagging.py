from __future__ import annotations

from typing import Iterable, List


def ensure_default_tag(tags: Iterable[str]) -> List[str]:
    """Ensure at least one tag is present."""
    unique: List[str] = []
    for tag in tags:
        if tag and tag not in unique:
            unique.append(tag)
    return unique or ["misc"]
