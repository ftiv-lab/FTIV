# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from utils.due_date import normalize_due_iso
from utils.error_reporter import ErrorNotifyState, report_unexpected_error
from utils.tag_ops import merge_tags, normalize_tags

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
    def _unique_window_uuids(window_uuids: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw_uuid in list(window_uuids or []):
            window_uuid = str(raw_uuid or "").strip()
            if not window_uuid or window_uuid in seen:
                continue
            out.append(window_uuid)
            seen.add(window_uuid)
        return out

    def _begin_undo_macro(self, name: str) -> bool:
        stack = getattr(self.mw, "undo_stack", None)
        if stack is None or not hasattr(stack, "beginMacro"):
            return False
        stack.beginMacro(str(name or "Info Bulk Action"))
        return True

    def _end_undo_macro(self, opened: bool) -> None:
        if not opened:
            return
        stack = getattr(self.mw, "undo_stack", None)
        if stack is None or not hasattr(stack, "endMacro"):
            return
        stack.endMacro()

    def _persist_app_settings(self) -> None:
        settings_manager = getattr(self.mw, "settings_manager", None)
        if settings_manager is not None and hasattr(settings_manager, "save_app_settings"):
            settings_manager.save_app_settings()

    def _append_operation_log(self, action: str, target_count: int, detail: str = "") -> None:
        try:
            count = int(target_count)
            if count < 1:
                return
            action_key = str(action or "").strip()
            if not action_key:
                return

            settings = getattr(self.mw, "app_settings", None)
            if settings is None:
                return

            logs = list(getattr(settings, "info_operation_logs", []) or [])
            logs.append(
                {
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "action": action_key,
                    "target_count": count,
                    "detail": str(detail or "").strip()[:80],
                }
            )
            settings.info_operation_logs = logs[-200:]
            self._persist_app_settings()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to save operation log", e, self._err_state)

    def get_operation_logs(self, limit: int | None = None) -> list[dict[str, Any]]:
        settings = getattr(self.mw, "app_settings", None)
        logs = list(getattr(settings, "info_operation_logs", []) or []) if settings is not None else []
        if limit is None:
            return logs
        if int(limit) <= 0:
            return []
        return logs[-int(limit) :]

    def clear_operation_logs(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        if settings is None:
            return
        settings.info_operation_logs = []
        self._persist_app_settings()
        self._refresh_info_tab()

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

            normalized = normalize_due_iso(due_iso)
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
            target = bool(value)
            changed_count = 0
            macro_opened = self._begin_undo_macro("Archive Selected" if target else "Restore Selected")
            try:
                for window_uuid in self._unique_window_uuids(window_uuids):
                    window = self._find_text_window(window_uuid)
                    if window is None:
                        continue
                    if bool(getattr(window, "is_archived", False)) == target:
                        continue
                    if hasattr(window, "set_archived"):
                        window.set_archived(target)
                        changed_count += 1
                    elif hasattr(window, "set_undoable_property"):
                        window.set_undoable_property("is_archived", target, "update_text")
                        changed_count += 1
            finally:
                self._end_undo_macro(macro_opened)

            if changed_count > 0:
                self._append_operation_log(
                    "bulk_archive" if target else "bulk_restore",
                    changed_count,
                    "archive" if target else "restore",
                )
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk archive", e, self._err_state)

    def bulk_set_star(self, window_uuids: list[str], value: bool) -> None:
        """複数UUIDに対してスター状態を一括更新する。"""
        try:
            target = bool(value)
            changed_count = 0
            macro_opened = self._begin_undo_macro("Star Selected" if target else "Unstar Selected")
            try:
                for window_uuid in self._unique_window_uuids(window_uuids):
                    window = self._find_text_window(window_uuid)
                    if window is None:
                        continue
                    if bool(getattr(window, "is_starred", False)) == target:
                        continue
                    if hasattr(window, "set_starred"):
                        window.set_starred(target)
                        changed_count += 1
                    elif hasattr(window, "set_undoable_property"):
                        window.set_undoable_property("is_starred", target, "update_text")
                        changed_count += 1
            finally:
                self._end_undo_macro(macro_opened)

            if changed_count > 0:
                self._append_operation_log(
                    "bulk_star" if target else "bulk_unstar",
                    changed_count,
                    "star" if target else "unstar",
                )
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk set star", e, self._err_state)

    def bulk_merge_tags(self, window_uuids: list[str], add_tags: list[str], remove_tags: list[str]) -> None:
        """複数UUIDに対してタグを add/remove マージ更新する。"""
        try:
            add_norm = normalize_tags(add_tags or [])
            remove_norm = normalize_tags(remove_tags or [])
            if not add_norm and not remove_norm:
                return

            changed_count = 0
            macro_opened = self._begin_undo_macro("Edit Tags Selected")
            try:
                for window_uuid in self._unique_window_uuids(window_uuids):
                    window = self._find_text_window(window_uuid)
                    if window is None:
                        continue

                    raw_tags = getattr(window, "tags", [])
                    current_tags = normalize_tags(raw_tags if isinstance(raw_tags, list) else [])
                    merged_tags = merge_tags(current_tags, add_norm, remove_norm)
                    if merged_tags == current_tags:
                        continue

                    if hasattr(window, "set_tags"):
                        window.set_tags(merged_tags)
                        changed_count += 1
                        continue
                    if hasattr(window, "set_title_and_tags"):
                        current_title = str(getattr(window, "title", "") or "")
                        window.set_title_and_tags(current_title, merged_tags)
                        changed_count += 1
                        continue
                    if hasattr(window, "set_undoable_property"):
                        window.set_undoable_property("tags", merged_tags, "update_text")
                        changed_count += 1
            finally:
                self._end_undo_macro(macro_opened)

            if changed_count > 0:
                self._append_operation_log(
                    "bulk_tags_merge",
                    changed_count,
                    f"add={len(add_norm)} remove={len(remove_norm)}",
                )
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk merge tags", e, self._err_state)

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
            processed_item_count = 0
            macro_opened = self._begin_undo_macro("Complete Selected" if value else "Uncomplete Selected")
            try:
                for window_uuid, indices in targets.items():
                    window = self._find_text_window(window_uuid)
                    if window is None:
                        continue

                    unique_indices = sorted(set(indices))
                    if not unique_indices:
                        continue

                    if hasattr(window, "bulk_set_task_done"):
                        window.bulk_set_task_done(unique_indices, bool(value))
                        changed = True
                        processed_item_count += len(unique_indices)
                        continue

                    if hasattr(window, "set_task_line_state"):
                        for idx in unique_indices:
                            window.set_task_line_state(idx, bool(value))
                            changed = True
                            processed_item_count += 1
                        continue

                    if hasattr(window, "toggle_task_line_state") and hasattr(window, "get_task_line_state"):
                        for idx in unique_indices:
                            current = bool(window.get_task_line_state(idx))
                            target = bool(value)
                            if current != target:
                                window.toggle_task_line_state(idx)
                                changed = True
                                processed_item_count += 1
            finally:
                self._end_undo_macro(macro_opened)

            if changed:
                self._append_operation_log(
                    "bulk_complete" if value else "bulk_uncomplete",
                    max(processed_item_count, 1),
                    "task",
                )
                self._refresh_info_tab()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to bulk update task state", e, self._err_state)
