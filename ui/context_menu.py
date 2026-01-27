# ui/context_menu.py

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from utils.translator import tr


class ContextMenuBuilder:
    """コンテキストメニュー構築を補助するクラス"""

    def __init__(self, target_window, main_window):
        self.window = target_window
        self.main_window = main_window
        self.menu = QMenu(target_window)
        self.menu.setStyleSheet("""
            QMenu { font-size: 14px; background-color: #eeeeee; border: 1px solid #aaa; }
            QMenu::item:selected { background-color: #99ccff; }
            QMenu::item { color: black; }
        """)

    def add_action(self, text_key, slot=None, checkable=False, checked=False, parent_menu=None):
        target_menu = parent_menu if parent_menu else self.menu
        action = QAction(tr(text_key), self.window)

        if slot:
            # checkableなActionはtriggered(bool)シグナルを発行する。
            # slotが引数を受け取らない場合にTypeErrorになるのを防ぐラッパーを導入。
            if checkable:

                def slot_wrapper(checked_status):
                    try:
                        # まず引数付きで呼び出しを試みる (例: toggle_fade(enabled: bool))
                        slot(checked_status)
                    except TypeError:
                        # 失敗した場合、引数なしで呼び出す (例: toggle_frontmost())
                        slot()

                action.triggered.connect(slot_wrapper)
            else:
                # checkableでなければ、通常通り接続
                action.triggered.connect(slot)

        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)

        target_menu.addAction(action)
        return action

    def add_submenu(self, text_key, parent_menu=None):
        target_menu = parent_menu if parent_menu else self.menu
        submenu = target_menu.addMenu(tr(text_key))
        return submenu

    def add_separator(self, parent_menu=None):
        target_menu = parent_menu if parent_menu else self.menu
        target_menu.addSeparator()

    def add_connect_group_menu(self):
        """接続・グループ化メニュー（共通機能）"""
        sub = self.add_submenu("menu_connect_group_ops")

        self.add_action(
            "menu_connect_to_last",
            lambda: self.main_window.window_manager.handle_connect_request(self.window),
            parent_menu=sub,
        )

        self.add_action(
            "menu_disconnect",
            lambda: self.main_window.window_manager.handle_disconnect_request(self.window),
            parent_menu=sub,
        )

        sub.addSeparator()

        self.add_action(
            "menu_group_with_last",
            lambda: self.main_window.window_manager.handle_group_request(self.window),
            parent_menu=sub,
        )

        self.add_action(
            "menu_ungroup",
            lambda: self.main_window.window_manager.handle_ungroup_request(self.window),
            parent_menu=sub,
        )

    def exec(self, pos):
        self.menu.exec(pos)
