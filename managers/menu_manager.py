from functools import partial
from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMessageBox

from utils.translator import tr


class MenuManager:
    """コンテキストメニューの管理を行うクラス。"""

    def __init__(self, main_window: Any):
        self.mw = main_window

    def show_context_menu(self, pos: QPoint) -> None:
        """メインウィンドウの背景右クリックメニュー構築。"""
        try:
            menu = QMenu(self.mw)
            menu.addAction(tr("menu_about")).triggered.connect(self.mw.show_about_dialog)
            menu.addSeparator()
            menu.setStyleSheet(
                "QMenu { font-size: 14px; background-color: #eee; color: black; } QMenu::item:selected { background-color: #9cf; }"
            )

            # テキスト
            menu.addAction(tr("menu_add_text")).triggered.connect(self.mw.add_text_window)
            t_list = menu.addMenu(tr("title_text_list"))
            t_list.setEnabled(bool(self.mw.text_windows))
            for i, tw in enumerate(self.mw.text_windows):
                lbl = tw.text.split("\n")[0][:20] or "Untitled"
                t_list.addAction(f"{i + 1}: {lbl}").triggered.connect(partial(self.mw.show_text_window_menu, tw, pos))

            menu.addAction(tr("menu_change_all_font")).triggered.connect(self.mw.change_all_fonts)

            menu.addSeparator()
            menu.addAction(tr("menu_save_json")).triggered.connect(self.mw.file_manager.save_scene_to_json)
            menu.addAction(tr("menu_load_json")).triggered.connect(self.mw.file_manager.load_scene_from_json)
            menu.addAction(tr("menu_hide_all_text")).triggered.connect(self.mw.hide_all_text_windows)
            menu.addAction(tr("menu_show_all_text")).triggered.connect(self.mw.show_all_text_windows)
            menu.addAction(tr("menu_switch_all_front_text")).triggered.connect(
                self.mw.toggle_all_frontmost_text_windows
            )
            menu.addAction(tr("menu_stop_all_text_anim")).triggered.connect(self.mw.stop_all_text_animations)
            menu.addAction(tr("menu_close_all_text")).triggered.connect(self.mw.close_all_text_windows)

            menu.addSeparator()

            # 画像
            menu.addAction(tr("menu_add_image")).triggered.connect(self.mw.add_image)
            i_list = menu.addMenu(tr("title_image_list"))
            i_list.setEnabled(bool(self.mw.image_windows))
            for iw in self.mw.image_windows:
                i_list.addAction(iw.get_filename()).triggered.connect(
                    partial(self.mw.show_image_window_context_menu, iw)
                )

            menu.addAction(tr("menu_set_all_image_size")).triggered.connect(self.mw.set_all_image_size_percentage)
            menu.addAction(tr("menu_set_all_image_opacity")).triggered.connect(self.mw.set_all_image_opacity)

            r_menu = menu.addMenu(tr("menu_set_all_image_rotation_90"))
            for angle in [0, 90, 180, 270]:
                a = QAction(f"{angle}°", self.mw, checkable=True)
                a.triggered.connect(self._create_all_rotation_action_handler(angle))
                if self.mw.image_windows and all(int(w.rotation_angle) == angle for w in self.mw.image_windows):
                    a.setChecked(True)
                r_menu.addAction(a)

            menu.addAction(tr("menu_toggle_all_anim")).triggered.connect(self.mw.toggle_all_image_animation_speed)
            menu.addAction(tr("menu_reset_all_flips")).triggered.connect(self.mw.reset_all_flips)
            menu.addAction(tr("menu_show_all_images")).triggered.connect(self.mw.show_all_image_windows)
            menu.addAction(tr("menu_switch_all_front_image")).triggered.connect(
                self.mw.toggle_all_frontmost_image_windows
            )
            menu.addAction(tr("menu_align_images")).triggered.connect(self.mw.open_align_dialog)
            menu.addAction(tr("menu_close_all_images")).triggered.connect(self.mw.close_all_images)

            menu.exec(self.mw.mapToGlobal(pos))
        except Exception as e:
            QMessageBox.critical(self.mw, "Error", f"Context menu error: {e}")

    def _create_all_rotation_action_handler(self, angle: int):
        """画像一括回転のためのクロージャを生成して返す。"""

        # MainWindowから移動してきたので self.mw を使用
        def handler():
            for w in self.mw.image_windows:
                if hasattr(w, "set_rotation"):
                    w.set_rotation(angle)

        return handler
