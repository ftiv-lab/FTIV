from types import SimpleNamespace

from ui.tabs.layer_tab import LayerTab


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
        self.sig_status_message.connect(lambda msg: self.status_messages.append(str(msg)))

    def find_window_by_uuid(self, uuid: str):
        for w in self.text_windows:
            if w.uuid == uuid:
                return w
        return None

    def set_selected_window(self, window) -> None:
        self.last_selected_window = window
        self.sig_selection_changed.emit(window)

    def attach_layer(self, parent, child) -> None:
        raise RuntimeError("attach failed")

    def detach_layer(self, child) -> None:
        _ = child

    def raise_group_stack(self, parent) -> None:
        _ = parent


class _DummyMainWindow:
    def __init__(self, wm: _DummyWindowManager) -> None:
        self.window_manager = wm


def test_drop_relation_returns_false_for_same_source_and_target():
    w1 = _DummyWindow("w1")
    wm = _DummyWindowManager([w1])
    tab = LayerTab(_DummyMainWindow(wm))
    tab.rebuild()

    assert tab._apply_tree_drop_relation("w1", "w1") is False


def test_drop_relation_attach_error_is_reported_and_false():
    source = _DummyWindow("source")
    target = _DummyWindow("target")
    wm = _DummyWindowManager([source, target])
    tab = LayerTab(_DummyMainWindow(wm))
    tab.rebuild()

    ok = tab._apply_tree_drop_relation("source", "target")

    assert ok is False
    assert any("attach failed" in msg for msg in wm.status_messages)
