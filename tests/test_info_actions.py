from types import SimpleNamespace
from unittest.mock import MagicMock

from ui.controllers.info_actions import InfoActions


class _DummyTextWindow:
    def __init__(self, uuid: str) -> None:
        self.uuid = uuid
        self.is_archived = False
        self.is_starred = False
        self.tags = []
        self.title = "Title"
        self.calls: list[tuple[str, object]] = []

    def set_due_at(self, due_iso: str) -> None:
        self.calls.append(("set_due_at", due_iso))

    def clear_due_at(self) -> None:
        self.calls.append(("clear_due_at", None))

    def set_archived(self, value: bool) -> None:
        self.is_archived = bool(value)
        self.calls.append(("set_archived", bool(value)))

    def set_starred(self, value: bool) -> None:
        self.is_starred = bool(value)
        self.calls.append(("set_starred", bool(value)))

    def set_tags(self, tags: list[str]) -> None:
        self.tags = list(tags)
        self.calls.append(("set_tags", list(tags)))

    def bulk_set_task_done(self, indices, value: bool) -> None:
        self.calls.append(("bulk_set_task_done", (list(indices), bool(value))))


class _DummySettingsManager:
    def __init__(self) -> None:
        self.save_count = 0

    def save_app_settings(self) -> None:
        self.save_count += 1


def _make_main_window(*text_windows):
    refresh_count = {"count": 0}

    def _refresh() -> None:
        refresh_count["count"] += 1

    info_tab = SimpleNamespace(refresh_data=_refresh)
    wm = SimpleNamespace(text_windows=list(text_windows), image_windows=[])
    settings_manager = _DummySettingsManager()
    app_settings = SimpleNamespace(info_operation_logs=[])
    undo_stack = MagicMock()
    mw = SimpleNamespace(
        window_manager=wm,
        info_tab=info_tab,
        app_settings=app_settings,
        settings_manager=settings_manager,
        undo_stack=undo_stack,
    )
    return mw, refresh_count


def test_set_due_at_valid():
    w = _DummyTextWindow("w1")
    mw, _ = _make_main_window(w)
    actions = InfoActions(mw)

    actions.set_due_at("w1", "2026-03-02")
    assert ("set_due_at", "2026-03-02T00:00:00") in w.calls


def test_set_due_at_invalid_is_noop():
    w = _DummyTextWindow("w1")
    mw, refreshed = _make_main_window(w)
    actions = InfoActions(mw)

    actions.set_due_at("w1", "2026/03/02")
    assert w.calls == []
    assert refreshed["count"] == 0


def test_clear_due_at():
    w = _DummyTextWindow("w1")
    mw, _ = _make_main_window(w)
    actions = InfoActions(mw)

    actions.clear_due_at("w1")
    assert ("clear_due_at", None) in w.calls


def test_bulk_archive_updates_multiple_windows_dedupes_and_logs():
    w1 = _DummyTextWindow("w1")
    w2 = _DummyTextWindow("w2")
    mw, refreshed = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_archive(["w1", "w1", "w2"], True)

    assert w1.is_archived is True
    assert w2.is_archived is True
    assert refreshed["count"] == 1
    assert mw.undo_stack.beginMacro.call_count == 1
    assert mw.undo_stack.endMacro.call_count == 1
    assert len(mw.app_settings.info_operation_logs) == 1
    assert mw.app_settings.info_operation_logs[0]["action"] == "bulk_archive"
    assert mw.app_settings.info_operation_logs[0]["target_count"] == 2


def test_bulk_archive_false_restores_and_logs():
    w1 = _DummyTextWindow("w1")
    w1.is_archived = True
    mw, _ = _make_main_window(w1)
    actions = InfoActions(mw)

    actions.bulk_archive(["w1"], False)

    assert w1.is_archived is False
    assert mw.app_settings.info_operation_logs[-1]["action"] == "bulk_restore"


def test_bulk_set_star_updates_and_logs():
    w1 = _DummyTextWindow("w1")
    w2 = _DummyTextWindow("w2")
    mw, refreshed = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_set_star(["w1", "w2"], True)

    assert w1.is_starred is True
    assert w2.is_starred is True
    assert refreshed["count"] == 1
    assert mw.app_settings.info_operation_logs[-1]["action"] == "bulk_star"
    assert mw.app_settings.info_operation_logs[-1]["target_count"] == 2


def test_bulk_merge_tags_add_remove_and_remove_wins():
    w1 = _DummyTextWindow("w1")
    w1.tags = ["A", "B"]
    w2 = _DummyTextWindow("w2")
    w2.tags = ["c"]
    mw, refreshed = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_merge_tags(["w1", "w2"], add_tags=["b", "D", "a"], remove_tags=["a"])

    assert w1.tags == ["B", "D"]
    assert w2.tags == ["c", "b", "D"]
    assert refreshed["count"] == 1
    assert mw.app_settings.info_operation_logs[-1]["action"] == "bulk_tags_merge"


def test_bulk_merge_tags_empty_input_noop():
    w1 = _DummyTextWindow("w1")
    mw, refreshed = _make_main_window(w1)
    actions = InfoActions(mw)

    actions.bulk_merge_tags(["w1"], add_tags=[], remove_tags=[])

    assert refreshed["count"] == 0
    assert mw.app_settings.info_operation_logs == []


def test_bulk_set_task_done_groups_by_window_and_logs():
    w1 = _DummyTextWindow("w1")
    w2 = _DummyTextWindow("w2")
    mw, refreshed = _make_main_window(w1, w2)
    actions = InfoActions(mw)

    actions.bulk_set_task_done(["w1:0", "w1:2", "w1:2", "w2:1"], True)

    assert ("bulk_set_task_done", ([0, 2], True)) in w1.calls
    assert ("bulk_set_task_done", ([1], True)) in w2.calls
    assert refreshed["count"] == 1
    assert mw.app_settings.info_operation_logs[-1]["action"] == "bulk_complete"
    assert mw.app_settings.info_operation_logs[-1]["target_count"] == 3


def test_get_and_clear_operation_logs():
    w1 = _DummyTextWindow("w1")
    mw, refreshed = _make_main_window(w1)
    actions = InfoActions(mw)

    actions._append_operation_log("bulk_archive", 1, "archive")
    actions._append_operation_log("bulk_restore", 1, "restore")

    assert len(actions.get_operation_logs()) == 2
    assert len(actions.get_operation_logs(limit=1)) == 1

    actions.clear_operation_logs()
    assert actions.get_operation_logs() == []
    assert refreshed["count"] == 1


def test_operation_logs_trim_to_200():
    w1 = _DummyTextWindow("w1")
    mw, _ = _make_main_window(w1)
    actions = InfoActions(mw)

    for i in range(205):
        actions._append_operation_log(f"bulk_{i}", 1, "x")

    assert len(mw.app_settings.info_operation_logs) == 200
    assert mw.app_settings.info_operation_logs[0]["action"] == "bulk_5"
    assert mw.app_settings.info_operation_logs[-1]["action"] == "bulk_204"
