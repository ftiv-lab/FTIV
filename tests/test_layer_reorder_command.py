from types import SimpleNamespace

from utils.commands import ReorderLayerCommand


class _DummySignal:
    def __init__(self) -> None:
        self.emit_count = 0

    def emit(self) -> None:
        self.emit_count += 1


class _DummyWindow:
    def __init__(self, uuid: str, order: int) -> None:
        self.uuid = uuid
        self.config = SimpleNamespace(layer_order=order)
        self.child_windows = []


class _DummyWindowManager:
    def __init__(self) -> None:
        self.raise_calls: list[str] = []
        self.sig_layer_structure_changed = _DummySignal()

    def raise_group_stack(self, parent) -> None:
        self.raise_calls.append(parent.uuid)


def test_reorder_layer_command_redo_and_undo_restore_order():
    parent = _DummyWindow("parent", 0)
    c1 = _DummyWindow("c1", 0)
    c2 = _DummyWindow("c2", 1)
    parent.child_windows = [c1, c2]

    wm = _DummyWindowManager()
    cmd = ReorderLayerCommand(parent, ["c1", "c2"], ["c2", "c1"], wm)

    cmd.redo()
    assert [w.uuid for w in parent.child_windows] == ["c2", "c1"]
    assert c2.config.layer_order == 0
    assert c1.config.layer_order == 1

    cmd.undo()
    assert [w.uuid for w in parent.child_windows] == ["c1", "c2"]
    assert c1.config.layer_order == 0
    assert c2.config.layer_order == 1


def test_reorder_layer_command_noop_when_uuid_set_mismatch():
    parent = _DummyWindow("parent", 0)
    c1 = _DummyWindow("c1", 0)
    c2 = _DummyWindow("c2", 1)
    parent.child_windows = [c1, c2]

    wm = _DummyWindowManager()
    cmd = ReorderLayerCommand(parent, ["c1", "missing"], ["missing", "c1"], wm)

    cmd.redo()
    assert [w.uuid for w in parent.child_windows] == ["c1", "c2"]
    assert wm.raise_calls == []
    assert wm.sig_layer_structure_changed.emit_count == 0
