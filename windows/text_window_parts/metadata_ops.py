from typing import Any, List

from utils.due_date import normalize_due_iso
from utils.tag_ops import normalize_tags


def set_title_and_tags(window: Any, title: str, tags: List[str]) -> None:
    """ノートメタ（title/tags）をまとめて更新する。"""
    normalized_title = str(title or "").strip()
    normalized_tags = normalize_tags(tags or [])

    title_changed = window.title != normalized_title
    tags_changed = window.tags != normalized_tags
    if not title_changed and not tags_changed:
        return

    services = window._runtime_services() if hasattr(window, "_runtime_services") else None
    use_macro = bool(
        title_changed and tags_changed and services is not None and services.begin_undo_macro("Update Note Metadata")
    )
    try:
        if title_changed:
            window.set_undoable_property("title", normalized_title, "update_text")
        if tags_changed:
            window.set_undoable_property("tags", normalized_tags, "update_text")
        window._touch_updated_at()
    finally:
        if use_macro and services is not None:
            services.end_undo_macro()


def set_tags(window: Any, tags: List[str]) -> None:
    """タグのみを正規化して更新する。"""
    normalized_tags = normalize_tags(tags or [])
    if list(getattr(window, "tags", []) or []) == normalized_tags:
        return
    window.set_undoable_property("tags", normalized_tags, "update_text")
    window._touch_updated_at()


def set_starred(window: Any, value: bool) -> None:
    """スター状態を更新する。"""
    new_value = bool(value)
    if bool(window.is_starred) == new_value:
        return
    window.set_undoable_property("is_starred", new_value, "update_text")
    window._touch_updated_at()


def set_archived(window: Any, value: bool) -> None:
    """アーカイブ状態を更新する。"""
    new_value = bool(value)
    if bool(getattr(window, "is_archived", False)) == new_value:
        return
    window.set_undoable_property("is_archived", new_value, "update_text")
    window._touch_updated_at()


def set_due_at(window: Any, value: str) -> None:
    """期限を設定する（内部保存は YYYY-MM-DDT00:00:00）。"""
    normalized = normalize_due_iso(value)
    if normalized is None:
        return
    current_due = str(getattr(window, "due_at", "") or "")
    current_precision = str(getattr(window, "due_precision", "date") or "date").strip().lower()
    current_time = str(getattr(window, "due_time", "") or "")
    current_timezone = str(getattr(window, "due_timezone", "") or "")
    if current_due == normalized and current_precision == "date" and not current_time and not current_timezone:
        return
    if current_due != normalized:
        window.set_undoable_property("due_at", normalized, "update_text")
    if current_precision != "date":
        window.set_undoable_property("due_precision", "date", None)
    if current_time:
        window.set_undoable_property("due_time", "", None)
    if current_timezone:
        window.set_undoable_property("due_timezone", "", None)
    window._touch_updated_at()


def clear_due_at(window: Any) -> None:
    """期限を解除する。"""
    has_due = bool(str(getattr(window, "due_at", "") or ""))
    has_time = bool(str(getattr(window, "due_time", "") or ""))
    has_timezone = bool(str(getattr(window, "due_timezone", "") or ""))
    precision = str(getattr(window, "due_precision", "date") or "date").strip().lower()
    if not has_due and not has_time and not has_timezone and precision == "date":
        return
    if has_due:
        window.set_undoable_property("due_at", "", "update_text")
    if has_time:
        window.set_undoable_property("due_time", "", None)
    if has_timezone:
        window.set_undoable_property("due_timezone", "", None)
    if precision != "date":
        window.set_undoable_property("due_precision", "date", None)
    window._touch_updated_at()
