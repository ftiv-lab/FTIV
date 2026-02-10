# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from utils.error_reporter import ErrorNotifyState, report_unexpected_error

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class InfoActions:
    """Infoタブ向けの操作ロジック。"""

    def __init__(self, mw: "MainWindow") -> None:
        self.mw = mw
        self._err_state = ErrorNotifyState()

    def _iter_text_windows(self) -> list[Any]:
        wm = getattr(self.mw, "window_manager", None)
        if wm is None:
            return []
        return list(getattr(wm, "text_windows", []) or [])

    def _iter_all_windows(self) -> list[Any]:
        wm = getattr(self.mw, "window_manager", None)
        if wm is None:
            return []
        text_windows = list(getattr(wm, "text_windows", []) or [])
        image_windows = list(getattr(wm, "image_windows", []) or [])
        return text_windows + image_windows

    def _find_text_window(self, window_uuid: str) -> Optional[Any]:
        target_uuid = str(window_uuid or "")
        if not target_uuid:
            return None
        for window in self._iter_text_windows():
            if str(getattr(window, "uuid", "") or "") == target_uuid:
                return window
        return None

    def _find_window(self, window_uuid: str) -> Optional[Any]:
        target_uuid = str(window_uuid or "")
        if not target_uuid:
            return None
        for window in self._iter_all_windows():
            if str(getattr(window, "uuid", "") or "") == target_uuid:
                return window
        return None

    def _refresh_info_tab(self) -> None:
        tab = getattr(self.mw, "info_tab", None)
        if tab is not None and hasattr(tab, "refresh_data"):
            tab.refresh_data()

    def focus_window(self, window_uuid: str) -> None:
        """UUID指定のウィンドウを前面化・選択する。"""
        try:
            window = self._find_window(window_uuid)
            if window is None:
                return

            if hasattr(self.mw, "window_manager"):
                self.mw.window_manager.set_selected_window(window)

            if hasattr(window, "show"):
                window.show()
            if hasattr(window, "raise_"):
                window.raise_()
            if hasattr(window, "activateWindow"):
                window.activateWindow()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to focus window", e, self._err_state)

    def toggle_task(self, item_key: str) -> None:
        """task item_key(uuid:index) を受けて完了状態をトグルする。"""
        try:
            key = str(item_key or "")
            if ":" not in key:
                return

            window_uuid, line_index_text = key.rsplit(":", 1)
            line_index = int(line_index_text)
            window = self._find_text_window(window_uuid)
            if window is None:
                return

            if hasattr(window, "toggle_task_line_state"):
                window.toggle_task_line_state(line_index)
            elif hasattr(window, "_toggle_task_line_by_index"):
                window._toggle_task_line_by_index(line_index)
            else:
                return

            if hasattr(self.mw, "window_manager"):
                self.mw.window_manager.set_selected_window(window)
            self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to toggle task", e, self._err_state)

    def set_star(self, window_uuid: str, value: bool) -> None:
        """指定ウィンドウのスター状態を設定する。"""
        try:
            window = self._find_text_window(window_uuid)
            if window is None:
                return

            if hasattr(window, "set_starred"):
                window.set_starred(bool(value))
            elif hasattr(window, "set_undoable_property"):
                window.set_undoable_property("is_starred", bool(value), "update_text")

            self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to set star", e, self._err_state)

    def archive_window(self, window_uuid: str, value: bool) -> None:
        """指定ウィンドウのアーカイブ状態を設定する。"""
        try:
            window = self._find_text_window(window_uuid)
            if window is None:
                return

            if hasattr(window, "set_archived"):
                window.set_archived(bool(value))
            elif hasattr(window, "set_undoable_property"):
                window.set_undoable_property("is_archived", bool(value), "update_text")

            self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to archive window", e, self._err_state)
