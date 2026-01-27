# -*- coding: utf-8 -*-
import json
import logging
import os
from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QFontDialog, QMessageBox

from utils.translator import tr

logger = logging.getLogger(__name__)


class BulkOperationManager:
    """一括操作（表示/非表示、閉じる、スタイル変更など）を管理するクラス。"""

    def __init__(self, main_window: Any):
        self.mw = main_window

    # ==========================================
    # Global Visibility & Lifecycle
    # ==========================================

    def show_all_everything(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.show_all_text_windows()
            self.mw.window_manager.show_all_image_windows()

    def hide_all_everything(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.hide_all_text_windows()
            self.mw.window_manager.hide_all_image_windows()

    def close_all_everything(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.clear_all()

    # ==========================================
    # ==========================================
    # Bulk Text Window Actions
    # ==========================================

    def close_all_image_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.close_all_image_windows()

    def show_all_image_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.show_all_image_windows()

    def hide_all_image_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.hide_all_image_windows()

    def close_all_text_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.close_all_text_windows()

    def show_all_text_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.show_all_text_windows()

    def hide_all_text_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.hide_all_text_windows()

    def toggle_text_click_through(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.toggle_text_click_through()

    def toggle_image_click_through(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.toggle_image_click_through()

    def toggle_all_frontmost_text_windows(self) -> None:
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.toggle_all_frontmost_text_windows()

    def disable_all_click_through(self) -> None:
        for w in self.mw.text_windows:
            w.set_click_through(False)
        for w in self.mw.image_windows:
            w.set_click_through(False)

    def show_text_window_list(self) -> None:
        """テキストウィンドウの一覧をメッセージボックスで表示。"""
        try:
            if not self.mw.text_windows:
                QMessageBox.information(self.mw, tr("title_text_list"), tr("msg_no_text_windows"))
                return
            text_list = "\n".join([f"{i + 1}: {window.text[:30]}..." for i, window in enumerate(self.mw.text_windows)])
            QMessageBox.information(self.mw, tr("title_text_list"), text_list)
        except Exception as e:
            QMessageBox.critical(self.mw, tr("msg_error"), f"Error listing windows: {e}")

    def show_text_window_menu(self, text_window: Any, pos: QPoint) -> None:
        """特定のテキストウィンドウのコンテキストメニューを表示。"""
        text_window.show_context_menu(self.mw.mapToGlobal(pos))

    # ==========================================
    # Bulk Styling Actions
    # ==========================================

    def change_all_fonts(self) -> None:
        """全てのテキストウィンドウのフォントを一括変更（Undo/Redo対応）。"""
        if not self.mw.text_windows:
            return

        # 既存のフォントをデフォルトとしてダイアログを開く
        initial_font = QFont(self.mw.text_windows[0].font_family, self.mw.text_windows[0].font_size)
        font_dialog = QFontDialog(self.mw)
        font_dialog.setCurrentFont(initial_font)

        if font_dialog.exec() == QFontDialog.Accepted:
            selected_font = font_dialog.selectedFont()

            # Undo操作を「フォント一括変更」として1つにまとめる
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.beginMacro("Batch Change Font")

            for text_window in self.mw.text_windows:
                # 1. undo可能なプロパティ変更としてフォントファミリーとサイズをセット
                #    ここではまだ再描画しない (None を指定)
                text_window.set_undoable_property("font_family", selected_font.family(), None)
                text_window.set_undoable_property("font_size", selected_font.pointSize(), None)

                # 2. フォントの種類（等幅かプロポーショナルか）に応じて縦書きモードを更新
                if hasattr(text_window, "auto_detect_offset_mode"):
                    text_window.auto_detect_offset_mode(selected_font)

                # 3. 最後に再描画をかける
                text_window.update_text()

            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

    def set_all_text_vertical(self) -> None:
        if not self.mw.text_windows:
            return
        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Set All Vertical")
        for window in self.mw.text_windows:
            window.set_undoable_property("is_vertical", True, "update_text")
        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.endMacro()

    def set_all_text_horizontal(self) -> None:
        if not self.mw.text_windows:
            return
        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Set All Horizontal")
        for window in self.mw.text_windows:
            window.set_undoable_property("is_vertical", False, "update_text")
        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.endMacro()

    def set_all_offset_mode_a(self) -> None:
        for window in self.mw.text_windows:
            window.set_offset_mode_a()

    def set_all_offset_mode_b(self) -> None:
        for window in self.mw.text_windows:
            window.set_offset_mode_b()

    def set_default_text_spacing(self) -> None:
        """デフォルトおよび現在のテキストウィンドウの余白設定を一括適用。"""
        # 遅延インポート (循環参照回避のため)
        from ui.dialogs import TextSpacingDialog

        json_path = os.path.join(self.mw.json_directory, "text_defaults.json")
        defaults = {
            "h_margin": 0.0,
            "v_margin": 0.2,
            "margin_top": 0.3,
            "margin_bottom": 0.3,
            "margin_left": 0.3,
            "margin_right": 0.0,
        }

        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    defaults.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load text defaults from {json_path}: {e}")

        dialog = TextSpacingDialog(*defaults.values(), self.mw)
        if dialog.exec() == QDialog.Accepted:
            new_values = dialog.get_values()

            # 1. 保存
            try:
                with open(json_path, "w") as f:
                    json.dump(new_values, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save text defaults: {e}")

            # 2. 現在のウィンドウに適用
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.beginMacro("Apply Spacing to All")

            for w in self.mw.text_windows:
                # 変更があればUndo登録
                #  (すべてを一発で変えるメソッドがあればよいが、set_undoable_propertyを個別に呼ぶ)
                #  ここでは簡略化のため直接属性セット＋update_text呼び出しの形にするか、
                #  あるいは set_undoable_property をループで呼ぶ。

                # ここでは既存ロジックを尊重しつつ、undo対応プロパティとしてセットする
                w.set_undoable_property("h_margin", new_values["h_margin"], None)
                w.set_undoable_property("v_margin", new_values["v_margin"], None)
                w.set_undoable_property("margin_top", new_values["margin_top"], None)
                w.set_undoable_property("margin_bottom", new_values["margin_bottom"], None)
                w.set_undoable_property("margin_left", new_values["margin_left"], None)
                w.set_undoable_property("margin_right", new_values["margin_right"], None)
                w.update_text()

            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

            QMessageBox.information(self.mw, tr("msg_info"), tr("msg_settings_saved_applied"))
