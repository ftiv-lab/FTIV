from types import SimpleNamespace

from PySide6.QtCore import QPoint

from ui.tabs.layer_tab import LayerTab
from utils.translator import tr


class _DummySignal:
    def __init__(self) -> None:
        self._slots = []

    def connect(self, slot) -> None:
        self._slots.append(slot)

    def emit(self, *args, **kwargs) -> None:
        for slot in list(self._slots):
            slot(*args, **kwargs)


class _DummyWindow:
    def __init__(self, uuid: str, parent_window_uuid: str | None = None, layer_order: int | None = None) -> None:
        self.uuid = uuid
        self.parent_window_uuid = parent_window_uuid
        self.child_windows = []
        self.config = SimpleNamespace(layer_order=layer_order)
        self.is_hidden = False
        self.is_locked = False
        self.is_frontmost = False
        self.context_menu_positions = []

    def mapFromGlobal(self, pos):
        return pos

    def show_context_menu(self, pos) -> None:
        self.context_menu_positions.append(pos)


class _DummyWindowManager:
    def __init__(self, windows: list[_DummyWindow]) -> None:
        self.text_windows = list(windows)
        self.image_windows = []
        self.last_selected_window = None

        self.sig_layer_structure_changed = _DummySignal()
        self.sig_selection_changed = _DummySignal()
        self.sig_status_message = _DummySignal()

        self.status_messages: list[str] = []
        self.attach_calls: list[tuple[str, str]] = []
        self.raise_calls: list[str] = []
        self.sig_status_message.connect(lambda msg: self.status_messages.append(str(msg)))

    def find_window_by_uuid(self, uuid: str):
        for w in self.text_windows + self.image_windows:
            if w.uuid == uuid:
                return w
        return None

    def set_selected_window(self, window) -> None:
        self.last_selected_window = window
        self.sig_selection_changed.emit(window)

    def attach_layer(self, parent, child) -> None:
        if child.parent_window_uuid:
            old_parent = self.find_window_by_uuid(child.parent_window_uuid)
            if old_parent and child in old_parent.child_windows:
                old_parent.child_windows.remove(child)
        child.parent_window_uuid = parent.uuid
        if child not in parent.child_windows:
            parent.child_windows.append(child)
        for idx, s in enumerate(parent.child_windows):
            s.config.layer_order = idx
        self.attach_calls.append((parent.uuid, child.uuid))
        self.sig_layer_structure_changed.emit()

    def detach_layer(self, child) -> None:
        parent_uuid = child.parent_window_uuid
        parent = self.find_window_by_uuid(parent_uuid) if parent_uuid else None
        if parent and child in parent.child_windows:
            parent.child_windows.remove(child)
        child.parent_window_uuid = None
        child.config.layer_order = None
        self.sig_layer_structure_changed.emit()

    def raise_group_stack(self, parent) -> None:
        self.raise_calls.append(parent.uuid)


class _DummyMainWindow:
    def __init__(self, wm: _DummyWindowManager) -> None:
        self.window_manager = wm
        self.main_context_calls: list = []
        self.undo_commands: list = []

    def show_context_menu(self, pos) -> None:
        self.main_context_calls.append(pos)

    def mapFromGlobal(self, pos):
        return pos

    def add_undo_command(self, command) -> None:
        self.undo_commands.append(command)
        command.redo()


def _build_layer_tab():
    parent = _DummyWindow("parent")
    child = _DummyWindow("child")
    alt_parent = _DummyWindow("alt-parent")
    wm = _DummyWindowManager([parent, child, alt_parent])
    mw = _DummyMainWindow(wm)
    tab = LayerTab(mw)
    tab.rebuild()
    return tab, wm, parent, child, alt_parent


def test_parent_slot_set_and_clear():
    tab, wm, parent, _child, _alt_parent = _build_layer_tab()
    wm.set_selected_window(parent)
    tab._on_set_parent()

    assert tab._explicit_parent_uuid == "parent"
    assert tab.lbl_parent_slot_value.text() != tr("layer_parent_slot_empty")

    tab._on_clear_parent()
    assert tab._explicit_parent_uuid is None
    assert tab.lbl_parent_slot_value.text() == tr("layer_parent_slot_empty")


