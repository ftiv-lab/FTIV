"""tests/test_main_window_context_menu_routing.py

MainWindow の右クリックメニュー委譲（選択中ウィンドウ優先）を検証する。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QPoint

from ui.main_window import MainWindow


class _Rect:
    def __init__(self, contains_result: bool) -> None:
        self._contains_result = contains_result

    def contains(self, _pos: QPoint) -> bool:
        return self._contains_result


class _SelectedWindowStub:
    def __init__(self, *, visible: bool = True, contains_cursor: bool = True) -> None:
        self._visible = visible
        self._contains_cursor = contains_cursor
        self.last_context_pos: QPoint | None = None

    def isVisible(self) -> bool:
        return self._visible

    def frameGeometry(self) -> _Rect:
        return _Rect(self._contains_cursor)

    def mapFromGlobal(self, pos: QPoint) -> QPoint:
        return QPoint(pos.x() - 5, pos.y() - 7)

    def show_context_menu(self, pos: QPoint) -> None:
        self.last_context_pos = QPoint(pos)


def _make_main(selected_window: object | None) -> SimpleNamespace:
    menu_manager = MagicMock()
    return SimpleNamespace(
        last_selected_window=selected_window,
        menu_manager=menu_manager,
        mapToGlobal=lambda p: QPoint(p),
        _try_forward_context_menu_to_selected_window=lambda pos: (
            MainWindow._try_forward_context_menu_to_selected_window(_make_main(selected_window), pos)
        ),
    )


def test_try_forward_context_menu_to_selected_window_forwards_when_cursor_is_inside() -> None:
    selected = _SelectedWindowStub(visible=True, contains_cursor=True)
    mw = _make_main(selected)

    forwarded = MainWindow._try_forward_context_menu_to_selected_window(mw, QPoint(100, 200))

    assert forwarded is True
    assert selected.last_context_pos == QPoint(95, 193)


def test_try_forward_context_menu_to_selected_window_returns_false_when_cursor_is_outside() -> None:
    selected = _SelectedWindowStub(visible=True, contains_cursor=False)
    mw = _make_main(selected)

    forwarded = MainWindow._try_forward_context_menu_to_selected_window(mw, QPoint(100, 200))

    assert forwarded is False
    assert selected.last_context_pos is None


def test_show_context_menu_uses_main_menu_when_not_forwarded() -> None:
    mw = _make_main(None)

    MainWindow.show_context_menu(mw, QPoint(11, 22))

    mw.menu_manager.show_context_menu.assert_called_once_with(QPoint(11, 22))


def test_show_context_menu_skips_main_menu_when_forwarded() -> None:
    mw = _make_main(None)
    mw._try_forward_context_menu_to_selected_window = lambda _pos: True

    MainWindow.show_context_menu(mw, QPoint(11, 22))

    mw.menu_manager.show_context_menu.assert_not_called()
