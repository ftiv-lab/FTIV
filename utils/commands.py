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

    def _move_target_tree_aware(self, target_pos):
        """親子ツリーを考慮して移動する。move_tree_by_delta があれば優先して使う。"""
        if not self._is_target_valid():
            return
        try:
            delta = None
            try:
                current_pos = self.target.pos()
                candidate = target_pos - current_pos
                if hasattr(candidate, "isNull"):
                    delta = candidate
            except Exception:
                delta = None

            if delta is not None and delta.isNull():
                return

            if delta is not None and hasattr(self.target, "move_tree_by_delta"):
                self.target.move_tree_by_delta(delta)
            else:
                self.target.move(target_pos)

            if hasattr(self.target, "config"):
                self.target.config.position = {"x": target_pos.x(), "y": target_pos.y()}
            if hasattr(self.target, "sig_window_moved"):
                self.target.sig_window_moved.emit(self.target)
        except (RuntimeError, TypeError):
            pass

    def redo(self):
        if not self._is_target_valid():
            return

        self._move_target_tree_aware(self.new_pos)

    def undo(self):
        if not self._is_target_valid():
            return

        self._move_target_tree_aware(self.old_pos)


class AttachLayerCommand(QUndoCommand):
    """child を parent の子レイヤーにアタッチする操作の Undo コマンド。"""

    def __init__(self, parent_win, child_win, window_manager):
        super().__init__("レイヤーをアタッチ")
        self._parent = parent_win
        self._child = child_win
        self._wm = window_manager
        self._saved_offset = child_win.config.layer_offset
        self._saved_order = child_win.config.layer_order

    def _are_valid(self) -> bool:
        return self._parent and shiboken6.isValid(self._parent) and self._child and shiboken6.isValid(self._child)

    def redo(self):
        if not self._are_valid():
            return
        try:
            if self._child not in self._parent.child_windows:
                self._child.config.layer_offset = self._saved_offset
                self._child.config.layer_order = self._saved_order
                self._parent.add_child_window(self._child)
            self._wm.raise_group_stack(self._parent)
            self._wm.sig_layer_structure_changed.emit()
        except (RuntimeError, ValueError):
            pass

    def undo(self):
        if not self._are_valid():
            return
        try:
            self._parent.remove_child_window(self._child)
            self._child.config.layer_offset = None
            self._child.config.layer_order = None
            self._wm.sig_layer_structure_changed.emit()
        except RuntimeError:
            pass


class DetachLayerCommand(QUndoCommand):
    """child を親レイヤーからデタッチする操作の Undo コマンド。"""

    def __init__(self, parent_win, child_win, window_manager, saved_offset, saved_order):
        super().__init__("レイヤーをデタッチ")
        self._parent = parent_win
        self._child = child_win
        self._wm = window_manager
        self._saved_offset = saved_offset
        self._saved_order = saved_order

    def _are_valid(self) -> bool:
        child_ok = self._child and shiboken6.isValid(self._child)
        parent_ok = self._parent is None or (self._parent and shiboken6.isValid(self._parent))
        return child_ok and parent_ok

    def redo(self):
        if not self._are_valid():
            return
        try:
            if self._parent and self._child in self._parent.child_windows:
                self._parent.remove_child_window(self._child)
            self._child.config.layer_offset = None
            self._child.config.layer_order = None
            self._wm.sig_layer_structure_changed.emit()
        except RuntimeError:
            pass

    def undo(self):
        if not self._are_valid():
            return
        try:
            if self._parent:
                self._child.config.layer_offset = self._saved_offset
                self._child.config.layer_order = self._saved_order
                self._parent.add_child_window(self._child)
                self._wm.raise_group_stack(self._parent)
            self._wm.sig_layer_structure_changed.emit()
        except (RuntimeError, ValueError):
            pass


class ReorderLayerCommand(QUndoCommand):
    """同一親配下のレイヤー順変更を Undo/Redo 可能にするコマンド。"""

    def __init__(self, parent_win, before_order_uuids, after_order_uuids, window_manager):
        super().__init__("レイヤー順序を変更")
        self._parent = parent_win
        self._before = list(before_order_uuids or [])
        self._after = list(after_order_uuids or [])
        self._wm = window_manager

    def _is_parent_valid(self) -> bool:
        if self._parent is None:
            return False
        try:
            return shiboken6.isValid(self._parent)
        except Exception:
            # テストダブルなど非Qtオブジェクトも許容
            return True

    def _apply(self, order_uuids) -> None:
        if not self._is_parent_valid():
            return

        try:
            siblings = list(getattr(self._parent, "child_windows", []))
        except Exception:
            return

        if not siblings:
            return

        by_uuid = {getattr(w, "uuid", None): w for w in siblings}
        if None in by_uuid:
            return

        try:
            ordered = [by_uuid[uid] for uid in order_uuids]
        except Exception:
            return

        # UUID集合が一致しない場合は破壊的変更を避ける
        if len(ordered) != len(siblings) or set(order_uuids) != set(by_uuid.keys()):
            return

        for idx, sibling in enumerate(ordered):
            try:
                sibling.config.layer_order = idx
            except Exception:
                pass

        try:
            self._parent.child_windows[:] = ordered
        except Exception:
            return

        try:
            self._wm.raise_group_stack(self._parent)
        except Exception:
            pass
        try:
            self._wm.sig_layer_structure_changed.emit()
        except Exception:
            pass

    def redo(self):
        self._apply(self._after)

    def undo(self):
        self._apply(self._before)