def test_attach_prefers_explicit_parent_slot():
    tab, wm, parent, child, alt_parent = _build_layer_tab()
    tab._explicit_parent_uuid = parent.uuid
    wm.last_selected_window = alt_parent
    tab._selected_uuid = lambda: child.uuid

    tab._on_attach()

    assert wm.attach_calls[-1] == (parent.uuid, child.uuid)


def test_attach_requires_explicit_parent_slot():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    wm.last_selected_window = parent
    tab._explicit_parent_uuid = None
    tab._selected_uuid = lambda: child.uuid

    tab._on_attach()

    assert wm.attach_calls == []
    assert any(tr("layer_msg_select_parent_first") in msg for msg in wm.status_messages)


def test_drop_relation_attach_as_child():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    ok = tab._apply_tree_drop_relation(child.uuid, parent.uuid)
    assert ok is True
    assert wm.attach_calls[-1] == (parent.uuid, child.uuid)
    assert child.parent_window_uuid == parent.uuid


def test_drop_relation_reorder_within_parent():
    tab, wm, parent, _child, _alt_parent = _build_layer_tab()
    c1 = _DummyWindow("c1", parent_window_uuid=parent.uuid, layer_order=0)
    c2 = _DummyWindow("c2", parent_window_uuid=parent.uuid, layer_order=1)
    parent.child_windows = [c1, c2]
    wm.text_windows.extend([c1, c2])
    tab.rebuild()

    ok = tab._apply_tree_drop_relation("c2", "c1")

    assert ok is True
    assert parent.child_windows[0].uuid == "c2"
    assert parent.child_windows[1].uuid == "c1"
    assert parent.child_windows[0].config.layer_order == 0
    assert parent.child_windows[1].config.layer_order == 1
    assert wm.raise_calls[-1] == parent.uuid


def test_move_up_moves_selected_child_toward_front():
    tab, wm, parent, _child, _alt_parent = _build_layer_tab()
    c1 = _DummyWindow("c1", parent_window_uuid=parent.uuid, layer_order=0)
    c2 = _DummyWindow("c2", parent_window_uuid=parent.uuid, layer_order=1)
    parent.child_windows = [c1, c2]
    wm.text_windows.extend([c1, c2])
    tab.rebuild()
    tab._selected_uuid = lambda: "c1"

    tab._on_move_up()

    assert parent.child_windows[0].uuid == "c2"
    assert parent.child_windows[1].uuid == "c1"
    assert parent.child_windows[0].config.layer_order == 0
    assert parent.child_windows[1].config.layer_order == 1


def test_move_up_pushes_reorder_command_and_undo_restores_order():
    tab, wm, parent, _child, _alt_parent = _build_layer_tab()
    c1 = _DummyWindow("c1", parent_window_uuid=parent.uuid, layer_order=0)
    c2 = _DummyWindow("c2", parent_window_uuid=parent.uuid, layer_order=1)
    parent.child_windows = [c1, c2]
    wm.text_windows.extend([c1, c2])
    tab.rebuild()
    tab._selected_uuid = lambda: "c1"

    tab._on_move_up()

    assert parent.child_windows[0].uuid == "c2"
    assert parent.child_windows[1].uuid == "c1"
    assert len(tab.mw.undo_commands) == 1

    tab.mw.undo_commands[-1].undo()
    assert parent.child_windows[0].uuid == "c1"
    assert parent.child_windows[1].uuid == "c2"


def test_detach_keeps_detached_window_selected():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    wm.attach_layer(parent, child)
    tab.rebuild()
    tab._selected_uuid = lambda: child.uuid

    tab._on_detach()

    assert child.parent_window_uuid is None
    assert wm.last_selected_window is child


def test_tree_context_menu_routes_to_selected_window_menu():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    item = tab._uuid_to_item[child.uuid]
    tab.tree.itemAt = lambda _pos: item

    tab._on_tree_context_menu(QPoint(1, 1))

    assert wm.last_selected_window is child
    assert child.context_menu_positions


def test_tree_context_menu_falls_back_to_main_menu_when_no_item():
    tab, _wm, _parent, _child, _alt_parent = _build_layer_tab()
    tab.tree.itemAt = lambda _pos: None
    tab.tree.selectedItems = lambda: []

    tab._on_tree_context_menu(QPoint(5, 6))

    assert tab.mw.main_context_calls


