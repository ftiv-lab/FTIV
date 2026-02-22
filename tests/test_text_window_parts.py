from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QPoint, QRect, Qt

from windows.text_window_parts import metadata_ops, selection_ops, task_ops


class _DummyServices:
    def __init__(self, begin_returns: bool = True) -> None:
        self.begin_calls: list[str] = []
        self.end_calls = 0
        self.begin_returns = begin_returns

    def begin_undo_macro(self, label: str) -> bool:
        self.begin_calls.append(label)
        return self.begin_returns

    def end_undo_macro(self) -> None:
        self.end_calls += 1


@dataclass
class _TaskItem:
    done: bool


class _DummyWindow:
    def __init__(
        self,
        *,
        text: str = "a\nb\nc",
        task_states: list[bool] | None = None,
        task_mode: bool = True,
    ) -> None:
        self.text = text
        self.task_states = task_states if task_states is not None else [False, False, False]
        self._task_mode = task_mode
        self._touch_count = 0
        self.undo_calls: list[tuple[str, Any, Any]] = []

        self.title = "old"
        self.tags = ["old-tag"]
        self.is_starred = False
        self.is_archived = False
        self.due_at = ""
        self.due_precision = "date"
        self.due_time = ""
        self.due_timezone = ""
        self.uuid = "dummy-window"

        self._task_press_pos: QPoint | None = None
        self.is_vertical = False
        self.is_dragging = False
        self.cursor_set = False
        self.cursor_unset = False
        self.toggled_indices: list[int] = []

        self._services = _DummyServices()
        self.renderer = None

    def _runtime_services(self) -> _DummyServices:
        return self._services

    def set_undoable_property(self, key: str, value: Any, action: Any = None) -> None:
        self.undo_calls.append((key, value, action))
        setattr(self, key, value)

    def _touch_updated_at(self) -> None:
        self._touch_count += 1

    def is_task_mode(self) -> bool:
        return self._task_mode

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        if not text:
            return []
        return str(text).splitlines()

    @staticmethod
    def _normalize_task_states(states: list[bool], total: int) -> list[bool]:
        normalized = [bool(v) for v in list(states or [])[:total]]
        if len(normalized) < total:
            normalized.extend([False] * (total - len(normalized)))
        return normalized

    def get_task_line_state(self, index: int) -> bool:
        return task_ops.get_task_line_state(self, index)

    def set_task_line_state(self, index: int, done: bool) -> None:
        task_ops.set_task_line_state(self, index, done)

    def toggle_task_line_state(self, index: int) -> None:
        task_ops.toggle_task_line_state(self, index)

    def _toggle_task_line_by_index(self, idx: int) -> None:
        self.toggled_indices.append(idx)

    def update_text(self) -> None:
        self._touch_count += 1

    def setCursor(self, _cursor: Any) -> None:
        self.cursor_set = True

    def unsetCursor(self) -> None:
        self.cursor_unset = True


class _PointWrapper:
    def __init__(self, point: QPoint) -> None:
        self._point = point

    def toPoint(self) -> QPoint:
        return self._point


class _MouseEventStub:
    def __init__(self, button: Qt.MouseButton, point: QPoint) -> None:
        self._button = button
        self._point = point

    def button(self) -> Qt.MouseButton:
        return self._button

    def position(self) -> _PointWrapper:
        return _PointWrapper(self._point)


class _RendererStub:
    def __init__(self, rects: list[QRect]) -> None:
        self._rects = rects

    def get_task_line_rects(self, _window: Any) -> list[QRect]:
        return self._rects


def test_metadata_set_title_and_tags_uses_macro_and_touches_once() -> None:
    window = _DummyWindow(task_mode=False)
    window._services = _DummyServices(begin_returns=True)

    metadata_ops.set_title_and_tags(window, "new title", ["a", "A", "b"])

    assert ("title", "new title", "update_text") in window.undo_calls
    assert ("tags", ["a", "b"], "update_text") in window.undo_calls
    assert window._services.begin_calls == ["Update Note Metadata"]
    assert window._services.end_calls == 1
    assert window._touch_count == 1


def test_metadata_set_title_and_tags_noop_when_unchanged() -> None:
    window = _DummyWindow(task_mode=False)
    window.title = "same"
    window.tags = ["x", "y"]

    metadata_ops.set_title_and_tags(window, " same ", ["x", "y"])

    assert window.undo_calls == []
    assert window._touch_count == 0


def test_metadata_set_due_at_normalizes_and_clears_datetime_fields() -> None:
    window = _DummyWindow(task_mode=False)
    window.due_at = "2026-03-10T00:00:00"
    window.due_precision = "datetime"
    window.due_time = "09:30"
    window.due_timezone = "Asia/Tokyo"

    metadata_ops.set_due_at(window, "2026-03-10")

    assert ("due_precision", "date", None) in window.undo_calls
    assert ("due_time", "", None) in window.undo_calls
    assert ("due_timezone", "", None) in window.undo_calls
    assert window.due_precision == "date"
    assert window.due_time == ""
    assert window.due_timezone == ""
    assert window._touch_count == 1


