# utils/commands.py

import shiboken6  # PySide6のオブジェクト生存確認用
from PySide6.QtGui import QUndoCommand


class PropertyChangeCommand(QUndoCommand):
    def __init__(self, target, property_name, old_value, new_value, update_method_name=None):
        super().__init__()
        self.target = target
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.update_method_name = update_method_name
        self.setText(f"Change {property_name}")

    def _is_target_valid(self):
        # オブジェクトが有効(削除されていない)かチェック
        return self.target and shiboken6.isValid(self.target)

    def redo(self):
        if not self._is_target_valid():
            return  # ターゲットがいなければ何もしない

        try:
            setattr(self.target, self.property_name, self.new_value)
            self._update_target()
        except RuntimeError:
            pass  # 万が一の競合エラー回避

    def undo(self):
        if not self._is_target_valid():
            return

        try:
            setattr(self.target, self.property_name, self.old_value)
            self._update_target()
        except RuntimeError:
            pass

    def _update_target(self):
        if not self._is_target_valid():
            return

        if self.update_method_name and hasattr(self.target, self.update_method_name):
            method = getattr(self.target, self.update_method_name)
            method()
        elif hasattr(self.target, "update_text"):
            self.target.update_text()
        elif hasattr(self.target, "update_image"):
            self.target.update_image()
        elif hasattr(self.target, "update_position"):
            self.target.update_position()


class MoveWindowCommand(QUndoCommand):
    def __init__(self, target, old_pos, new_pos):
        super().__init__()
        self.target = target
        self.old_pos = old_pos
        self.new_pos = new_pos
        # targetのuuidがある場合は参照用に保持しておくとログ等で便利
        uuid_str = target.uuid if hasattr(target, "uuid") else "Window"
        self.setText(f"Move {uuid_str}")

    def _is_target_valid(self):
        return self.target and shiboken6.isValid(self.target)

    def redo(self):
        if not self._is_target_valid():
            return

        try:
            self.target.move(self.new_pos)
            if hasattr(self.target, "config"):
                self.target.config.position = {"x": self.new_pos.x(), "y": self.new_pos.y()}
            if hasattr(self.target, "sig_window_moved"):
                self.target.sig_window_moved.emit(self.target)
        except RuntimeError:
            pass

    def undo(self):
        if not self._is_target_valid():
            return

        try:
            self.target.move(self.old_pos)
            if hasattr(self.target, "config"):
                self.target.config.position = {"x": self.old_pos.x(), "y": self.old_pos.y()}
            if hasattr(self.target, "sig_window_moved"):
                self.target.sig_window_moved.emit(self.target)
        except RuntimeError:
            pass
