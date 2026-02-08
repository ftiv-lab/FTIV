# -*- coding: utf-8 -*-
import json
import logging
import os
from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QMessageBox

from models.window_config import TextWindowConfig
from utils.font_dialog import choose_font
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

    def show_image_window_context_menu(self, image_window: Any) -> None:
        """特定の画像ウィンドウのコンテキストメニューを表示。"""
        # ImageWindow.show_context_menu は引数なしか、QPointかを要確認
        # 通常は QCursor.pos() を使う実装が多いが、シグネチャによる
        # ここでは cursor position を使用する前提
        try:
            from PySide6.QtGui import QCursor

            image_window.show_context_menu(QCursor.pos())
        except Exception:
            pass

    def toggle_all_frontmost_image_windows(self) -> None:
        """全画像ウィンドウの最前面状態をトグル切り替え。"""
        if not hasattr(self.mw, "image_windows") or not self.mw.image_windows:
            return

        # 最初のウィンドウの状態を見て反転
        first = self.mw.image_windows[0]
        target_state = not getattr(first, "is_frontmost", False)

        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Toggle All Images Frontmost")

        for w in self.mw.image_windows:
            if hasattr(w, "set_undoable_property"):
                w.set_undoable_property("is_frontmost", target_state, None)
            else:
                w.set_frontmost(target_state)

        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.endMacro()

    # ==========================================
    # Bulk Styling Actions
    # ==========================================

    def change_all_fonts(self) -> None:
        """全てのテキストウィンドウのフォントを一括変更（Undo/Redo対応）。"""
        if not self.mw.text_windows:
            return

        # 既存のフォントをデフォルトとしてダイアログを開く
        initial_font = QFont(self.mw.text_windows[0].font_family, self.mw.text_windows[0].font_size)
        selected_font = choose_font(self.mw, initial_font)
        if selected_font is not None:
            # Undo操作を「フォント一括変更」として1つにまとめる
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.beginMacro("Batch Change Font")

            for text_window in self.mw.text_windows:
                # 1. undo可能なプロパティ変更としてフォントファミリーとサイズをセット
                #    ここではまだ再描画しない (None を指定)
                text_window.set_undoable_property("font_family", selected_font.family(), None)
                text_window.set_undoable_property("font_size", selected_font.pointSize(), None)

                # 2. フォントの種類（等幅かプロポーショナルか）に応じて縦書きモードを更新
                # Note: auto_detect_offset_mode is specific to TextWindow, strictly we should add it to protocol
                # or keep hasattr if it's optional feature. For now, we keep hasattr for specific mixin methods,
                # but STRICTLY enforce set_undoable_property.
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

    def set_default_text_spacing(self) -> None:
        """デフォルトおよび現在のテキストウィンドウの余白設定を一括適用。

        Note:
            一括設定は横書きモードの設定を全ウィンドウに適用する。
            個別ウィンドウの縦書き設定は各ウィンドウのコンテキストメニューから行う。
        """
        from ui.dialogs import TextSpacingDialog

        json_path = os.path.join(self.mw.json_directory, "text_defaults.json")
        # Use Single Source of Truth
        base_config = TextWindowConfig()
        defaults = base_config.model_dump()
        # Map Config properties to Dialog expectations (Legacy Keys)
        defaults["h_margin"] = base_config.char_spacing_h
        defaults["v_margin"] = base_config.line_spacing_h
        defaults["margin_top"] = base_config.v_margin_top
        defaults["margin_bottom"] = base_config.v_margin_bottom
        defaults["margin_left"] = base_config.v_margin_left
        defaults["margin_right"] = base_config.v_margin_right

        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    defaults.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load text defaults from {json_path}: {e}")

        # 横書きモードとしてダイアログを表示（一括設定は横書き基準）
        dialog = TextSpacingDialog(
            defaults["h_margin"],
            defaults["v_margin"],
            defaults["margin_top"],
            defaults["margin_bottom"],
            defaults["margin_left"],
            defaults["margin_right"],
            self.mw,
            is_vertical=False,
        )

        if dialog.exec() == QDialog.Accepted:
            # 新しい get_values_dict() メソッドを使用
            values_dict = dialog.get_values_dict()

            # 保存用の形式に変換（後方互換性）
            save_values = {
                "h_margin": values_dict.get("horizontal_margin_ratio", 0.0),
                "v_margin": values_dict.get("vertical_margin_ratio", 0.0),
                "margin_top": values_dict.get("margin_top_ratio", 0.0),
                "margin_bottom": values_dict.get("margin_bottom_ratio", 0.0),
                "margin_left": values_dict.get("margin_left_ratio", 0.0),
                "margin_right": values_dict.get("margin_right_ratio", 0.0),
            }

            # 1. 保存
            try:
                with open(json_path, "w") as f:
                    json.dump(save_values, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save text defaults: {e}")

            # 2. 現在のウィンドウに適用
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.beginMacro("Apply Spacing to All")

            # 辞書から直接プロパティ名と値を取得
            prop_items = list(values_dict.items())
            for w in self.mw.text_windows:
                for prop_name, value in prop_items[:-1]:
                    w.set_undoable_property(prop_name, value, None)
                # 最後のプロパティで update_text を呼ぶ
                last_prop, last_val = prop_items[-1]
                w.set_undoable_property(last_prop, last_val, "update_text")

            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

            QMessageBox.information(self.mw, tr("msg_info"), tr("msg_settings_saved_applied"))

    def set_default_text_spacing_vertical(self) -> None:
        """縦書きモードのデフォルト余白設定を一括適用。"""
        from ui.dialogs import TextSpacingDialog

        json_path = os.path.join(self.mw.json_directory, "text_defaults_vertical.json")
        # Use Single Source of Truth
        base_config = TextWindowConfig()
        defaults = base_config.model_dump()
        # Map Config properties to Dialog expectations
        defaults["v_margin_top"] = base_config.v_margin_top
        defaults["v_margin_bottom"] = base_config.v_margin_bottom
        defaults["v_margin_left"] = base_config.v_margin_left
        defaults["v_margin_right"] = base_config.v_margin_right

        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    defaults.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load vertical text defaults from {json_path}: {e}")

        # 縦書きモードとしてダイアログを表示
        dialog = TextSpacingDialog(
            0.0,  # h_ratio (縦書きでは文字間隔として使用)
            0.0,  # v_ratio (縦書きでは行間隔として使用)
            defaults["v_margin_top"],
            defaults["v_margin_bottom"],
            defaults["v_margin_left"],
            defaults["v_margin_right"],
            self.mw,
            is_vertical=True,
        )

        if dialog.exec() == QDialog.Accepted:
            values_dict = dialog.get_values_dict()

            # 保存用の形式
            save_values = {
                "v_margin_top": values_dict.get("v_margin_top_ratio", 0.0),
                "v_margin_bottom": values_dict.get("v_margin_bottom_ratio", 0.0),
                "v_margin_left": values_dict.get("v_margin_left_ratio", 0.0),
                "v_margin_right": values_dict.get("v_margin_right_ratio", 0.0),
            }

            # 1. 保存
            try:
                with open(json_path, "w") as f:
                    json.dump(save_values, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save vertical text defaults: {e}")

            # 2. 現在の縦書きウィンドウに適用
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.beginMacro("Apply Vertical Spacing to All")

            # 縦書き専用プロパティのみ適用
            prop_items = list(values_dict.items())
            for w in self.mw.text_windows:
                # 縦書きウィンドウのみに適用
                if getattr(w, "is_vertical", False):
                    for prop_name, value in prop_items[:-1]:
                        w.set_undoable_property(prop_name, value, None)
                    last_prop, last_val = prop_items[-1]
                    w.set_undoable_property(last_prop, last_val, "update_text")

            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

            QMessageBox.information(self.mw, tr("msg_info"), tr("msg_settings_saved_applied"))
