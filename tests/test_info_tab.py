from types import SimpleNamespace

from PySide6.QtCore import Qt

from ui.tabs.info_tab import InfoTab
from utils.translator import tr


class _DummyTaskWindow:
    def __init__(
        self,
        uuid: str = "tw-1",
        text: str = "task one",
        states=None,
        due_at: str = "",
        is_archived: bool = False,
    ) -> None:
        self.uuid = uuid
        self.text = text
        self.content_mode = "task"
        self.title = "Tasks"
        self.tags = []
        self.is_starred = False
        self.created_at = ""
        self.updated_at = ""
        self.due_at = due_at
        self.is_archived = is_archived
        lines = text.split("\n")
        if states is None:
            states = [False] * len(lines)
        self._states = list(states)

    def iter_task_items(self):
        lines = self.text.split("\n")
        return [SimpleNamespace(line_index=i, text=lines[i], done=bool(self._states[i])) for i in range(len(lines))]

    def toggle_task_line_state(self, index: int) -> None:
        if 0 <= index < len(self._states):
            self._states[index] = not self._states[index]

    def set_task_line_state(self, index: int, value: bool) -> None:
        if 0 <= index < len(self._states):
            self._states[index] = bool(value)

    def bulk_set_task_done(self, indices, value: bool) -> None:
        for idx in list(indices):
            self.set_task_line_state(int(idx), bool(value))

    def set_archived(self, value: bool) -> None:
        self.is_archived = bool(value)


class _DummyNoteWindow:
    def __init__(self, uuid: str = "nw-1", is_archived: bool = False) -> None:
        self.uuid = uuid
        self.text = "note body"
        self.content_mode = "note"
        self.title = "Memo"
        self.tags = []
        self.is_starred = False
        self.created_at = ""
        self.updated_at = ""
        self.due_at = ""
        self.is_archived = is_archived

    def set_starred(self, value: bool) -> None:
        self.is_starred = bool(value)

    def set_archived(self, value: bool) -> None:
        self.is_archived = bool(value)


class _DummyInfoActions:
    def __init__(self, tab: InfoTab, windows: list[object]) -> None:
        self.tab = tab
        self.windows = windows
        self.last_bulk_archive: list[str] = []
        self.last_bulk_done: list[str] = []

    def _find(self, window_uuid: str):
        for w in self.windows:
            if str(getattr(w, "uuid", "")) == str(window_uuid):
                return w
        return None

    def toggle_task(self, item_key: str) -> None:
        window_uuid, idx = item_key.rsplit(":", 1)
        w = self._find(window_uuid)
        if w is not None and hasattr(w, "toggle_task_line_state"):
            w.toggle_task_line_state(int(idx))
        # Rebuild list immediately (regression path for deleted QListWidgetItem safety).
        self.tab.refresh_data(immediate=True)

    def set_star(self, window_uuid: str, value: bool) -> None:
        w = self._find(window_uuid)
        if w is not None and hasattr(w, "set_starred"):
            w.set_starred(value)
        self.tab.refresh_data(immediate=True)

    def bulk_archive(self, window_uuids: list[str], value: bool) -> None:
        self.last_bulk_archive = list(window_uuids)
        for window_uuid in window_uuids:
            w = self._find(window_uuid)
            if w is not None and hasattr(w, "set_archived"):
                w.set_archived(value)
        self.tab.refresh_data(immediate=True)

    def bulk_set_task_done(self, item_keys: list[str], value: bool) -> None:
        self.last_bulk_done = list(item_keys)
        for key in item_keys:
            if ":" not in key:
                continue
            window_uuid, idx = key.rsplit(":", 1)
            w = self._find(window_uuid)
            if w is not None and hasattr(w, "set_task_line_state"):
                w.set_task_line_state(int(idx), value)
        self.tab.refresh_data(immediate=True)

    def focus_window(self, window_uuid: str) -> None:
        _ = window_uuid


