from typing import Any

from PySide6.QtCore import QPoint, Qt


def after_set_selected(window: Any, *, previous: bool, current: bool) -> None:
    if previous != current:
        window.update_text()


def mouse_press(window: Any, event: Any) -> None:
    if event.button() == Qt.MouseButton.LeftButton:
        window._task_press_pos = event.position().toPoint()


def mouse_release_should_toggle(window: Any, event: Any) -> bool:
    if event.button() != Qt.MouseButton.LeftButton or not window.is_task_mode():
        return False
    release_pos = event.position().toPoint()
    press_pos = getattr(window, "_task_press_pos", None)
    if press_pos is None:
        return False
    dist = (release_pos - press_pos).manhattanLength()
    if dist >= 10:
        return False
    idx = hit_test_task_checkbox(window, release_pos)
    if idx < 0:
        return False
    window._toggle_task_line_by_index(idx)
    return True


def mouse_move(window: Any, event: Any) -> None:
    if window.is_task_mode() and not window.is_dragging:
        pos = event.position().toPoint()
        idx = hit_test_task_checkbox(window, pos)
        if idx >= 0:
            window.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            window.unsetCursor()


def hit_test_task_checkbox(window: Any, pos: QPoint) -> int:
    if not window.is_task_mode() or window.is_vertical:
        return -1

    renderer = getattr(window, "renderer", None)
    if renderer is None:
        return -1

    rects = renderer.get_task_line_rects(window)
    for i, rect in enumerate(rects):
        if rect.contains(pos):
            return i
    return -1
