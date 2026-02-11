from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

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


def normalize_due_time(value: str) -> str | None:
    """Normalize due time input into HH:MM (24h). Empty input stays empty."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.strptime(raw, "%H:%M")
        return parsed.strftime("%H:%M")
    except Exception:
        return None


def is_valid_timezone(value: str) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return True
    try:
        ZoneInfo(raw)
        return True
    except Exception:
        return False


def compose_due_datetime(
    due_at: str,
    due_time: str = "",
    due_timezone: str = "",
    due_precision: str = "date",
) -> datetime | None:
    normalized_date = normalize_due_iso(due_at)
    if normalized_date is None:
        return None

    due_day = datetime.fromisoformat(normalized_date).date()
    precision = str(due_precision or "date").strip().lower()
    if precision != "datetime":
        return datetime(due_day.year, due_day.month, due_day.day, 0, 0)

    normalized_time = normalize_due_time(due_time)
    if normalized_time in (None, ""):
        return datetime(due_day.year, due_day.month, due_day.day, 0, 0)

    hour_text, minute_text = normalized_time.split(":")
    due_local = datetime(due_day.year, due_day.month, due_day.day, int(hour_text), int(minute_text))

    tz_name = str(due_timezone or "").strip()
    if not tz_name:
        return due_local
    try:
        zone = ZoneInfo(tz_name)
        return due_local.replace(tzinfo=zone).astimezone().replace(tzinfo=None)
    except Exception:
        return None


def display_due_iso(value: str) -> str:
    """Convert internal due ISO text into UI text (YYYY-MM-DD)."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).date().isoformat()
    except Exception:
        return raw


def format_due_for_display(
    due_at: str,
    due_time: str = "",
    due_timezone: str = "",
    due_precision: str = "date",
) -> str:
    date_text = display_due_iso(due_at)
    if not date_text:
        return ""

    precision = str(due_precision or "date").strip().lower()
    if precision != "datetime":
        return date_text

    normalized_time = normalize_due_time(due_time)
    if normalized_time in (None, ""):
        return date_text

    tz_name = str(due_timezone or "").strip()
    if tz_name:
        return f"{date_text} {normalized_time} ({tz_name})"
    return f"{date_text} {normalized_time}"


def classify_due(
    value: str,
    today: date | None = None,
    *,
    due_time: str = "",
    due_timezone: str = "",
    due_precision: str = "date",
    now: datetime | None = None,
) -> DueState:
    """Classify due text for visual emphasis."""
    raw = str(value or "").strip()
    if not raw:
        return "none"

    precision = str(due_precision or "date").strip().lower()
    if precision == "datetime":
        due_dt = compose_due_datetime(raw, due_time=due_time, due_timezone=due_timezone, due_precision=precision)
        if due_dt is None:
            return "invalid"
        base_now = now or datetime.now()
        if due_dt.date() == base_now.date():
            return "overdue" if due_dt < base_now else "today"
        return "overdue" if due_dt < base_now else "upcoming"

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