def _make_main_window(task_windows=None, note_windows=None):
    if task_windows is None:
        task_windows = [_DummyTaskWindow()]
    if note_windows is None:
        note_windows = [_DummyNoteWindow()]
    text_windows = [*task_windows, *note_windows]
    wm = SimpleNamespace(text_windows=text_windows)
    app_settings = SimpleNamespace(info_view_presets=[], info_last_view_preset_id="builtin:all")
    settings_manager = SimpleNamespace(save_app_settings=lambda: None)
    mw = SimpleNamespace(window_manager=wm, app_settings=app_settings, settings_manager=settings_manager)
    return mw, text_windows


def _find_note_item(tab: InfoTab, window_uuid: str):
    for i in range(tab.notes_list.count()):
        candidate = tab.notes_list.item(i)
        if candidate is None:
            continue
        if str(candidate.data(Qt.ItemDataRole.UserRole) or "") == window_uuid:
            return candidate
    return None


def _count_task_items(tab: InfoTab) -> int:
    count = 0
    for i in range(tab.tasks_list.count()):
        item = tab.tasks_list.item(i)
        if item is None:
            continue
        if ":" in str(item.data(Qt.ItemDataRole.UserRole) or ""):
            count += 1
    return count


def test_task_item_changed_safe_when_action_refreshes(qapp):
    _ = qapp
    mw, text_windows = _make_main_window()
    tab = InfoTab(mw)
    mw.main_controller = SimpleNamespace(info_actions=_DummyInfoActions(tab, text_windows))

    item = tab.tasks_list.item(0)
    assert item is not None

    # Must not raise RuntimeError even if action refreshes list immediately.
    item.setCheckState(Qt.CheckState.Checked)
    task_window = text_windows[0]
    assert isinstance(task_window, _DummyTaskWindow)
    assert task_window._states[0] is True


def test_note_item_changed_safe_when_action_refreshes(qapp):
    _ = qapp
    mw, text_windows = _make_main_window()
    tab = InfoTab(mw)
    mw.main_controller = SimpleNamespace(info_actions=_DummyInfoActions(tab, text_windows))

    note_window = next(w for w in text_windows if isinstance(w, _DummyNoteWindow))
    item = _find_note_item(tab, note_window.uuid)
    assert item is not None

    # Must not raise RuntimeError even if action refreshes list immediately.
    item.setCheckState(Qt.CheckState.Checked)
    assert note_window.is_starred is True


def test_smart_view_overdue_filters_tasks(qapp):
    _ = qapp
    overdue = _DummyTaskWindow(uuid="t-overdue", text="over", due_at="2001-01-01T00:00:00")
    future = _DummyTaskWindow(uuid="t-future", text="future", due_at="2999-01-01T00:00:00")
    mw, _ = _make_main_window(task_windows=[overdue, future], note_windows=[])
    tab = InfoTab(mw)

    tab._apply_preset_by_id("builtin:overdue")
    tab.refresh_data(immediate=True)

    assert _count_task_items(tab) == 1
    first = tab.tasks_list.item(0)
    assert first is not None
    assert str(first.data(Qt.ItemDataRole.UserRole)).startswith("t-overdue:")


