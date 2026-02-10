# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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

    @staticmethod
    def _normalize_due_iso(value: str) -> str | None:
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

    def set_due_at(self, window_uuid: str, due_iso: str) -> None:
        """指定ウィンドウへ期限を設定する。"""
        try:
            window = self._find_text_window(window_uuid)
            if window is None:
                return

            normalized = self._normalize_due_iso(due_iso)
            if normalized is None:
                return

            if hasattr(window, "set_due_at"):
                window.set_due_at(normalized)
            elif hasattr(window, "set_undoable_property"):
                window.set_undoable_property("due_at", normalized, "update_text")
            self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to set due date", e, self._err_state)

    def clear_due_at(self, window_uuid: str) -> None:
        """指定ウィンドウの期限を解除する。"""
        try:
            window = self._find_text_window(window_uuid)
            if window is None:
                return

            if hasattr(window, "clear_due_at"):
                window.clear_due_at()
            elif hasattr(window, "set_undoable_property"):
                window.set_undoable_property("due_at", "", "update_text")
            self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to clear due date", e, self._err_state)

    def bulk_archive(self, window_uuids: list[str], value: bool) -> None:
        """複数UUIDに対してアーカイブ状態を一括更新する。"""
        try:
            changed = False
            for raw_uuid in list(window_uuids or []):
                window_uuid = str(raw_uuid or "").strip()
                if not window_uuid:
                    continue
                window = self._find_text_window(window_uuid)
                if window is None:
                    continue
                if hasattr(window, "set_archived"):
                    window.set_archived(bool(value))
                    changed = True
                elif hasattr(window, "set_undoable_property"):
                    window.set_undoable_property("is_archived", bool(value), "update_text")
                    changed = True
            if changed:
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk archive", e, self._err_state)

    def bulk_set_task_done(self, item_keys: list[str], value: bool) -> None:
        """item_key(uuid:index) 群に対して完了状態を一括更新する。"""
        try:
            targets: Dict[str, List[int]] = {}
            for raw_key in list(item_keys or []):
                key = str(raw_key or "").strip()
                if ":" not in key:
                    continue
                window_uuid, line_index_text = key.rsplit(":", 1)
                try:
                    line_index = int(line_index_text)
                except ValueError:
                    continue
                if line_index < 0:
                    continue
                targets.setdefault(window_uuid, []).append(line_index)

            changed = False
            for window_uuid, indices in targets.items():
                window = self._find_text_window(window_uuid)
                if window is None:
                    continue

                if hasattr(window, "bulk_set_task_done"):
                    window.bulk_set_task_done(indices, bool(value))
                    changed = True
                    continue

                if hasattr(window, "set_task_line_state"):
                    for idx in sorted(set(indices)):
                        window.set_task_line_state(idx, bool(value))
                        changed = True
                    continue

                if hasattr(window, "toggle_task_line_state") and hasattr(window, "get_task_line_state"):
                    for idx in sorted(set(indices)):
                        current = bool(window.get_task_line_state(idx))
                        target = bool(value)
                        if current != target:
                            window.toggle_task_line_state(idx)
                            changed = True

            if changed:
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk update task state", e, self._err_state)
