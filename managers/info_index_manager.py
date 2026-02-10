from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, List, Literal, Sequence, Tuple


@dataclass(frozen=True)
class TaskIndexItem:
    item_key: str
    window_uuid: str
    title: str
    text: str
    line_index: int
    done: bool
    tags: Tuple[str, ...]
    is_starred: bool
    created_at: str
    updated_at: str
    due_at: str
    is_archived: bool


@dataclass(frozen=True)
class NoteIndexItem:
    window_uuid: str
    title: str
    first_line: str
    content_mode: str
    tags: Tuple[str, ...]
    is_starred: bool
    created_at: str
    updated_at: str
    due_at: str
    is_archived: bool


@dataclass(frozen=True)
class InfoQuery:
    text: str = ""
    tag: str = ""
    starred_only: bool = False
    open_tasks_only: bool = False
    include_archived: bool = False
    due_filter: Literal["all", "today", "overdue", "upcoming", "dated", "undated"] = "all"
    mode_filter: Literal["all", "task", "note"] = "all"
    sort_by: Literal["updated", "due", "created", "title"] = "updated"
    sort_desc: bool = True


@dataclass(frozen=True)
class InfoStats:
    open_tasks: int = 0
    done_tasks: int = 0
    overdue_tasks: int = 0
    starred_notes: int = 0


