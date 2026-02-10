from types import SimpleNamespace

from ui.controllers.info_actions import InfoActions


class _DummyTextWindow:
    def __init__(self, uuid: str) -> None:
        self.uuid = uuid
        self.calls: list[tuple[str, object]] = []

    def set_due_at(self, due_iso: str) -> None:
        self.calls.append(("set_due_at", due_iso))

    def clear_due_at(self) -> None:
        self.calls.append(("clear_due_at", None))

    def set_archived(self, value: bool) -> None:
        self.calls.append(("set_archived", bool(value)))

    def bulk_set_task_done(self, indices, value: bool) -> None:
        self.calls.append(("bulk_set_task_done", (list(indices), bool(value))))


def _make_main_window(*text_windows):
    info_tab = SimpleNamespace(refresh_data=lambda: None)
    wm = SimpleNamespace(text_windows=list(text_windows), image_windows=[])
    return SimpleNamespace(window_manager=wm, info_tab=info_tab)


def test_set_due_at_valid():
    w = _DummyTextWindow("w1")
    mw = _make_main_window(w)
    actions = InfoActions(mw)

    actions.set_due_at("w1", "2026-03-02")
    assert ("set_due_at", "2026-03-02T00:00:00") in w.calls


def test_set_due_at_invalid_is_noop():
    w = _DummyTextWindow("w1")
    refreshed = {"count": 0}

    def _refresh():
        refreshed["count"] += 1

    mw = SimpleNamespace(
        window_manager=SimpleNamespace(text_windows=[w], image_windows=[]),
        info_tab=SimpleNamespace(refresh_data=_refresh),
    )
    actions = InfoActions(mw)

    actions.set_due_at("w1", "2026/03/02")
    assert w.calls == []
    assert refreshed["count"] == 0


def test_clear_due_at():
    w = _DummyTextWindow("w1")
    mw = _make_main_window(w)
    actions = InfoActions(mw)

    actions.clear_due_at("w1")
    assert ("clear_due_at", None) in w.calls


def test_bulk_archive_updates_multiple_windows():
    w1 = _DummyTextWindow("w1")
    w2 = _DummyTextWindow("w2")
    mw = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_archive(["w1", "w2"], True)
    assert ("set_archived", True) in w1.calls
    assert ("set_archived", True) in w2.calls


def test_bulk_set_task_done_groups_by_window():
    w1 = _DummyTextWindow("w1")
    w2 = _DummyTextWindow("w2")
    mw = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_set_task_done(["w1:0", "w1:2", "w2:1"], True)

    assert ("bulk_set_task_done", ([0, 2], True)) in w1.calls
    assert ("bulk_set_task_done", ([1], True)) in w2.calls
