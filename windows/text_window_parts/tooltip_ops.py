from __future__ import annotations

from typing import Any, List

from utils.due_date import classify_due, format_due_for_display
from utils.translator import tr


def classify_due_state(window: Any) -> str:
    raw_due = getattr(window, "due_at", "")
    due_at = str(raw_due).strip() if isinstance(raw_due, str) else ""
    if not due_at:
        return ""
    try:
        return str(
            classify_due(
                due_at,
                due_time=str(getattr(window, "due_time", "") or ""),
                due_timezone=str(getattr(window, "due_timezone", "") or ""),
                due_precision=str(getattr(window, "due_precision", "date") or "date"),
            )
        )
    except Exception:
        return ""


def build_overlay_meta_tooltip_lines(window: Any) -> List[str]:
    lines: List[str] = []

    title = str(getattr(window, "title", "") or "").strip()
    if title:
        lines.append(f"{tr('label_note_title')}: {title}")

    if window.is_task_mode():
        done, total = window._task_progress_counts()
        lines.append(str(tr("label_task_progress_fmt")).format(done=done, total=total))

    raw_due = getattr(window, "due_at", "")
    due_at = str(raw_due).strip() if isinstance(raw_due, str) else ""
    if due_at:
        due_display = format_due_for_display(
            due_at,
            due_time=str(getattr(window, "due_time", "") or ""),
            due_timezone=str(getattr(window, "due_timezone", "") or ""),
            due_precision=str(getattr(window, "due_precision", "date") or "date"),
        )
        if due_display:
            lines.append(f"{tr('label_note_due_at')}: {due_display}")
        due_state = classify_due_state(window)
        if due_state == "today":
            lines.append(tr("text_meta_due_today"))
        elif due_state == "overdue":
            lines.append(tr("text_meta_due_overdue"))

    raw_tags = getattr(window, "tags", [])
    tags = [str(tag).strip() for tag in raw_tags] if isinstance(raw_tags, list) else []
    tags = [tag for tag in tags if tag]
    if tags:
        lines.append(f"{tr('label_note_tags')}: {', '.join(tags)}")

    if bool(getattr(window, "is_starred", False)):
        lines.append(f"★ {tr('text_meta_starred')}")
    if bool(getattr(window, "is_archived", False)):
        lines.append(tr("text_meta_archived"))
    return lines


def refresh_overlay_meta_tooltip(window: Any) -> None:
    prev_append = str(getattr(window, "_overlay_meta_tooltip_append", "") or "")
    try:
        current = str(window.toolTip() or "")
    except Exception:
        return

    base = current
    if prev_append and current.endswith(prev_append):
        base = current[: -len(prev_append)]
    base = base.rstrip()

    lines = window._build_overlay_meta_tooltip_lines()
    if not lines:
        try:
            window.setToolTip(base)
        except Exception:
            pass
        window._overlay_meta_tooltip_append = ""
        return

    suffix = "\n".join(lines)
    append = f"\n\n{suffix}" if base else suffix
    try:
        window.setToolTip(base + append)
        window._overlay_meta_tooltip_append = append
    except Exception:
        window._overlay_meta_tooltip_append = ""