def test_bulk_archive_selected_updates_windows(qapp):
    _ = qapp
    task_window = _DummyTaskWindow(uuid="t-1")
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, text_windows = _make_main_window(task_windows=[task_window], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    note_item.setSelected(True)

    tab._archive_selected()
    assert note_window.is_archived is True
    assert "n-1" in actions.last_bulk_archive


def test_bulk_complete_selected_updates_task_states(qapp):
    _ = qapp
    task_window = _DummyTaskWindow(uuid="t-1", text="a\nb", states=[False, False])
    mw, text_windows = _make_main_window(task_windows=[task_window], note_windows=[])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    for i in range(tab.tasks_list.count()):
        item = tab.tasks_list.item(i)
        if item is None:
            continue
        if ":" in str(item.data(Qt.ItemDataRole.UserRole) or ""):
            item.setSelected(True)

    tab._apply_bulk_task_done(True)
    assert task_window._states == [True, True]
    assert len(actions.last_bulk_done) == 2


def test_mode_filter_task_limits_note_list(qapp):
    _ = qapp
    task_window = _DummyTaskWindow(uuid="t-1")
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, _ = _make_main_window(task_windows=[task_window], note_windows=[note_window])
    tab = InfoTab(mw)

    tab.cmb_mode_filter.setCurrentIndex(tab.cmb_mode_filter.findData("task"))
    tab.refresh_data(immediate=True)

    note_rows = []
    for i in range(tab.notes_list.count()):
        item = tab.notes_list.item(i)
        if item is None:
            continue
        uuid = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if uuid:
            note_rows.append(uuid)
    assert note_rows == ["t-1"]


def test_due_filter_upcoming_limits_tasks(qapp):
    _ = qapp
    overdue = _DummyTaskWindow(uuid="t-overdue", text="over", due_at="2001-01-01T00:00:00")
    future = _DummyTaskWindow(uuid="t-future", text="future", due_at="2999-01-01T00:00:00")
    mw, _ = _make_main_window(task_windows=[overdue, future], note_windows=[])
    tab = InfoTab(mw)

    tab.cmb_due_filter.setCurrentIndex(tab.cmb_due_filter.findData("upcoming"))
    tab.refresh_data(immediate=True)

    assert _count_task_items(tab) == 1
    first = tab.tasks_list.item(0)
    assert first is not None
    assert str(first.data(Qt.ItemDataRole.UserRole)).startswith("t-future:")


def test_smart_view_today_applies_due_sort_controls(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    tab._on_smart_view_clicked("today", True)

    assert str(tab.cmb_due_filter.currentData()) == "today"
    assert str(tab.cmb_sort_by.currentData()) == "due"
    assert tab.btn_sort_desc.isChecked() is False


def test_manual_control_change_marks_custom_smart_view(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    tab._apply_preset_by_id("builtin:all")
    tab.cmb_due_filter.setCurrentIndex(tab.cmb_due_filter.findData("overdue"))

    assert tab._smart_view == "custom"
    assert all(not btn.isChecked() for btn in tab._smart_view_buttons.values())


def test_view_preset_save_update_delete_syncs_settings(qapp):
    _ = qapp
    save_calls = {"count": 0}

    def _save():
        save_calls["count"] += 1

    task_window = _DummyTaskWindow(uuid="t-1")
    mw, _ = _make_main_window(task_windows=[task_window], note_windows=[])
    mw.settings_manager = SimpleNamespace(save_app_settings=_save)
    tab = InfoTab(mw)

    tab.edit_search.setText("hello")
    tab._save_new_view_preset()
    assert len(mw.app_settings.info_view_presets) == 1
    preset_id = mw.app_settings.info_view_presets[0]["id"]
    assert preset_id.startswith("user:")
    assert save_calls["count"] >= 1

    tab.edit_search.setText("updated")
    tab._update_current_view_preset()
    assert mw.app_settings.info_view_presets[0]["filters"]["text"] == "updated"

    tab._delete_current_view_preset()
    assert mw.app_settings.info_view_presets == []
    assert mw.app_settings.info_last_view_preset_id == "builtin:all"


def test_overdue_badge_rendered_on_task_item(qapp):
    _ = qapp
    overdue = _DummyTaskWindow(uuid="t-overdue", text="over", due_at="2001-01-01T00:00:00")
    mw, _ = _make_main_window(task_windows=[overdue], note_windows=[])
    tab = InfoTab(mw)
    tab.refresh_data(immediate=True)

    first = tab.tasks_list.item(0)
    assert first is not None
    assert f"[{tr('info_badge_overdue')}]" in first.text()
