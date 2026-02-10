from types import SimpleNamespace

from PySide6.QtCore import Qt

from ui.tabs.info_tab import InfoTab


class _DummyTaskWindow:
    def __init__(self) -> None:
        self.uuid = "tw-1"
        self.text = "task one"
        self.content_mode = "task"
        self.title = "Tasks"
        self.tags = []
        self.is_starred = False
        self.created_at = ""
        self.updated_at = ""
        self.due_at = ""
        self.is_archived = False
        self._states = [False]

    def iter_task_items(self):
        return [SimpleNamespace(line_index=0, text="task one", done=self._states[0])]

    def toggle_task_line_state(self, index: int) -> None:
        if index == 0:
            self._states[0] = not self._states[0]


class _DummyNoteWindow:
    def __init__(self) -> None:
        self.uuid = "nw-1"
        self.text = "note body"
        self.content_mode = "note"
        self.title = "Memo"
        self.tags = []
        self.is_starred = False
        self.created_at = ""
        self.updated_at = ""
        self.due_at = ""
        self.is_archived = False

    def set_starred(self, value: bool) -> None:
        self.is_starred = bool(value)


class _DummyInfoActions:
    def __init__(self, tab: InfoTab, task_window: _DummyTaskWindow, note_window: _DummyNoteWindow) -> None:
        self.tab = tab
        self.task_window = task_window
        self.note_window = note_window

    def toggle_task(self, item_key: str) -> None:
        _, idx = item_key.rsplit(":", 1)
        self.task_window.toggle_task_line_state(int(idx))
        # Rebuild list immediately (this used to invalidate QListWidgetItem)
        self.tab.refresh_data()

    def set_star(self, window_uuid: str, value: bool) -> None:
        if window_uuid == self.note_window.uuid:
            self.note_window.set_starred(value)
        self.tab.refresh_data()

    def focus_window(self, window_uuid: str) -> None:
        _ = window_uuid


def _make_main_window(tab_ref=None):
    task_window = _DummyTaskWindow()
    note_window = _DummyNoteWindow()
    wm = SimpleNamespace(text_windows=[task_window, note_window])
    mw = SimpleNamespace(window_manager=wm)
    if tab_ref is not None:
        actions = _DummyInfoActions(tab_ref, task_window, note_window)
        mw.main_controller = SimpleNamespace(info_actions=actions)
    return mw, task_window, note_window


def test_task_item_changed_safe_when_action_refreshes(qapp):
    _ = qapp
    mw, task_window, note_window = _make_main_window()
    tab = InfoTab(mw)
    mw.main_controller = SimpleNamespace(info_actions=_DummyInfoActions(tab, task_window, note_window))

    item = tab.tasks_list.item(0)
    assert item is not None

    # Must not raise RuntimeError even if action refreshes list immediately.
    item.setCheckState(Qt.CheckState.Checked)
    assert task_window._states[0] is True


def test_note_item_changed_safe_when_action_refreshes(qapp):
    _ = qapp
    mw, task_window, note_window = _make_main_window()
    tab = InfoTab(mw)
    mw.main_controller = SimpleNamespace(info_actions=_DummyInfoActions(tab, task_window, note_window))

    item = None
    for i in range(tab.notes_list.count()):
        candidate = tab.notes_list.item(i)
        if candidate is None:
            continue
        if str(candidate.data(Qt.ItemDataRole.UserRole) or "") == note_window.uuid:
            item = candidate
            break
    assert item is not None

    # Must not raise RuntimeError even if action refreshes list immediately.
    item.setCheckState(Qt.CheckState.Checked)
    assert note_window.is_starred is True
