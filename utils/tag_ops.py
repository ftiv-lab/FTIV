from __future__ import annotations

from typing import Any, Iterable, Sequence


def normalize_tags(raw_tags: Iterable[Any]) -> list[str]:
    """Normalize tags while preserving the first seen display case/order."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_tags:
        tag = str(raw or "").strip()
        key = tag.lower()
        if not tag or key in seen:
            continue
        out.append(tag)
        seen.add(key)
    return out


def parse_tags_csv(raw: str) -> list[str]:
    """Parse comma-separated tag text and return normalized tags."""
    return normalize_tags(str(raw or "").split(","))


def merge_tags(existing: Sequence[str], add_tags: Sequence[str], remove_tags: Sequence[str]) -> list[str]:
    """Merge add/remove operations onto existing tags.

    Remove wins when the same logical tag appears in both add/remove.
    """
    base = normalize_tags(existing)
    add = normalize_tags(add_tags)
    remove = normalize_tags(remove_tags)

    remove_keys = {tag.lower() for tag in remove}
    add = [tag for tag in add if tag.lower() not in remove_keys]

    merged: list[str] = []
    seen: set[str] = set()

    for tag in base:
        key = tag.lower()
        if key in remove_keys or key in seen:
            continue
        merged.append(tag)
        seen.add(key)

    for tag in add:
        key = tag.lower()
        if key in remove_keys or key in seen:
            continue
        merged.append(tag)
        seen.add(key)

    return merged
