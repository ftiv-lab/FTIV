import json
import logging
import os
import re
import traceback
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QMessageBox,
)

from models.constants import AppDefaults
from models.window_config import TextWindowConfig
from ui.context_menu import ContextMenuBuilder
from ui.dialogs import (
    GradientEditorDialog,
    MarginRatioDialog,
    ShadowOffsetDialog,
    StyleGalleryDialog,
    TextInputDialog,
    TextSpacingDialog,
)
from utils.due_date import normalize_due_iso
from utils.font_dialog import choose_font
from utils.tag_ops import normalize_tags
from utils.translator import tr

from .base_window import BaseOverlayWindow
from .mixins.inline_editor_mixin import InlineEditorMixin
from .mixins.text_properties_mixin import TextPropertiesMixin

# ロガーの取得
logger = logging.getLogger(__name__)
LEGACY_TASK_LINE_PATTERN = re.compile(r"^\s*\[(?P<state>[ xX])\]\s?(?P<body>.*)$")


@dataclass(frozen=True)
class TaskLineRef:
    """タスク一覧向けの1行参照。"""

    window_uuid: str
    line_index: int
    text: str
    done: bool


class TextWindow(TextPropertiesMixin, InlineEditorMixin, BaseOverlayWindow):  # type: ignore
    """テキストを表示・制御するためのオーバーレイウィンドウクラス。

    テキストの描画、スタイル設定、およびマインドマップ風のノード操作を管理します。
    """

    def __init__(self, main_window: Any, text: str, pos: QPoint):
        """TextWindowの初期化を行い、ログに記録します。

        Args:
            main_window (Any): メインウィンドウのインスタンス。
            text (str): 初期表示テキスト。
            pos (QPoint): 表示位置。
        """
        BaseOverlayWindow.__init__(self, main_window, config_class=TextWindowConfig)
        InlineEditorMixin.__init__(self)

        try:
            self._init_text_renderer(main_window)
            self._suppress_task_state_sync = False
            self._task_press_pos: Optional[QPoint] = None

            self.config.text = text
            self.config.position = {"x": pos.x(), "y": pos.y()}
            now_iso = datetime.now().isoformat(timespec="seconds")
            if not self.config.created_at:
                self.config.created_at = now_iso
            if not self.config.updated_at:
                self.config.updated_at = now_iso
            if self.config.is_vertical:
                self.config.note_vertical_preference = True
            self._ensure_task_states_for_text(self.config.text)
            self._ensure_task_mode_constraints(allow_legacy_migration=True)
            self.canvas_size: QSize = QSize(10, 10)
            self.setGeometry(QRect(pos, self.canvas_size))

            defaults = self.load_text_defaults()
            self.config.horizontal_margin_ratio = defaults.get("h_margin", 0.0)
            self.config.vertical_margin_ratio = defaults.get("v_margin", 0.0)  # Was 0.2
            self.config.margin_top = defaults.get("margin_top", 0.0)
            self.config.margin_bottom = defaults.get("margin_bottom", 0.0)
            self.config.margin_left = defaults.get("margin_left", 0.0)
            self.config.margin_right = defaults.get("margin_right", 0.0)

            self._previous_text_opacity: int = 100
            self._previous_background_opacity: int = 100

            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
            self.setMouseTracking(True)  # タスクモードのホバーカーソル変更用

            self._last_loaded_font_path: str = ""

            self.update_text()
            logger.info(f"TextWindow initialized: UUID={self.uuid}")

        except Exception as e:
            logger.error(f"Failed to initialize TextWindow: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(None, tr("msg_error"), f"Initialization error: {e}")

    # --- Properties ---

    # --- Properties ---
    # Moved to TextPropertiesMixin

    # --- Core Logic ---

    def paintEvent(self, event: Any) -> None:
        """ペイントイベントのオーバーライド。

        Args:
            event: QPaintEventオブジェクト。
        """
        super().paintEvent(event)
        painter = QPainter(self)
        self.draw_selection_frame(painter)
        painter.end()

    # update_text, update_text_debounced, _update_text_immediate, _restore_render_debounce_ms_after_wheel
    # Moved to TextPropertiesMixin. _update_text_immediate handles rendering.

    def _update_text_immediate(self) -> None:
        self._ensure_task_mode_constraints()
        super()._update_text_immediate()

    def set_undoable_property(
        self,
        property_name: str,
        new_value: Any,
        update_method_name: Optional[str] = None,
    ) -> None:
        """Undo可能な形式でプロパティを変更する（TextWindow用の最適化）。

        Notes:
            font_size はホイール操作で連打されやすく、update_text が重い。
            そのため font_size 変更時は update_text を即時実行せず、デバウンス予約に寄せる。

        Args:
            property_name (str): 変更プロパティ名。
            new_value (Any): 新しい値。
            update_method_name (Optional[str]): 通常の更新メソッド名。
        """
        # font_size は常に「即時update_text」にならないようにする
        if property_name == "font_size":
            super().set_undoable_property(property_name, new_value, None)
            self.update_text_debounced()
            return

        if property_name == "is_vertical":
            requested = bool(new_value)
            if self.is_task_mode() and requested:
                QMessageBox.information(self, tr("msg_info"), tr("msg_task_mode_horizontal_only"))
                return
            super().set_undoable_property(property_name, requested, update_method_name)
            if not self.is_task_mode():
                self.note_vertical_preference = requested
            return

        if property_name == "task_states":
            line_count = len(self._split_lines(self.text))
            normalized = self._normalize_task_states(
                list(new_value) if isinstance(new_value, list) else [],
                line_count,
            )
            super().set_undoable_property(property_name, normalized, update_method_name)
            return

        super().set_undoable_property(property_name, new_value, update_method_name)

    def toggle_outline(self) -> None:
        self.set_undoable_property("outline_enabled", not self.outline_enabled, "update_text")

    def change_outline_color(self) -> None:
        color = QColorDialog.getColor(self.outline_color, self)
        if color.isValid():
            self.set_undoable_property("outline_color", color, "update_text")

    def toggle_second_outline(self) -> None:
        self.set_undoable_property("second_outline_enabled", not self.second_outline_enabled, "update_text")

    def change_second_outline_color(self) -> None:
        color = QColorDialog.getColor(self.second_outline_color, self)
        if color.isValid():
            self.set_undoable_property("second_outline_color", color, "update_text")

    def toggle_third_outline(self) -> None:
        self.set_undoable_property("third_outline_enabled", not self.third_outline_enabled, "update_text")

    def change_third_outline_color(self) -> None:
        color = QColorDialog.getColor(self.third_outline_color, self)
        if color.isValid():
            self.set_undoable_property("third_outline_color", color, "update_text")

    def toggle_vertical_text(self) -> None:
        if self.is_task_mode():
            QMessageBox.information(self, tr("msg_info"), tr("msg_task_mode_horizontal_only"))
            return

        new_value = not self.is_vertical
        self.set_undoable_property("is_vertical", new_value, "update_text")
        self.note_vertical_preference = bool(new_value)
        self._touch_updated_at()

    def is_task_mode(self) -> bool:
        """現在のコンテンツモードが task かどうかを返す。"""
        return str(getattr(self, "content_mode", "note")).lower() == "task"

    @staticmethod
    def _split_lines(text: str) -> List[str]:
        src = str(text or "")
        return src.split("\n") if src else [""]

    @staticmethod
    def _normalize_task_states(states: List[bool], line_count: int) -> List[bool]:
        normalized = [bool(v) for v in states] if isinstance(states, list) else []
        if line_count <= 0:
            return []
        if len(normalized) < line_count:
            normalized.extend([False] * (line_count - len(normalized)))
        elif len(normalized) > line_count:
            normalized = normalized[:line_count]
        return normalized

    @staticmethod
    def _remap_task_states(old_lines: List[str], new_lines: List[str], old_states: List[bool]) -> List[bool]:
        matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
        remapped: List[bool] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                remapped.extend(old_states[i1:i2])
            elif tag == "replace":
                old_chunk = old_states[i1:i2]
                new_count = j2 - j1
                carry = min(len(old_chunk), new_count)
                remapped.extend(old_chunk[:carry])
                if new_count > carry:
                    remapped.extend([False] * (new_count - carry))
            elif tag == "insert":
                remapped.extend([False] * (j2 - j1))
            elif tag == "delete":
                continue
        return remapped

    def _ensure_task_states_for_text(self, text: str, old_text: Optional[str] = None) -> None:
        new_lines = self._split_lines(text)
        if old_text is None:
            self.task_states = self._normalize_task_states(self.task_states, len(new_lines))
            return

        old_lines = self._split_lines(old_text)
        old_states = self._normalize_task_states(self.task_states, len(old_lines))
        remapped = self._remap_task_states(old_lines, new_lines, old_states)
        self.task_states = self._normalize_task_states(remapped, len(new_lines))

    def _extract_legacy_task_data(self, text: str) -> tuple[str, List[bool], bool]:
        lines = self._split_lines(text)
        migrated_lines: List[str] = []
        migrated_states: List[bool] = []
        migrated_any = False

        for line in lines:
            match = LEGACY_TASK_LINE_PATTERN.match(str(line or ""))
            if match:
                migrated_any = True
                state = str(match.group("state") or " ").strip().lower() == "x"
                body = str(match.group("body") or "")
                migrated_lines.append(body)
                migrated_states.append(state)
            else:
                migrated_lines.append(str(line or ""))
                migrated_states.append(False)
        return "\n".join(migrated_lines), migrated_states, migrated_any

    def _migrate_legacy_task_prefixes(self) -> None:
        text_now = str(self.text or "")
        cleaned_text, migrated_states, migrated_any = self._extract_legacy_task_data(text_now)
        if not migrated_any:
            return

        # task_states が既に実運用値を持っている場合は、本文だけ変換して状態は保持する。
        existing_states = self._normalize_task_states(self.task_states, len(self._split_lines(text_now)))
        has_non_default_state = any(existing_states)

        self._suppress_task_state_sync = True
        try:
            self.config.text = cleaned_text
        finally:
            self._suppress_task_state_sync = False

        if has_non_default_state:
            self._ensure_task_states_for_text(cleaned_text)
        else:
            self.task_states = self._normalize_task_states(migrated_states, len(self._split_lines(cleaned_text)))

    def _ensure_task_mode_constraints(self, allow_legacy_migration: bool = False) -> None:
        self._ensure_task_states_for_text(self.text)
        if self.is_task_mode():
            if allow_legacy_migration:
                self._migrate_legacy_task_prefixes()
                self._ensure_task_states_for_text(self.text)
            if self.is_vertical:
                self.config.is_vertical = False
        else:
            self.note_vertical_preference = bool(self.is_vertical)

    def _on_text_assigned(self, old_text: str, new_text: str) -> None:
        if getattr(self, "_suppress_task_state_sync", False):
            return
        self._ensure_task_states_for_text(new_text, old_text=old_text)

    def _touch_updated_at(self) -> None:
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    def _get_task_rail_width_for_mode(self, mode: str) -> int:
        normalized = "task" if str(mode or "").lower() == "task" else "note"
        if normalized != "task":
            return 0

        font = QFont(self.font_family, int(self.font_size))
        fm = QFontMetrics(font)
        renderer = getattr(self, "renderer", None)
        if renderer is not None and hasattr(renderer, "_compute_task_rail_width"):
            try:
                return int(renderer._compute_task_rail_width(int(self.font_size), fm))
            except Exception:
                pass

        marker_width = max(1, fm.horizontalAdvance("☐"))
        marker_gap = max(2, fm.horizontalAdvance(" "))
        side_padding = max(2, int(float(self.font_size) * 0.08))
        return int(marker_width + marker_gap + side_padding)

    def _preserve_text_anchor_on_mode_change(self, old_mode: str, new_mode: str) -> None:
        if bool(self.is_vertical):
            return
        old_rail = self._get_task_rail_width_for_mode(old_mode)
        new_rail = self._get_task_rail_width_for_mode(new_mode)
        delta = int(new_rail - old_rail)
        if delta != 0:
            try:
                self.move(self.x() - delta, self.y())
            except RuntimeError:
                # ロジックテスト等で QWidget 初期化前の場合は補正をスキップ
                return

    def set_content_mode(self, mode: str) -> None:
        """note/task モードを切り替える。"""
        old_mode = str(self.content_mode or "note").lower()
        normalized = "task" if str(mode or "").lower() == "task" else "note"
        if self.content_mode == normalized:
            self._ensure_task_mode_constraints()
            return

        stack = getattr(self.main_window, "undo_stack", None)
        use_macro = bool(stack is not None and hasattr(stack, "beginMacro") and hasattr(stack, "endMacro"))
        if use_macro:
            stack.beginMacro("Change Content Mode")
        try:
            if normalized == "task":
                self.note_vertical_preference = bool(self.is_vertical)
                if self.is_vertical:
                    self.set_undoable_property("is_vertical", False, None)
                self._migrate_legacy_task_prefixes()
                self._ensure_task_states_for_text(self.text)
            else:
                restore_vertical = bool(self.note_vertical_preference)
                if self.is_vertical != restore_vertical:
                    self.set_undoable_property("is_vertical", restore_vertical, None)

            self.set_undoable_property("content_mode", normalized, "update_text")
            self._preserve_text_anchor_on_mode_change(old_mode, normalized)
            self._touch_updated_at()
        finally:
            if use_macro:
                stack.endMacro()

    def _toggle_task_line_by_index(self, idx: int) -> None:
        """指定行の完了状態をトグルする。"""
        self.toggle_task_line_state(idx)

    def _toggle_task_line_under_cursor(self) -> None:
        """インライン編集中のカーソル行の完了状態をトグルする。"""
        if not self.is_task_mode() or not getattr(self, "_is_editing", False):
            QMessageBox.information(self, tr("msg_info"), tr("msg_task_toggle_requires_inline_edit"))
            return

        editor = getattr(self, "_inline_editor", None)
        if editor is None:
            QMessageBox.information(self, tr("msg_info"), tr("msg_task_toggle_requires_inline_edit"))
            return

        cursor = editor.textCursor()
        line_idx = cursor.blockNumber()

        lines = editor.toPlainText().split("\n")
        if line_idx < 0 or line_idx >= len(lines):
            return

        self._toggle_task_line_by_index(line_idx)

        self._touch_updated_at()
        self.update_text()

    def get_task_progress(self) -> tuple[int, int]:
        """タスクの進捗を返す（完了数, 総数）。"""
        if not self.is_task_mode():
            return 0, 0
        total = len(self._split_lines(self.text))
        states = self._normalize_task_states(self.task_states, total)
        done = sum(1 for state in states if state)
        return done, total

    def iter_task_items(self) -> List[TaskLineRef]:
        """タスク行の参照一覧を返す（taskモード時のみ）。"""
        if not self.is_task_mode():
            return []

        lines = self._split_lines(self.text)
        states = self._normalize_task_states(self.task_states, len(lines))
        window_uuid = str(getattr(self, "uuid", ""))
        return [
            TaskLineRef(
                window_uuid=window_uuid,
                line_index=i,
                text=str(line or ""),
                done=bool(states[i]),
            )
            for i, line in enumerate(lines)
        ]

    def get_task_line_state(self, index: int) -> bool:
        """指定行のタスク状態を返す。"""
        if not self.is_task_mode():
            return False
        lines = self._split_lines(self.text)
        if index < 0 or index >= len(lines):
            return False
        states = self._normalize_task_states(self.task_states, len(lines))
        return bool(states[index])

    def set_task_line_state(self, index: int, done: bool) -> None:
        """指定行のタスク状態を設定する。"""
        if not self.is_task_mode():
            return
        lines = self._split_lines(self.text)
        if index < 0 or index >= len(lines):
            return

        states = self._normalize_task_states(self.task_states, len(lines))
        target = bool(done)
        if bool(states[index]) == target:
            return

        new_states = list(states)
        new_states[index] = target
        self.set_undoable_property("task_states", new_states, "update_text")
        self._touch_updated_at()

    def toggle_task_line_state(self, index: int) -> None:
        """指定行のタスク状態をトグルする。"""
        if not self.is_task_mode():
            return
        self.set_task_line_state(index, not self.get_task_line_state(index))

    def set_title_and_tags(self, title: str, tags: List[str]) -> None:
        """ノートメタ（title/tags）をまとめて更新する。"""
        normalized_title = str(title or "").strip()
        normalized_tags = normalize_tags(tags or [])

        stack = getattr(self.main_window, "undo_stack", None)
        use_macro = bool(stack is not None and hasattr(stack, "beginMacro") and hasattr(stack, "endMacro"))
        if use_macro:
            stack.beginMacro("Update Note Metadata")
        try:
            if self.title != normalized_title:
                self.set_undoable_property("title", normalized_title, "update_text")
            if self.tags != normalized_tags:
                self.set_undoable_property("tags", normalized_tags, "update_text")
            self._touch_updated_at()
        finally:
            if use_macro:
                stack.endMacro()

    def set_tags(self, tags: List[str]) -> None:
        """タグのみを正規化して更新する。"""
        normalized_tags = normalize_tags(tags or [])
        if list(getattr(self, "tags", []) or []) == normalized_tags:
            return
        self.set_undoable_property("tags", normalized_tags, "update_text")
        self._touch_updated_at()

    def set_starred(self, value: bool) -> None:
        """スター状態を更新する。"""
        new_value = bool(value)
        if bool(self.is_starred) == new_value:
            return
        self.set_undoable_property("is_starred", new_value, "update_text")
        self._touch_updated_at()

    def set_archived(self, value: bool) -> None:
        """アーカイブ状態を更新する。"""
        new_value = bool(value)
        if bool(getattr(self, "is_archived", False)) == new_value:
            return
        self.set_undoable_property("is_archived", new_value, "update_text")
        self._touch_updated_at()

    @staticmethod
    def _normalize_due_iso(value: str) -> str | None:
        return normalize_due_iso(value)

    def set_due_at(self, value: str) -> None:
        """期限を設定する（内部保存は YYYY-MM-DDT00:00:00）。"""
        normalized = self._normalize_due_iso(value)
        if normalized is None:
            return
        if str(getattr(self, "due_at", "") or "") == normalized:
            return
        self.set_undoable_property("due_at", normalized, "update_text")
        self._touch_updated_at()

    def clear_due_at(self) -> None:
        """期限を解除する。"""
        if not str(getattr(self, "due_at", "") or ""):
            return
        self.set_undoable_property("due_at", "", "update_text")
        self._touch_updated_at()

    def bulk_set_task_done(self, indices: List[int], value: bool) -> None:
        """指定行群のタスク状態を一括設定する。"""
        if not self.is_task_mode():
            return
        total = len(self._split_lines(self.text))
        states = self._normalize_task_states(self.task_states, total)
        new_states = list(states)
        target = bool(value)
        changed = False
        for idx in sorted(set(indices or [])):
            if idx < 0 or idx >= total:
                continue
            if bool(new_states[idx]) == target:
                continue
            new_states[idx] = target
            changed = True
        if changed:
            self.set_undoable_property("task_states", new_states, "update_text")
            self._touch_updated_at()

    def complete_all_tasks(self) -> None:
        """全タスク行を完了状態にする。"""
        if not self.is_task_mode():
            return
        total = len(self._split_lines(self.text))
        states = self._normalize_task_states(self.task_states, total)
        new_states = [True for _ in states]
        if new_states != states:
            self.set_undoable_property("task_states", new_states, "update_text")
            self._touch_updated_at()

    def uncomplete_all_tasks(self) -> None:
        """全タスク行を未完了状態にする。"""
        if not self.is_task_mode():
            return
        total = len(self._split_lines(self.text))
        states = self._normalize_task_states(self.task_states, total)
        new_states = [False for _ in states]
        if new_states != states:
            self.set_undoable_property("task_states", new_states, "update_text")
            self._touch_updated_at()

    def set_horizontal_margin_ratio(self) -> None:
        dialog = MarginRatioDialog(
            tr("title_set_h_margin"), tr("label_char_spacing_horz"), self.horizontal_margin_ratio, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.set_undoable_property("horizontal_margin_ratio", dialog.get_value(), "update_text")

    def set_vertical_margin_ratio(self) -> None:
        dialog = MarginRatioDialog(
            tr("title_set_v_margin"), tr("label_line_spacing_vert"), self.vertical_margin_ratio, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.set_undoable_property("vertical_margin_ratio", dialog.get_value(), "update_text")

    def keyPressEvent(self, event: Any) -> None:
        """キープレスイベントの管理。

        ロック中は配置が変わる操作（ノード追加/ナビ/変形）を無効化する。
        ただし管理系（Delete/H/F）は許可する。

        Args:
            event (Any): QKeyEvent
        """
        try:
            locked: bool = bool(getattr(self, "is_locked", False))

            # --- 管理系（ロック中でも許可）---
            if event.key() == Qt.Key_Delete:
                self.close()
                event.accept()
                return

            if event.key() == Qt.Key_H:
                self.hide_action()
                event.accept()
                return

            if event.key() == Qt.Key_F:
                self.toggle_frontmost()
                event.accept()
                return

            # --- ロック中はここから先を止める ---
            if locked:
                event.accept()
                return

            # --- 配置/ノード操作 ---
            if event.key() == Qt.Key_Tab:
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "create_related_node"
                ):
                    self.main_window.window_manager.create_related_node(self, "child")
                event.accept()
                return

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "create_related_node"
                ):
                    self.main_window.window_manager.create_related_node(self, "sibling")
                event.accept()
                return

            # --- ナビゲーション ---
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "navigate_selection"
                ):
                    self.main_window.window_manager.navigate_selection(self, event.key())
                event.accept()
                return

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Error handling key press: {e}")
            traceback.print_exc()
            event.accept()
            return

        # デフォルト処理
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: Any) -> None:
        """ログに記録しながらダブルクリックイベントを処理します。"""
        try:
            if event.modifiers() & Qt.ControlModifier:
                super().mouseDoubleClickEvent(event)
                return

            if event.button() == Qt.MouseButton.LeftButton:
                # インライン編集を開始
                self._start_inline_edit()
                event.accept()
            else:
                super().mouseDoubleClickEvent(event)
        except Exception as e:
            logger.error(f"Error in mouseDoubleClickEvent: {e}")
            # Fallback to old behavior or just log and pass
            self.change_text()  # This line was in the original snippet, keeping it as a fallback
            pass

    def mousePressEvent(self, event: Any) -> None:
        """マウスプレスイベント。タスクモードのクリック検出用に位置を記録。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._task_press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        """マウスリリースイベント。タスクモードでチェックボックスクリックを処理。"""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.is_task_mode()
            and not getattr(self, "_is_editing", False)
        ):
            release_pos = event.position().toPoint()
            press_pos = getattr(self, "_task_press_pos", None)
            if press_pos is not None:
                dist = (release_pos - press_pos).manhattanLength()
                if dist < 10:
                    idx = self._hit_test_task_checkbox(release_pos)
                    if idx >= 0:
                        self._toggle_task_line_by_index(idx)
                        super().mouseReleaseEvent(event)
                        return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        """マウスムーブイベント。タスクモード時にチェックボックス上でカーソル変更。"""
        if self.is_task_mode() and not self.is_dragging and not getattr(self, "_is_editing", False):
            pos = event.position().toPoint()
            idx = self._hit_test_task_checkbox(pos)
            if idx >= 0:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.unsetCursor()
        super().mouseMoveEvent(event)

    def _hit_test_task_checkbox(self, pos: QPoint) -> int:
        """クリック位置がどのタスク行のチェックボックスにヒットするか判定。

        Args:
            pos: ウィジェット座標系のクリック位置。

        Returns:
            ヒットした行インデックス。ヒットなしの場合は -1。
        """
        if not self.is_task_mode() or self.is_vertical:
            return -1

        renderer = getattr(self, "renderer", None)
        if renderer is None:
            return -1

        rects = renderer.get_task_line_rects(self)
        for i, rect in enumerate(rects):
            if rect.contains(pos):
                return i
        return -1

    def wheelEvent(self, event: Any) -> None:
        """マウスホイールによるフォントサイズ変更。

        ロック中は誤操作防止のため無効化する。
        """
        # インライン編集中はスクロール（リサイズ）を無効化
        if self._is_editing:
            return

        try:
            if bool(getattr(self, "is_locked", False)):
                event.accept()
                return

            angle = event.angleDelta().y()
            if angle == 0:
                return

            step = 2
            current_size = self.font_size

            # 上回転で縮小、下回転で拡大
            new_size = (current_size - step) if angle > 0 else (current_size + step)
            new_size = max(5, min(500, new_size))

            if new_size != current_size:
                # Undoは積むが、即時レンダ(update_text)は走らせない
                # → 描画はデバウンス予約で最後の1回に寄せる
                self.set_undoable_property("font_size", new_size, None)
                self.update_text_debounced()

            # ホイール中だけデバウンスを強めて、フリーズ感をさらに減らす
            try:
                # 設定値があればそれを使い、なければ80
                val = getattr(self, "_wheel_debounce_setting", AppDefaults.WHEEL_DEBOUNCE_MS)
                self._render_debounce_ms = int(val)
                self._wheel_render_relax_timer.start(150)
            except Exception:
                pass

            event.accept()

        except Exception:
            traceback.print_exc()

    def _restore_render_debounce_ms_after_wheel(self) -> None:
        """ホイール操作後に描画デバウンス値を標準へ戻す。"""
        try:
            self._render_debounce_ms = 25
        except Exception:
            pass

    def toggle_text_visibility(self) -> None:
        if self.text_opacity > 0:
            self._previous_text_opacity = self.text_opacity
            new_opacity = 0
        else:
            new_opacity = getattr(self, "_previous_text_opacity", 100)
        self.set_undoable_property("text_opacity", new_opacity, "update_text")

    def toggle_background_visibility(self) -> None:
        if self.background_opacity > 0:
            self._previous_background_opacity = self.background_opacity
            new_opacity = 0
        else:
            new_opacity = getattr(self, "_previous_background_opacity", 100)
        self.set_undoable_property("background_opacity", new_opacity, "update_text")

    def change_text(self) -> None:
        """リアルタイムプレビュー付きでテキストを変更し、変更をログに記録します。"""
        original_text = self.text

        def live_update_callback(new_text: str):
            try:
                self.text = new_text
                self.update_text()
            except Exception as e:
                logger.error(f"Live update failed: {e}")

        try:
            dialog = TextInputDialog(self.text, self, callback=live_update_callback)

            # ダイアログの配置ロジック
            screen = self.screen()
            if screen:
                screen_geo = screen.availableGeometry()
                win_geo = self.geometry()
                dlg_w, dlg_h, padding = dialog.width(), dialog.height(), 20

                target_x = win_geo.right() + padding
                if target_x + dlg_w > screen_geo.right():
                    target_x = win_geo.left() - dlg_w - padding
                target_y = max(screen_geo.top(), min(win_geo.top(), screen_geo.bottom() - dlg_h))
                dialog.move(target_x, target_y)

            if dialog.exec() == QDialog.Accepted:
                final_text = dialog.get_text()
                self.text = original_text
                if final_text != original_text:
                    self.set_undoable_property("text", final_text, "update_text")
                    logger.info(f"Text changed for {self.uuid}")
                else:
                    self.update_text()
            else:
                self.text = original_text
                self.update_text()

        except Exception as e:
            logger.error(f"Error in change_text dialog: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open edit dialog: {e}")
            self.text = original_text
            self.update_text()

    def change_font(self) -> None:
        """フォント選択ダイアログを表示し、適用する。"""
        font = choose_font(self, QFont(self.font_family, int(self.font_size)))
        if font is not None:
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Change Font")
            self.set_undoable_property("font_family", font.family(), None)
            self.set_undoable_property("font_size", font.pointSize(), None)

            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def change_font_color(self) -> None:
        color = QColorDialog.getColor(self.font_color, self)
        if color.isValid():
            self.set_undoable_property("font_color", color, "update_text")

    def change_background_color(self) -> None:
        color = QColorDialog.getColor(self.background_color, self)
        if color.isValid():
            self.set_undoable_property("background_color", color, "update_text")

    def toggle_shadow(self) -> None:
        self.set_undoable_property("shadow_enabled", not self.shadow_enabled, "update_text")

    def change_shadow_color(self) -> None:
        color = QColorDialog.getColor(self.shadow_color, self)
        if color.isValid():
            self.set_undoable_property("shadow_color", color, "update_text")

    def add_text_window(self) -> None:
        """新規テキストウィンドウを追加する（WindowManager 経由で生成）。

        目的:
            - 生成経路を WindowManager に統一し、FREE制限・選択同期・シグナル接続・管理リストの整合性を守る。

        """
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            # 自分の近くに出す（少しずらす）
            new_pos: QPoint = self.pos() + QPoint(20, 20)

            _w: Optional["TextWindow"] = mw.window_manager.add_text_window(
                text=tr("new_text_default"),
                pos=new_pos,
                suppress_limit_message=False,
            )
            # None の場合（FREE制限等）は WindowManager 側で通知される想定

        except Exception as e:
            logger.error("Failed to add TextWindow via WindowManager: %s\n%s", e, traceback.format_exc())
            QMessageBox.critical(self, tr("msg_error"), f"Failed to add text window: {e}")

    def clone_text(self) -> None:
        """現在のテキストウィンドウを複製します（WindowManager に委譲）。

        目的:
            - クローンの生成経路を WindowManager に一本化し、制限・選択同期・シグナル接続の整合性を保つ。
        """
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            mw.window_manager.clone_text_window(self)

        except Exception as e:
            logger.error("Failed to clone TextWindow via WindowManager: %s\n%s", e, traceback.format_exc())
            QMessageBox.critical(self, tr("msg_error"), f"Clone failed: {e}")

    def save_as_png(self) -> None:
        """現在の描画結果をPNG画像として保存し、結果をログに記録します。"""
        try:
            first_line = self.text.split("\n")[0]
            file_name, _ = QFileDialog.getSaveFileName(
                self, tr("title_save_png"), f"{first_line}.png", "PNG Files (*.png)"
            )

            if file_name:
                self._update_text_immediate()
                pixmap = self.pixmap()
                if pixmap:
                    if pixmap.save(file_name, "PNG"):
                        logger.info(f"Successfully saved PNG: {file_name}")
                    else:
                        raise IOError(f"Failed to save image file at {file_name}")
                else:
                    raise ValueError("Pixmap is empty, cannot save.")

        except Exception as e:
            logger.error(f"Error saving PNG: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, tr("msg_error"), f"Could not save image: {e}")

    def hide_all_other_windows(self) -> None:
        """自分以外のテキストを隠す（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.hide_all_other_text_windows(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to hide other text windows: {e}")
            traceback.print_exc()

    def close_all_other_windows(self) -> None:
        """自分以外のテキストを閉じる（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.close_all_other_text_windows(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to close other text windows: {e}")
            traceback.print_exc()

    def save_text_to_json(self) -> None:
        """設定をJSONファイルに保存します（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.save_window_to_json(self)

    def load_text_from_json(self) -> None:
        """JSONファイルから設定を読み込みます（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.load_window_from_json(self)

    def toggle_text_gradient(self) -> None:
        self.set_undoable_property("text_gradient_enabled", not self.text_gradient_enabled, "update_text")

    def toggle_background_gradient(self) -> None:
        self.set_undoable_property("background_gradient_enabled", not self.background_gradient_enabled, "update_text")

    def edit_text_gradient(self) -> None:
        dialog = GradientEditorDialog(self.text_gradient, self.text_gradient_angle, self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Edit Text Gradient")
            self.set_undoable_property("text_gradient", dialog.get_gradient(), None)
            self.set_undoable_property("text_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def edit_background_gradient(self) -> None:
        dialog = GradientEditorDialog(self.background_gradient, self.background_gradient_angle, self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Edit Background Gradient")
            self.set_undoable_property("background_gradient", dialog.get_gradient(), None)
            self.set_undoable_property("background_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def _open_slider_dialog(
        self,
        title: str,
        label: str,
        min_val: float,
        max_val: float,
        initial_val: float,
        property_name: str,
        update_method_name: str,
        decimals: int = 0,
        suffix: str = "",
    ) -> None:
        """プレビュー中Undoなし・OKで1回Undoのスライダーダイアログ共通処理（TextWindow版）。

        Args:
            title (str): タイトル
            label (str): ラベル
            min_val (float): 最小
            max_val (float): 最大
            initial_val (float): 初期値（現在値）
            property_name (str): 変更するプロパティ名
            update_method_name (str): 更新メソッド名（例: update_text）
            decimals (int): 小数桁
            suffix (str): サフィックス
        """
        try:
            from ui.dialogs import PreviewCommitDialog

            # Cancel復帰用に「確定前の値」を保持
            try:
                old_value: Any = getattr(self, property_name)
            except Exception:
                old_value = initial_val

            # プレビュー適用（Undoなし）
            def on_preview(val: float) -> None:
                try:
                    # もとの型に寄せる（int/float）
                    target_type = type(old_value)
                    v = target_type(val)

                    setattr(self, property_name, v)
                    if update_method_name and hasattr(self, update_method_name):
                        getattr(self, update_method_name)()
                except Exception:
                    pass

            # 確定適用（Undoあり：1回だけ）
            def on_commit(val: float) -> None:
                try:
                    target_type = type(old_value)
                    new_value = target_type(val)

                    # 変化が無ければ戻して終了（Undoを積まない）
                    if new_value == old_value:
                        on_preview(float(old_value))
                        return

                    # Undo化された変更として積む（内部で command を積む）
                    self.set_undoable_property(property_name, new_value, update_method_name)
                except Exception:
                    pass

            dialog = PreviewCommitDialog(
                title=title,
                label=label,
                min_val=float(min_val),
                max_val=float(max_val),
                initial_val=float(old_value),
                on_preview=on_preview,
                on_commit=on_commit,
                parent=self,
                suffix=suffix,
                decimals=decimals,
            )
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open dialog: {e}")
            traceback.print_exc()

    def open_text_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_text_opacity"), tr("label_opacity"), 0, 100, self.text_opacity, "text_opacity", "update_text"
        )

    def open_background_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_bg_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_opacity,
            "background_opacity",
            "update_text",
        )

    def open_shadow_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.shadow_opacity,
            "shadow_opacity",
            "update_text",
        )

    def open_shadow_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_blur"),
            tr("label_blur"),
            0,
            100,
            self.shadow_blur,
            "shadow_blur",
            "update_text",
            suffix="%",
        )

    def open_shadow_scale_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_scale"),
            tr("label_shadow_scale"),
            0.01,
            10.0,
            self.shadow_scale,
            "shadow_scale",
            "update_text",
            decimals=2,
        )

    def open_text_gradient_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("menu_set_text_gradient_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.text_gradient_opacity,
            "text_gradient_opacity",
            "update_text",
        )

    def open_background_gradient_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("menu_set_bg_gradient_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_gradient_opacity,
            "background_gradient_opacity",
            "update_text",
        )

    def open_bg_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_bg_outline_width"),
            tr("label_bg_outline_width"),
            0.0,
            1.0,
            self.background_outline_width_ratio,
            "background_outline_width_ratio",
            "update_text",
            decimals=2,
        )

    def open_bg_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_bg_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_outline_opacity,
            "background_outline_opacity",
            "update_text",
        )

    def open_bg_corner_ratio_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_bg_corner"),
            tr("label_ratio"),
            0.0,
            2.0,
            self.background_corner_ratio,
            "background_corner_ratio",
            "update_text",
            decimals=2,
        )

    def open_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.outline_opacity,
            "outline_opacity",
            "update_text",
        )

    def open_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.outline_width,
            "outline_width",
            "update_text",
            decimals=1,
        )

    def open_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.outline_blur,
            "outline_blur",
            "update_text",
            suffix="%",
        )

    def open_second_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_second_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.second_outline_opacity,
            "second_outline_opacity",
            "update_text",
        )

    def open_second_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_second_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.second_outline_width,
            "second_outline_width",
            "update_text",
            decimals=1,
        )

    def open_second_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_second_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.second_outline_blur,
            "second_outline_blur",
            "update_text",
            suffix="%",
        )

    def open_third_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_third_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.third_outline_opacity,
            "third_outline_opacity",
            "update_text",
        )

    def open_third_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_third_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.third_outline_width,
            "third_outline_width",
            "update_text",
            decimals=1,
        )

    def open_third_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_third_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.third_outline_blur,
            "third_outline_blur",
            "update_text",
            suffix="%",
        )

    def set_shadow_offsets(self) -> None:
        old_x, old_y = self.shadow_offset_x, self.shadow_offset_y

        def preview_callback(x: float, y: float):
            self.shadow_offset_x, self.shadow_offset_y = x, y
            self.update_text()

        dialog = ShadowOffsetDialog(
            tr("title_set_shadow_offsets"), old_x, old_y, callback=preview_callback, parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            new_x, new_y = dialog.get_offsets()
            if old_x != new_x or old_y != new_y:
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.beginMacro("Set Shadow Offsets")
                self.set_undoable_property("shadow_offset_x", new_x, None)
                self.set_undoable_property("shadow_offset_y", new_y, "update_text")
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.endMacro()

    def toggle_background_outline(self) -> None:
        self.set_undoable_property("background_outline_enabled", not self.background_outline_enabled, "update_text")

    def change_background_outline_color(self) -> None:
        color = QColorDialog.getColor(self.background_outline_color, self)
        if color.isValid():
            self.set_undoable_property("background_outline_color", color, "update_text")

    def load_text_defaults(self) -> Dict[str, Any]:
        """各種デフォルト設定ファイルからスタイルを読み込む。"""
        # 1. 基礎（ハードコード）
        # 1. 基礎（WindowConfigから正解を取得）
        # Hardcoded dictionary is REMOVED. We use the Single Source of Truth.
        base_config = TextWindowConfig()
        defaults = base_config.model_dump()

        # 旧キー名互換マッピング（必要ならここで変換、あるいはConfig側でAlias対応）
        # 現在のコードベースでは TextWindow 側で getattr(self, "h_margin", ...) のように
        # 旧キー名を探す箇所自体がリファクタリング済みであれば不要だが、
        # load_text_defaults の戻り値が __init__ でどう使われるか確認が必要。
        # __init__ では self.config へのセットが主なら model_dump でOK。
        # ただし、__init__ 内で `defaults.get("h_margin", ...)` している箇所があるなら
        # マッピングが必要。
        # 今回の調査では TextWindow.__init__ は load_text_defaults の戻り値を
        # self.config に直接マージする形式ではなく、個別の属性として扱っている可能性がある。
        # しかし、今回は "Eradication" なので、Configの値を正とする。

        # 簡易マッピング: Configの新しいプロパティ名を旧来のキー名としてもアクセスできるようにする
        # （もし __init__ が旧キーに依存している場合のため）
        defaults["h_margin"] = base_config.char_spacing_h
        defaults["v_margin"] = base_config.line_spacing_v
        defaults["margin_top"] = base_config.v_margin_top
        defaults["margin_bottom"] = base_config.v_margin_bottom
        defaults["margin_left"] = base_config.v_margin_left
        defaults["margin_right"] = base_config.v_margin_right
        defaults["v_margin_top"] = base_config.v_margin_top
        defaults["v_margin_bottom"] = base_config.v_margin_bottom
        defaults["v_margin_left"] = base_config.v_margin_left
        defaults["v_margin_right"] = base_config.v_margin_right

        # 2. レガシー：横書き余白
        h_path = os.path.join(self.main_window.json_directory, "text_defaults.json")
        if os.path.exists(h_path):
            try:
                with open(h_path, "r") as f:
                    defaults.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load text defaults: {e}")

        # 3. レガシー：縦書き余白 (BUG FIX: これがロードされていなかった)
        v_path = os.path.join(self.main_window.json_directory, "text_defaults_vertical.json")
        if os.path.exists(v_path):
            try:
                with open(v_path, "r") as f:
                    defaults.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load vertical text defaults: {e}")

        # 4. モダン：Archetype (すべてのスタイル)
        if hasattr(self.main_window, "settings_manager"):
            archetype = self.main_window.settings_manager.load_text_archetype()
            if archetype:
                # Archetype のキー名が config 準拠 (horizontal_margin_ratio 等) なのでマッピング
                # load_text_defaults は従来辞書を返し、__init__ で直接属性に代入されている
                defaults.update(archetype)

        return defaults

    def open_spacing_settings(self) -> None:
        # 縦書き/横書きに応じた値でダイアログを初期化
        if self.is_vertical:
            # Vertical Mode: h_ratio=char_spacing, v_ratio=line_spacing
            dialog = TextSpacingDialog(
                self.char_spacing_v,
                self.line_spacing_v,
                self.v_margin_top_ratio,
                self.v_margin_bottom_ratio,
                self.v_margin_left_ratio,
                self.v_margin_right_ratio,
                self,
                is_vertical=True,
            )
        else:
            # Horizontal Mode: h_ratio=char_spacing, v_ratio=line_spacing
            dialog = TextSpacingDialog(
                self.char_spacing_h,
                self.line_spacing_h,
                self.margin_top_ratio,
                self.margin_bottom_ratio,
                self.margin_left_ratio,
                self.margin_right_ratio,
                self,
                is_vertical=False,
            )

        if dialog.exec() == QDialog.Accepted:
            values_dict = dialog.get_values_dict()
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Change Spacing")

            # 辞書の最後のキー以外は update_text を None に
            keys = list(values_dict.keys())
            for key in keys[:-1]:
                self.set_undoable_property(key, values_dict[key], None)
            # 最後のキーで update_text を呼ぶ
            if keys:
                self.set_undoable_property(keys[-1], values_dict[keys[-1]], "update_text")

            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def show_property_panel(self) -> None:
        self.sig_request_property_panel.emit(self)

    def propagate_scale_to_children(self, ratio: float) -> None:
        """子ウィンドウに対してスケーリングを伝搬させる。

        Args:
            ratio (float): スケール倍率。
        """
        if not self.child_windows:
            return
        parent_center = self.geometry().center()
        for child in self.child_windows:
            try:
                vec = child.geometry().center() - parent_center
                new_center = parent_center + QPoint(int(vec.x() * ratio), int(vec.y() * ratio))
                if hasattr(child, "font_size"):
                    child.font_size *= ratio
                    child.update_text()
                elif hasattr(child, "scale_factor"):
                    child.scale_factor *= ratio
                    child.update_image()
                child.move(int(new_center.x() - child.width() / 2), int(new_center.y() - child.height() / 2))
                if hasattr(child, "propagate_scale_to_children"):
                    child.propagate_scale_to_children(ratio)
            except Exception:
                pass  # Error propagating scale

    # --- UI Menu ---

    def show_context_menu(self, pos: QPoint) -> None:
        """コンテキストメニューを構築して表示する。
        Args:
            pos (QPoint): 表示位置。
        """
        try:
            builder = ContextMenuBuilder(self, self.main_window)

            builder.add_connect_group_menu()
            builder.add_action("menu_show_properties", self.show_property_panel)
            builder.add_separator()

            # スタイルプリセット
            if hasattr(self.main_window, "style_manager"):
                style_menu = builder.add_submenu("menu_style_presets")
                builder.add_action("menu_open_style_gallery", self.open_style_gallery, parent_menu=style_menu)
                builder.add_separator(parent_menu=style_menu)
                builder.add_action(
                    "menu_save_style",
                    lambda: self.main_window.style_manager.save_text_style(self),
                    parent_menu=style_menu,
                )
                builder.add_action(
                    "menu_load_style_file",
                    lambda: self.main_window.style_manager.load_text_style(self),
                    parent_menu=style_menu,
                )

            builder.add_separator()
            builder.add_action("menu_change_text", self.change_text)
            builder.add_action(
                "menu_toggle_task_mode",
                lambda checked: self.set_content_mode("task" if checked else "note"),
                checkable=True,
                checked=self.is_task_mode(),
            )
            builder.add_action("menu_add_text", self.add_text_window)
            builder.add_action("menu_clone_text", self.clone_text)
            builder.add_action("menu_save_png", self.save_as_png)
            builder.add_action("menu_save_json", self.save_text_to_json)
            builder.add_action("menu_load_json", self.main_window.file_manager.load_scene_from_json)
            builder.add_separator()

            # テキスト表示
            builder.add_action(
                "menu_toggle_text", self.toggle_text_visibility, checkable=True, checked=(self.text_opacity > 0)
            )

            # テキスト設定
            text_menu = builder.add_submenu("menu_text_settings")
            builder.add_action("menu_change_font", self.change_font, parent_menu=text_menu)
            builder.add_action("menu_change_color", self.change_font_color, parent_menu=text_menu)
            builder.add_action("menu_change_text_opacity", self.open_text_opacity_dialog, parent_menu=text_menu)
            builder.add_separator()

            # 背景
            builder.add_action(
                "menu_toggle_background",
                self.toggle_background_visibility,
                checkable=True,
                checked=(self.background_opacity > 0),
            )
            builder.add_action(
                "menu_toggle_bg_outline",
                self.toggle_background_outline,
                checkable=True,
                checked=self.background_outline_enabled,
            )

            bg_menu = builder.add_submenu("menu_bg_settings")
            builder.add_action("menu_change_bg_color", self.change_background_color, parent_menu=bg_menu)
            builder.add_action("menu_change_bg_opacity", self.open_background_opacity_dialog, parent_menu=bg_menu)
            builder.add_separator(parent_menu=bg_menu)
            builder.add_action(
                "menu_change_bg_outline_color", self.change_background_outline_color, parent_menu=bg_menu
            )
            builder.add_action("menu_change_bg_outline_width", self.open_bg_outline_width_dialog, parent_menu=bg_menu)
            builder.add_action(
                "menu_change_bg_outline_opacity", self.open_bg_outline_opacity_dialog, parent_menu=bg_menu
            )
            builder.add_separator(parent_menu=bg_menu)
            builder.add_action("menu_set_bg_corner", self.open_bg_corner_ratio_dialog, parent_menu=bg_menu)
            builder.add_separator()

            # 影
            builder.add_action("menu_toggle_shadow", self.toggle_shadow, checkable=True, checked=self.shadow_enabled)
            shadow_menu = builder.add_submenu("menu_shadow_settings")
            builder.add_action("menu_change_shadow_color", self.change_shadow_color, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_opacity", self.open_shadow_opacity_dialog, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_scale", self.open_shadow_scale_dialog, parent_menu=shadow_menu)
            builder.add_action("menu_set_shadow_offsets", self.set_shadow_offsets, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_blur", self.open_shadow_blur_dialog, parent_menu=shadow_menu)
            builder.add_separator()

            # グラデーション（テキスト）
            builder.add_action(
                "menu_toggle_text_gradient",
                self.toggle_text_gradient,
                checkable=True,
                checked=self.text_gradient_enabled,
            )
            grad_text_menu = builder.add_submenu("menu_text_gradient_settings")
            builder.add_action("menu_edit_text_gradient", self.edit_text_gradient, parent_menu=grad_text_menu)
            builder.add_action(
                "menu_set_text_gradient_opacity", self.open_text_gradient_opacity_dialog, parent_menu=grad_text_menu
            )
            builder.add_separator()

            # グラデーション（背景）
            builder.add_action(
                "menu_toggle_bg_gradient",
                self.toggle_background_gradient,
                checkable=True,
                checked=self.background_gradient_enabled,
            )
            grad_bg_menu = builder.add_submenu("menu_bg_gradient_settings")
            builder.add_action("menu_edit_bg_gradient", self.edit_background_gradient, parent_menu=grad_bg_menu)
            builder.add_action(
                "menu_set_bg_gradient_opacity", self.open_background_gradient_opacity_dialog, parent_menu=grad_bg_menu
            )
            builder.add_separator()

            # 縁取り（1〜3）
            outline_parent_menu = builder.add_submenu("menu_outline_parent_settings")
            for i, prefix in enumerate(["", "second_", "third_"], 1):
                enabled = getattr(self, f"{prefix}outline_enabled")
                builder.add_action(
                    f"menu_toggle_{prefix}outline",
                    getattr(self, f"toggle_{prefix}outline"),
                    checkable=True,
                    checked=enabled,
                    parent_menu=outline_parent_menu,
                )
                sub = builder.add_submenu(f"menu_{prefix}outline_settings", parent_menu=outline_parent_menu)
                builder.add_action(
                    f"menu_change_{prefix}outline_color",
                    getattr(self, f"change_{prefix}outline_color"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_opacity",
                    getattr(self, f"open_{prefix}outline_opacity_dialog"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_width",
                    getattr(self, f"open_{prefix}outline_width_dialog"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_blur",
                    getattr(self, f"open_{prefix}outline_blur_dialog"),
                    parent_menu=sub,
                )
                if i < 3:
                    builder.add_separator(parent_menu=outline_parent_menu)

            builder.add_separator()

            # 縦書き設定
            builder.add_action(
                "menu_toggle_vertical", self.toggle_vertical_text, checkable=True, checked=self.is_vertical
            )

            builder.add_separator()

            # 余白設定
            builder.add_action("menu_margin_settings", self.open_spacing_settings)
            builder.add_separator()

            # --- アニメ関連は完全撤去（MainWindowのAnimationタブに一本化） ---

            builder.add_action(
                "menu_toggle_frontmost", self.toggle_frontmost, checkable=True, checked=self.is_frontmost
            )
            builder.add_action("menu_hide_text", self.hide_action)
            builder.add_action("menu_hide_others", self.hide_all_other_windows)
            builder.add_action("menu_show_text", self.show_action)

            builder.add_separator()

            builder.add_action("menu_close_others", self.close_all_other_windows)
            builder.add_action("menu_close_text", self.close)

            builder.add_separator()

            builder.add_action(
                "menu_lock_transform",
                lambda checked: self.set_undoable_property("is_locked", bool(checked), None),
                checkable=True,
                checked=bool(getattr(self, "is_locked", False)),
            )

            builder.add_separator()

            builder.add_action(
                "menu_click_through",
                lambda: self.set_click_through(not self.is_click_through),
                checkable=True,
                checked=self.is_click_through,
            )

            builder.exec(self.mapToGlobal(pos))

        except Exception:
            pass  # An error occurred in show_context_menu
            # (以下略とさせていただきますが、メニュー内の load_scene_from_json 部分のみの差し替えでOKです)

    def open_style_gallery(self) -> None:
        """スタイルギャラリーダイアログを表示し、選択されたスタイルを適用する。"""
        dialog = StyleGalleryDialog(self.main_window.style_manager, self)
        if dialog.exec() == QDialog.Accepted:
            json_path = dialog.get_selected_style_path()
            if json_path:
                self.main_window.style_manager.load_text_style(self, json_path)
