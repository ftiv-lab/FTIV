from __future__ import annotations

from datetime import date, datetime
from typing import Literal

DueState = Literal["today", "overdue", "upcoming", "none", "invalid"]


def normalize_due_iso(value: str) -> str | None:
    """Normalize due input into internal ISO (YYYY-MM-DDT00:00:00)."""
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 10:
            due_day = datetime.strptime(raw, "%Y-%m-%d").date()
        else:
            due_day = datetime.fromisoformat(raw).date()
        return f"{due_day.isoformat()}T00:00:00"
    except Exception:
        return None


def normalize_due_input_allow_empty(value: str) -> str | None:
    """Normalize due input and keep empty input as clear marker."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    return normalize_due_iso(raw)


def display_due_iso(value: str) -> str:
    """Convert internal due ISO text into UI text (YYYY-MM-DD)."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).date().isoformat()
    except Exception:
        return raw


def classify_due(value: str, today: date | None = None) -> DueState:
    """Classify due text for visual emphasis."""
    raw = str(value or "").strip()
    if not raw:
        return "none"
    normalized = normalize_due_iso(raw)
    if normalized is None:
        return "invalid"
    due_day = datetime.fromisoformat(normalized).date()
    base_day = today or date.today()
    if due_day == base_day:
        return "today"
    if due_day < base_day:
        return "overdue"
    return "upcoming"
