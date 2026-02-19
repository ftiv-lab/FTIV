from types import SimpleNamespace

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