def test_metadata_clear_due_at_noop_when_empty() -> None:
    window = _DummyWindow(task_mode=False)
    metadata_ops.clear_due_at(window)
    assert window.undo_calls == []
    assert window._touch_count == 0


def test_metadata_clear_due_at_clears_all_due_fields() -> None:
    window = _DummyWindow(task_mode=False)
    window.due_at = "2026-03-10T00:00:00"
    window.due_precision = "datetime"
    window.due_time = "10:00"
    window.due_timezone = "Asia/Tokyo"

    metadata_ops.clear_due_at(window)

    assert ("due_at", "", "update_text") in window.undo_calls
    assert ("due_time", "", None) in window.undo_calls
    assert ("due_timezone", "", None) in window.undo_calls
    assert ("due_precision", "date", None) in window.undo_calls
    assert window._touch_count == 1


def test_task_ops_progress_and_state_updates() -> None:
    window = _DummyWindow(text="a\nb\nc", task_states=[True, False, True], task_mode=True)

    assert task_ops.get_task_progress(window) == (2, 3)
    assert task_ops.get_task_line_state(window, 1) is False

    task_ops.set_task_line_state(window, 1, True)
    assert window.task_states == [True, True, True]
    assert window._touch_count == 1


def test_task_ops_bulk_set_task_done_ignores_duplicates_and_out_of_range() -> None:
    window = _DummyWindow(text="a\nb\nc", task_states=[False, False, False], task_mode=True)

    task_ops.bulk_set_task_done(window, [0, 0, 2, 9, -1], True)

    assert window.task_states == [True, False, True]
    assert window._touch_count == 1


def test_task_ops_complete_and_uncomplete_all() -> None:
    window = _DummyWindow(text="a\nb", task_states=[False, True], task_mode=True)

    task_ops.complete_all_tasks(window)
    assert window.task_states == [True, True]

    task_ops.uncomplete_all_tasks(window)
    assert window.task_states == [False, False]


def test_task_ops_iter_items_returns_empty_for_note_mode() -> None:
    window = _DummyWindow(task_mode=False)
    assert task_ops.iter_task_items(window) == []


def test_task_ops_iter_items_builds_task_line_refs() -> None:
    window = _DummyWindow(text="x\ny", task_states=[True, False], task_mode=True)

    items = task_ops.iter_task_items(window)

    assert len(items) == 2
    assert items[0].line_index == 0
    assert items[0].done is True
    assert items[1].text == "y"


def test_selection_after_set_selected_updates_only_on_change() -> None:
    window = _DummyWindow()
    before = window._touch_count

    selection_ops.after_set_selected(window, previous=True, current=True)
    assert window._touch_count == before

    selection_ops.after_set_selected(window, previous=False, current=True)
    assert window._touch_count == before + 1


def test_selection_mouse_release_toggles_when_click_inside_checkbox() -> None:
    window = _DummyWindow(task_mode=True)
    window.renderer = _RendererStub([QRect(0, 0, 20, 20)])
    press = _MouseEventStub(Qt.MouseButton.LeftButton, QPoint(5, 5))
    release = _MouseEventStub(Qt.MouseButton.LeftButton, QPoint(6, 6))

    selection_ops.mouse_press(window, press)
    toggled = selection_ops.mouse_release_should_toggle(window, release)

    assert toggled is True
    assert window.toggled_indices == [0]


def test_selection_mouse_move_sets_and_unsets_cursor() -> None:
    window = _DummyWindow(task_mode=True)
    window.renderer = _RendererStub([QRect(0, 0, 20, 20)])

    selection_ops.mouse_move(window, _MouseEventStub(Qt.MouseButton.LeftButton, QPoint(1, 1)))
    assert window.cursor_set is True

    selection_ops.mouse_move(window, _MouseEventStub(Qt.MouseButton.LeftButton, QPoint(50, 50)))
    assert window.cursor_unset is True


def test_selection_hit_test_respects_mode_and_vertical_flag() -> None:
    window = _DummyWindow(task_mode=True)
    window.renderer = _RendererStub([QRect(0, 0, 20, 20)])

    assert selection_ops.hit_test_task_checkbox(window, QPoint(1, 1)) == 0

    window.is_vertical = True
    assert selection_ops.hit_test_task_checkbox(window, QPoint(1, 1)) == -1

    window.is_vertical = False
    window._task_mode = False
    assert selection_ops.hit_test_task_checkbox(window, QPoint(1, 1)) == -1
