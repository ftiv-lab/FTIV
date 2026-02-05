from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMessageBox

from utils.translator import tr


class ShortcutMixin:
    """ショートカットキー処理を提供する Mixin。

    Undo/Redoアクション生成、緊急ショートカット登録など。
    """

    def create_undo_redo_actions(self) -> None:
        """Undo/Redoアクションの生成とショートカットの設定。"""
        # self.undo_stack, self.undo_action, self.redo_action は MainWindow で管理
        if hasattr(self, "undo_stack"):
            self.undo_action = self.undo_stack.createUndoAction(self, tr("menu_undo"))
            self.undo_action.setShortcut(QKeySequence.Undo)
            self.undo_action.setShortcutContext(Qt.ApplicationShortcut)
            self.addAction(self.undo_action)

            self.redo_action = self.undo_stack.createRedoAction(self, tr("menu_redo"))
            self.redo_action.setShortcut(QKeySequence.Redo)
            self.redo_action.setShortcutContext(Qt.ApplicationShortcut)
            self.addAction(self.redo_action)

    def _register_emergency_shortcuts(self) -> None:
        """操作不能の復旧用・緊急ショートカットを登録する。

        ショートカット（ApplicationShortcut）:
            - Ctrl+Alt+Shift+R: 全クリック透過解除
            - Ctrl+Alt+Shift+M: MainWindowを前面に出す
            - Ctrl+Alt+Shift+H: 全ウィンドウ表示
        """
        # すでに登録済みなら二重登録しない（保険）
        if hasattr(self, "_emergency_shortcuts_registered") and bool(getattr(self, "_emergency_shortcuts_registered")):
            return
        self._emergency_shortcuts_registered = True

        try:
            # 1) 全クリック透過解除
            act_rescue_ct = QAction(self)  # type: ignore[call-overload]
            act_rescue_ct.setShortcut(QKeySequence("Ctrl+Alt+Shift+R"))
            act_rescue_ct.setShortcutContext(Qt.ApplicationShortcut)
            act_rescue_ct.triggered.connect(self.emergency_disable_all_click_through)
            self.addAction(act_rescue_ct)

            # 2) MainWindow を前面に出す
            act_raise = QAction(self)  # type: ignore[call-overload]
            act_raise.setShortcut(QKeySequence("Ctrl+Alt+Shift+M"))
            act_raise.setShortcutContext(Qt.ApplicationShortcut)
            act_raise.triggered.connect(self.emergency_raise_main_window)
            self.addAction(act_raise)

            # 3) 全ウィンドウ表示
            act_show_all = QAction(self)  # type: ignore[call-overload]
            act_show_all.setShortcut(QKeySequence("Ctrl+Alt+Shift+H"))
            act_show_all.setShortcutContext(Qt.ApplicationShortcut)
            act_show_all.triggered.connect(self.emergency_show_all_windows)
            self.addAction(act_show_all)

        except Exception as e:
            QMessageBox.warning(self, tr("msg_warning"), f"Failed to register emergency shortcuts: {e}")

    def emergency_disable_all_click_through(self) -> None:
        """緊急：全ウィンドウのクリック透過を解除する。"""
        try:
            # 既存の救出ボタンと同じ処理に寄せる
            if hasattr(self, "disable_all_click_through"):
                self.disable_all_click_through()

            # ConnectorLabel も含めて確実に解除（label_window は text_windows に含まれないため）
            try:
                for conn in list(getattr(self, "connectors", [])):
                    lw = getattr(conn, "label_window", None)
                    if lw is None:
                        continue
                    try:
                        if hasattr(lw, "set_click_through"):
                            lw.set_click_through(False)
                        elif hasattr(lw, "is_click_through"):
                            lw.is_click_through = False
                    except Exception:
                        pass
            except Exception:
                pass

            # 操作盤を前面へ
            self.emergency_raise_main_window()

            # フッター通知（あれば）
            if hasattr(self, "show_status_message"):
                self.show_status_message("Click-through OFF (Emergency)", timeout_ms=1500)
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Emergency click-through rescue failed: {e}")

    def emergency_raise_main_window(self) -> None:
        """緊急：MainWindow を前面に出す（最前面固定はしない）。"""
        try:
            # self は MainWindow
            self.show()
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def emergency_show_all_windows(self) -> None:
        """緊急：全ウィンドウを表示する（hide解除の迷子救済）。"""
        try:
            if hasattr(self, "show_all_everything"):
                self.show_all_everything()

            # ConnectorLabelも表示（text_windows に含まれないため）
            try:
                for conn in list(getattr(self, "connectors", [])):
                    lw = getattr(conn, "label_window", None)
                    if lw is None:
                        continue
                    try:
                        if hasattr(lw, "show_action"):
                            lw.show_action()
                        else:
                            lw.show()
                    except Exception:
                        pass
            except Exception:
                pass

            # 操作盤を前面へ
            self.emergency_raise_main_window()

            if hasattr(self, "show_status_message"):
                self.show_status_message("Show All Windows (Emergency)", timeout_ms=1500)
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Emergency show-all failed: {e}")