def test_button_states_follow_parent_slot_and_selection_state_machine():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()

    # 初期状態: 選択なし
    assert tab.btn_attach.isEnabled() is False
    assert tab.btn_detach.isEnabled() is False
    assert tab.btn_up.isEnabled() is False
    assert tab.btn_down.isEnabled() is False

    # 子を選択しても、親候補がない限り attach は無効
    child_item = tab._uuid_to_item[child.uuid]
    tab.tree.setCurrentItem(child_item)
    tab._on_tree_selection_changed()
    assert wm.last_selected_window is child
    assert tab.btn_attach.isEnabled() is False
    assert tab.btn_detach.isEnabled() is False
    assert tab.btn_up.isEnabled() is True
    assert tab.btn_down.isEnabled() is True

    # 親候補を設定すると attach 有効
    tab._explicit_parent_uuid = parent.uuid
    tab._refresh_parent_slot_ui()
    assert tab.btn_attach.isEnabled() is True

    # 親自身を選んだときは self-attach 防止で無効
    parent_item = tab._uuid_to_item[parent.uuid]
    tab.tree.setCurrentItem(parent_item)
    tab._on_tree_selection_changed()
    assert tab.btn_attach.isEnabled() is False


def test_detach_button_enabled_only_when_selected_item_has_parent():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    wm.attach_layer(parent, child)
    tab.rebuild()

    child_item = tab._uuid_to_item[child.uuid]
    tab.tree.setCurrentItem(child_item)
    tab._on_tree_selection_changed()
    assert tab.btn_detach.isEnabled() is True

    parent_item = tab._uuid_to_item[parent.uuid]
    tab.tree.setCurrentItem(parent_item)
    tab._on_tree_selection_changed()
    assert tab.btn_detach.isEnabled() is False


def test_sonar_hover_previews_subtree_and_clears():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    wm.attach_layer(parent, child)
    tab.rebuild()

    parent_item = tab._uuid_to_item[parent.uuid]
    tab._on_tree_item_entered(parent_item, 0)

    assert bool(getattr(parent, "_layer_hover_preview", False)) is True
    assert bool(getattr(child, "_layer_hover_preview", False)) is True

    tab._clear_hover_preview()

    assert bool(getattr(parent, "_layer_hover_preview", False)) is False
    assert bool(getattr(child, "_layer_hover_preview", False)) is False


def test_sonar_selection_previews_subtree_once_for_same_uuid():
    tab, wm, parent, child, _alt_parent = _build_layer_tab()
    wm.attach_layer(parent, child)
    tab.rebuild()

    calls: list[tuple[str, str]] = []
    original = tab._preview_subtree

    def _spy_preview(root_uuid: str, *, source: str = "hover"):
        calls.append((root_uuid, source))
        return original(root_uuid, source=source)

    tab._preview_subtree = _spy_preview  # type: ignore[method-assign]

    parent_item = tab._uuid_to_item[parent.uuid]
    tab.tree.setCurrentItem(parent_item)
    tab._on_tree_selection_changed()
    tab._on_tree_selection_changed()

    assert calls.count((parent.uuid, "selection")) == 1
    assert bool(getattr(parent, "_layer_hover_preview", False)) is True
    assert bool(getattr(child, "_layer_hover_preview", False)) is True


def test_sonar_timer_default_duration_is_extended(monkeypatch):
    monkeypatch.setenv("FTIV_TEST_MODE", "0")
    tab, _wm, parent, _child, _alt_parent = _build_layer_tab()
    parent_item = tab._uuid_to_item[parent.uuid]

    tab._on_tree_item_entered(parent_item, 0)

    assert tab._sonar_clear_timer.interval() == 1200


def test_sonar_timer_uses_test_mode_duration(monkeypatch):
    monkeypatch.setenv("FTIV_TEST_MODE", "1")
    tab, _wm, parent, _child, _alt_parent = _build_layer_tab()
    parent_item = tab._uuid_to_item[parent.uuid]

    tab._on_tree_item_entered(parent_item, 0)

    assert tab._sonar_clear_timer.interval() == 0