class InfoIndexManager:
    """TextWindow群から情報管理用インデックスを構築する。"""

    @staticmethod
    def _normalize_tags(raw_tags: Any) -> Tuple[str, ...]:
        if not isinstance(raw_tags, list):
            return ()
        out: List[str] = []
        seen: set[str] = set()
        for raw in raw_tags:
            tag = str(raw or "").strip()
            key = tag.lower()
            if not tag or key in seen:
                continue
            out.append(tag)
            seen.add(key)
        return tuple(out)

    @staticmethod
    def _parse_iso(value: str) -> datetime:
        text = str(value or "").strip()
        if not text:
            return datetime.min
        try:
            return datetime.fromisoformat(text)
        except Exception:
            return datetime.min

    @staticmethod
    def _parse_due_iso(value: str) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text)
        except Exception:
            return None

    def _parse_due_for_sort(self, value: str) -> datetime:
        parsed = self._parse_due_iso(value)
        # 要件: 不正値は安全側として末尾寄せしやすい datetime.max 扱い
        return parsed if parsed is not None else datetime.max

    @staticmethod
    def _matches_mode(mode_filter: str, item_mode: str) -> bool:
        mode = str(mode_filter or "").strip().lower()
        if mode in ("", "all"):
            return True
        normalized_item = "task" if str(item_mode or "").strip().lower() == "task" else "note"
        return mode == normalized_item

    def _matches_due(self, due_filter: str, due_at: str) -> bool:
        due_mode = str(due_filter or "").strip().lower()
        if due_mode in ("", "all"):
            return True

        due_dt = self._parse_due_iso(due_at)
        if due_mode == "dated":
            return due_dt is not None
        if due_mode == "undated":
            return due_dt is None

        if due_dt is None:
            return False

        today = date.today()
        due_day = due_dt.date()
        if due_mode == "today":
            return due_day == today
        if due_mode == "overdue":
            return due_day < today
        if due_mode == "upcoming":
            return due_day > today
        return True

    @staticmethod
    def _build_display_title(title: str, first_line: str, window_uuid: str) -> str:
        if title:
            return title
        if first_line:
            return first_line
        if window_uuid:
            return f"TextWindow {window_uuid[:8]}"
        return "TextWindow"

    def build_index(self, text_windows: Sequence[Any]) -> tuple[List[TaskIndexItem], List[NoteIndexItem]]:
        task_items: List[TaskIndexItem] = []
        note_items: List[NoteIndexItem] = []

        for window in list(text_windows or []):
            if window is None:
                continue

            window_uuid = str(getattr(window, "uuid", "") or "")
            text = str(getattr(window, "text", "") or "")
            first_line = text.split("\n", 1)[0].strip() if text else ""
            title = str(getattr(window, "title", "") or "").strip()
            tags = self._normalize_tags(getattr(window, "tags", []))
            is_starred = bool(getattr(window, "is_starred", False))
            created_at = str(getattr(window, "created_at", "") or "")
            updated_at = str(getattr(window, "updated_at", "") or "")
            due_at = str(getattr(window, "due_at", "") or "")
            is_archived = bool(getattr(window, "is_archived", False))
            content_mode = str(getattr(window, "content_mode", "note") or "note").lower()
            display_title = self._build_display_title(title, first_line, window_uuid)

            note_items.append(
                NoteIndexItem(
                    window_uuid=window_uuid,
                    title=display_title,
                    first_line=first_line,
                    content_mode="task" if content_mode == "task" else "note",
                    tags=tags,
                    is_starred=is_starred,
                    created_at=created_at,
                    updated_at=updated_at,
                    due_at=due_at,
                    is_archived=is_archived,
                )
            )

            if content_mode != "task":
                continue

            if hasattr(window, "iter_task_items"):
                refs: Iterable[Any] = window.iter_task_items()
            else:
                lines = text.split("\n")
                states = list(getattr(window, "task_states", []) or [])
                refs = [
                    {
                        "line_index": i,
                        "text": lines[i],
                        "done": bool(states[i]) if i < len(states) else False,
                    }
                    for i in range(len(lines))
                ]

            for ref in refs:
                line_index = int(getattr(ref, "line_index", -1))
                task_text = str(getattr(ref, "text", "") or "")
                done = bool(getattr(ref, "done", False))
                if line_index < 0:
                    continue

                task_items.append(
                    TaskIndexItem(
                        item_key=f"{window_uuid}:{line_index}",
                        window_uuid=window_uuid,
                        title=display_title,
                        text=task_text,
                        line_index=line_index,
                        done=done,
                        tags=tags,
                        is_starred=is_starred,
                        created_at=created_at,
                        updated_at=updated_at,
                        due_at=due_at,
                        is_archived=is_archived,
                    )
                )

        task_items.sort(
            key=lambda item: (
                self._parse_iso(item.updated_at),
                self._parse_iso(item.created_at),
                item.window_uuid,
                item.line_index,
            ),
            reverse=True,
        )
        note_items.sort(
            key=lambda item: (
                self._parse_iso(item.updated_at),
                self._parse_iso(item.created_at),
                item.window_uuid,
            ),
            reverse=True,
        )
        return task_items, note_items

    @staticmethod
    def _matches_search(search: str, parts: Sequence[str]) -> bool:
        query = str(search or "").strip().lower()
        if not query:
            return True
        haystack = " ".join(str(part or "").lower() for part in parts)
        return query in haystack

    @staticmethod
    def _matches_tag(tag_filter: str, tags: Tuple[str, ...]) -> bool:
        query = str(tag_filter or "").strip().lower()
        if not query:
            return True
        return any(query in tag.lower() for tag in tags)

    def query_tasks(self, items: Sequence[TaskIndexItem], query: InfoQuery) -> List[TaskIndexItem]:
        out: List[TaskIndexItem] = []
        for item in list(items or []):
            if not query.include_archived and item.is_archived:
                continue
            if not self._matches_mode(query.mode_filter, "task"):
                continue
            if query.starred_only and not item.is_starred:
                continue
            if query.open_tasks_only and item.done:
                continue
            if not self._matches_due(query.due_filter, item.due_at):
                continue
            if not self._matches_tag(query.tag, item.tags):
                continue
            if not self._matches_search(query.text, [item.title, item.text, " ".join(item.tags)]):
                continue
            out.append(item)
        return self._sort_tasks(out, query)

    def query_notes(self, items: Sequence[NoteIndexItem], query: InfoQuery) -> List[NoteIndexItem]:
        out: List[NoteIndexItem] = []
        for item in list(items or []):
            if not query.include_archived and item.is_archived:
                continue
            if not self._matches_mode(query.mode_filter, item.content_mode):
                continue
            if query.starred_only and not item.is_starred:
                continue
            if not self._matches_due(query.due_filter, item.due_at):
                continue
            if not self._matches_tag(query.tag, item.tags):
                continue
            if not self._matches_search(query.text, [item.title, item.first_line, " ".join(item.tags)]):
                continue
            out.append(item)
        return self._sort_notes(out, query)

    def _sort_tasks(self, items: List[TaskIndexItem], query: InfoQuery) -> List[TaskIndexItem]:
        sort_by = str(query.sort_by or "updated").strip().lower()
        reverse = bool(query.sort_desc)

        if sort_by == "title":
            return sorted(
                items,
                key=lambda item: (str(item.title).lower(), item.window_uuid, item.line_index),
                reverse=reverse,
            )
        if sort_by == "due":
            return sorted(
                items,
                key=lambda item: (
                    self._parse_due_for_sort(item.due_at),
                    self._parse_iso(item.updated_at),
                    item.window_uuid,
                    item.line_index,
                ),
                reverse=reverse,
            )
        if sort_by == "created":
            return sorted(
                items,
                key=lambda item: (
                    self._parse_iso(item.created_at),
                    self._parse_iso(item.updated_at),
                    item.window_uuid,
                    item.line_index,
                ),
                reverse=reverse,
            )
        # default: updated
        return sorted(
            items,
            key=lambda item: (
                self._parse_iso(item.updated_at),
                self._parse_iso(item.created_at),
                item.window_uuid,
                item.line_index,
            ),
            reverse=reverse,
        )

    def _sort_notes(self, items: List[NoteIndexItem], query: InfoQuery) -> List[NoteIndexItem]:
        sort_by = str(query.sort_by or "updated").strip().lower()
        reverse = bool(query.sort_desc)

        if sort_by == "title":
            return sorted(items, key=lambda item: (str(item.title).lower(), item.window_uuid), reverse=reverse)
        if sort_by == "due":
            return sorted(
                items,
                key=lambda item: (
                    self._parse_due_for_sort(item.due_at),
                    self._parse_iso(item.updated_at),
                    item.window_uuid,
                ),
                reverse=reverse,
            )
        if sort_by == "created":
            return sorted(
                items,
                key=lambda item: (
                    self._parse_iso(item.created_at),
                    self._parse_iso(item.updated_at),
                    item.window_uuid,
                ),
                reverse=reverse,
            )
        # default: updated
        return sorted(
            items,
            key=lambda item: (
                self._parse_iso(item.updated_at),
                self._parse_iso(item.created_at),
                item.window_uuid,
            ),
            reverse=reverse,
        )

    def build_stats(self, tasks: Sequence[TaskIndexItem], notes: Sequence[NoteIndexItem]) -> InfoStats:
        open_tasks = 0
        done_tasks = 0
        overdue_tasks = 0
        today = date.today()

        for item in list(tasks or []):
            if item.done:
                done_tasks += 1
                continue
            open_tasks += 1
            due_dt = self._parse_due_iso(item.due_at)
            if due_dt is not None and due_dt.date() < today:
                overdue_tasks += 1

        starred_notes = sum(1 for note in list(notes or []) if bool(note.is_starred))
        return InfoStats(
            open_tasks=open_tasks,
            done_tasks=done_tasks,
            overdue_tasks=overdue_tasks,
            starred_notes=starred_notes,
        )
