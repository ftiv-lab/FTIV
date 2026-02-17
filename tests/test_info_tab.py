from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import Qt

from ui.tabs.info_tab import InfoTab
from utils.tag_ops import merge_tags
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

    def set_starred(self, value: bool) -> None:
        self.is_starred = bool(value)

    def set_tags(self, tags) -> None:
        self.tags = list(tags)


class _DummyNoteWindow:
    def __init__(self, uuid: str = "nw-1", is_archived: bool = False, tags=None) -> None:
        if tags is None:
            tags = []
        self.uuid = uuid
        self.text = "note body"
        self.content_mode = "note"
        self.title = "Memo"
        self.tags = list(tags)
        self.is_starred = False
        self.created_at = ""
        self.updated_at = ""
        self.due_at = ""
        self.is_archived = is_archived

    def set_starred(self, value: bool) -> None:
        self.is_starred = bool(value)

    def set_archived(self, value: bool) -> None:
        self.is_archived = bool(value)

    def set_tags(self, tags) -> None:
        self.tags = list(tags)


class _DummyInfoActions:
    def __init__(self, tab: InfoTab, windows: list[object]) -> None:
        self.tab = tab
        self.windows = windows
        self.last_bulk_archive: list[str] = []
        self.last_bulk_done: list[str] = []
        self.last_bulk_star: list[str] = []
        self.last_bulk_tags: tuple[list[str], list[str], list[str]] = ([], [], [])
        self.logs: list[dict[str, object]] = []

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
        self.logs.append(
            {
                "at": "2026-02-10T10:00:00",
                "action": "bulk_archive" if value else "bulk_restore",
                "target_count": len(list(window_uuids)),
                "detail": "",
            }
        )
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

    def bulk_set_star(self, window_uuids: list[str], value: bool) -> None:
        self.last_bulk_star = list(window_uuids)
        for window_uuid in window_uuids:
            w = self._find(window_uuid)
            if w is not None and hasattr(w, "set_starred"):
                w.set_starred(value)
        self.logs.append(
            {
                "at": "2026-02-10T10:01:00",
                "action": "bulk_star" if value else "bulk_unstar",
                "target_count": len(list(window_uuids)),
                "detail": "",
            }
        )
        self.tab.refresh_data(immediate=True)

    def bulk_merge_tags(self, window_uuids: list[str], add_tags: list[str], remove_tags: list[str]) -> None:
        self.last_bulk_tags = (list(window_uuids), list(add_tags), list(remove_tags))
        for window_uuid in window_uuids:
            w = self._find(window_uuid)
            if w is None:
                continue
            raw_tags = getattr(w, "tags", [])
            current = list(raw_tags) if isinstance(raw_tags, list) else []
            merged = merge_tags(current, add_tags, remove_tags)
            if hasattr(w, "set_tags"):
                w.set_tags(merged)
        self.logs.append(
            {
                "at": "2026-02-10T10:02:00",
                "action": "bulk_tags_merge",
                "target_count": len(list(window_uuids)),
                "detail": "tags",
            }
        )
        self.tab.refresh_data(immediate=True)

    def get_operation_logs(self, limit=None):
        if limit is None:
            return list(self.logs)
        return list(self.logs[-int(limit) :])

    def clear_operation_logs(self) -> None:
        self.logs = []
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
    app_settings = SimpleNamespace(
        main_window_width=0,
        main_window_height=0,
        main_window_pos_x=None,
        main_window_pos_y=None,
        info_view_presets=[],
        info_last_view_preset_id="builtin:all",
        info_operation_logs=[],
        info_layout_mode="auto",
        info_advanced_filters_expanded=False,
    )
    settings_manager = SimpleNamespace(save_app_settings=lambda: None)
    mw = SimpleNamespace(window_manager=wm, app_settings=app_settings, settings_manager=settings_manager)
    return mw, text_windows


def _iter_all_tree_items(tree):
    """QTreeWidget の全アイテム（トップレベル + 子）をフラットに列挙する。"""
    result = []
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if top is None:
            continue
        result.append(top)
        for j in range(top.childCount()):
            child = top.child(j)
            if child is not None:
                result.append(child)
    return result


def _find_note_item(tab: InfoTab, window_uuid: str):
    for item in _iter_all_tree_items(tab.notes_tree):
        if str(item.data(0, Qt.ItemDataRole.UserRole) or "") == window_uuid:
            return item
    return None


def _count_task_items(tab: InfoTab) -> int:
    count = 0
    for item in _iter_all_tree_items(tab.tasks_tree):
        if ":" in str(item.data(0, Qt.ItemDataRole.UserRole) or ""):
            count += 1
    return count


def _find_first_task_item(tab: InfoTab):
    """最初の実タスクアイテム（グループヘッダーを除く）を返す。"""
    for item in _iter_all_tree_items(tab.tasks_tree):
        if ":" in str(item.data(0, Qt.ItemDataRole.UserRole) or ""):
            return item
    return None


def test_task_item_changed_safe_when_action_refreshes(qapp):
    _ = qapp
    mw, text_windows = _make_main_window()
    tab = InfoTab(mw)
    mw.main_controller = SimpleNamespace(info_actions=_DummyInfoActions(tab, text_windows))

    item = _find_first_task_item(tab)
    assert item is not None

    # Must not crash even if action refreshes list immediately.
    # Action is deferred via QTimer.singleShot(0), so processEvents is needed.
    item.setCheckState(0, Qt.CheckState.Checked)
    qapp.processEvents()
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

    # Must not crash even if action refreshes list immediately.
    # Action is deferred via QTimer.singleShot(0), so processEvents is needed.
    item.setCheckState(0, Qt.CheckState.Checked)
    qapp.processEvents()
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
    first = _find_first_task_item(tab)
    assert first is not None
    assert str(first.data(0, Qt.ItemDataRole.UserRole)).startswith("t-overdue:")


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

    for item in _iter_all_tree_items(tab.tasks_tree):
        if ":" in str(item.data(0, Qt.ItemDataRole.UserRole) or ""):
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
    for item in _iter_all_tree_items(tab.notes_tree):
        uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
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
    first = _find_first_task_item(tab)
    assert first is not None
    assert str(first.data(0, Qt.ItemDataRole.UserRole)).startswith("t-future:")


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
    assert "mode_filter" not in mw.app_settings.info_view_presets[0]["filters"]
    assert save_calls["count"] >= 1

    tab.edit_search.setText("updated")
    tab._update_current_view_preset()
    assert mw.app_settings.info_view_presets[0]["filters"]["text"] == "updated"
    assert "mode_filter" not in mw.app_settings.info_view_presets[0]["filters"]

    tab._delete_current_view_preset()
    assert mw.app_settings.info_view_presets == []
    assert mw.app_settings.info_last_view_preset_id == "builtin:all"


def test_overdue_badge_rendered_on_task_item(qapp):
    _ = qapp
    overdue = _DummyTaskWindow(uuid="t-overdue", text="over", due_at="2001-01-01T00:00:00")
    mw, _ = _make_main_window(task_windows=[overdue], note_windows=[])
    tab = InfoTab(mw)
    tab.refresh_data(immediate=True)

    first = _find_first_task_item(tab)
    assert first is not None
    assert f"[{tr('info_badge_overdue')}]" in first.text(0)


def test_archive_scope_archived_filters_task_rows(qapp):
    _ = qapp
    active = _DummyTaskWindow(uuid="t-active", text="a", is_archived=False)
    archived = _DummyTaskWindow(uuid="t-archived", text="b", is_archived=True)
    mw, _ = _make_main_window(task_windows=[active, archived], note_windows=[])
    tab = InfoTab(mw)

    tab.cmb_archive_scope.setCurrentIndex(tab.cmb_archive_scope.findData("archived"))
    tab.refresh_data(immediate=True)

    assert _count_task_items(tab) == 1
    first = _find_first_task_item(tab)
    assert first is not None
    assert str(first.data(0, Qt.ItemDataRole.UserRole)).startswith("t-archived:")


def test_builtin_archived_preset_sets_archive_scope(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    tab._apply_preset_by_id("builtin:archived")

    assert str(tab.cmb_archive_scope.currentData()) == "archived"
    assert tab._smart_view == "archived"


def test_restore_selected_updates_windows(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1", is_archived=True)
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    tab.cmb_archive_scope.setCurrentIndex(tab.cmb_archive_scope.findData("all"))
    tab.refresh_data(immediate=True)
    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    note_item.setSelected(True)

    tab._restore_selected()
    assert note_window.is_archived is False
    assert actions.last_bulk_archive == ["n-1"]


def test_bulk_star_selected_updates_windows(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    note_item.setSelected(True)

    tab._apply_bulk_star(True)
    assert note_window.is_starred is True
    assert actions.last_bulk_star == ["n-1"]


def test_bulk_edit_tags_selected_calls_dialog_and_action(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1", tags=["old"])
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    note_item.setSelected(True)

    with patch("ui.tabs.info_tab.BulkTagEditDialog.ask", return_value=(["new"], ["old"])):
        tab._edit_tags_selected()

    assert note_window.tags == ["new"]
    assert actions.last_bulk_tags == (["n-1"], ["new"], ["old"])


def test_archived_badge_rendered_on_note_item(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1", is_archived=True)
    mw, _ = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    tab.cmb_archive_scope.setCurrentIndex(tab.cmb_archive_scope.findData("all"))
    tab.refresh_data(immediate=True)

    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    assert f"[{tr('info_badge_archived')}]" in note_item.text(0)


def test_operation_log_panel_renders_and_clears(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    actions.logs = [
        {"at": "2026-02-10T11:00:00", "action": "bulk_archive", "target_count": 1, "detail": ""},
        {"at": "2026-02-10T11:01:00", "action": "bulk_star", "target_count": 1, "detail": ""},
    ]
    mw.main_controller = SimpleNamespace(info_actions=actions)

    tab.refresh_data(immediate=True)
    assert tr("info_log_action_bulk_star") in tab.lbl_operation_summary.text()

    tab._clear_operation_logs()
    assert tab.lbl_operation_summary.text() == tr("info_operation_empty")


def test_layout_mode_compact_from_settings_applies_short_labels(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    mw.app_settings.info_layout_mode = "compact"

    tab = InfoTab(mw)

    assert tab._effective_layout_mode == "compact"
    assert tab.btn_refresh.text() == tr("info_refresh_short")
    assert tab.btn_bulk_actions.text() == tr("info_bulk_actions_short")


def test_layout_mode_auto_switches_compact_and_regular(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    mw.app_settings.info_layout_mode = "auto"
    tab = InfoTab(mw)

    tab.resize(320, 600)
    tab._apply_layout_mode(force=True)
    assert tab._effective_layout_mode == "compact"

    tab.resize(420, 600)
    tab._apply_layout_mode(force=True)
    assert tab._effective_layout_mode == "regular"


def test_advanced_filter_forced_collapsed_on_auto_mode(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    mw.app_settings.info_layout_mode = "auto"
    mw.app_settings.info_advanced_filters_expanded = True

    tab = InfoTab(mw)

    assert tab.advanced_filters_box.toggle_button.isChecked() is False


def test_bulk_menu_action_uses_existing_bulk_handler(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    mw.main_controller = SimpleNamespace(info_actions=actions)

    note_item = _find_note_item(tab, "n-1")
    assert note_item is not None
    note_item.setSelected(True)

    tab.btn_star_selected.trigger()
    assert note_window.is_starred is True
    assert actions.last_bulk_star == ["n-1"]


def test_preset_action_menu_save_creates_user_preset(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    tab.edit_search.setText("hello")
    tab.btn_view_save.trigger()

    assert len(mw.app_settings.info_view_presets) == 1
    assert str(mw.app_settings.info_view_presets[0]["id"]).startswith("user:")
    assert "mode_filter" not in mw.app_settings.info_view_presets[0]["filters"]


def test_canonical_scope_preset_is_applied_without_legacy_mode_filter(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    mw.app_settings.info_view_presets = [
        {
            "id": "user:1",
            "name": "Canonical",
            "filters": {"item_scope": "tasks", "content_mode_filter": "task", "due_filter": "today"},
        }
    ]
    mw.app_settings.info_last_view_preset_id = "user:1"

    tab = InfoTab(mw)

    assert str(tab.cmb_mode_filter.currentData() or "") == "task"
    assert len(mw.app_settings.info_view_presets) == 1
    filters = mw.app_settings.info_view_presets[0]["filters"]
    assert filters["item_scope"] == "tasks"
    assert filters["content_mode_filter"] == "task"
    assert "mode_filter" not in filters


def test_operation_summary_and_dialog(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, text_windows = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    actions = _DummyInfoActions(tab, text_windows)
    actions.logs = [
        {"at": "2026-02-10T11:00:00", "action": "bulk_archive", "target_count": 1, "detail": ""},
        {"at": "2026-02-10T11:01:00", "action": "bulk_star", "target_count": 1, "detail": ""},
    ]
    mw.main_controller = SimpleNamespace(info_actions=actions)

    tab.refresh_data(immediate=True)
    assert tr("info_log_action_bulk_star") in tab.lbl_operation_summary.text()

    with patch("ui.tabs.info_tab.InfoOperationsDialog.exec", return_value=0):
        tab._open_operations_dialog()
    assert tab._operations_dialog is not None
    first = tab._operations_dialog.operations_list.item(0)
    assert first is not None
    assert tr("info_log_action_bulk_star") in first.text()


def test_info_tab_core_controls_visible_on_320px_width(qapp):
    mw, _ = _make_main_window()
    tab = InfoTab(mw)
    tab.resize(320, 600)
    tab.show()
    qapp.processEvents()
    tab._apply_layout_mode(force=True)

    assert tab.cmb_view_preset.isVisible() is True
    assert tab.cmb_smart_view.isVisible() is True
    assert tab.cmb_archive_scope.isVisible() is True
    assert tab.btn_bulk_actions.isVisible() is True


def test_smart_view_combo_items_have_tooltips(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    for value, tip_key in [
        ("all", "info_view_tip_all"),
        ("open", "info_view_tip_open"),
        ("today", "info_view_tip_today"),
        ("overdue", "info_view_tip_overdue"),
        ("starred", "info_view_tip_starred"),
        ("archived", "info_view_tip_archived"),
        ("custom", "info_view_tip_custom"),
    ]:
        idx = tab.cmb_smart_view.findData(value)
        assert idx >= 0
        assert tab.cmb_smart_view.itemData(idx, Qt.ItemDataRole.ToolTipRole) == tr(tip_key)


def test_empty_state_hint_first_time_shows_cta(qapp):
    _ = qapp
    mw, _ = _make_main_window(task_windows=[], note_windows=[])
    tab = InfoTab(mw)
    tab.refresh_data(immediate=True)

    assert tab.empty_state_row.isHidden() is False
    assert tab.lbl_empty_state_hint.text() == tr("info_empty_state_first_time")
    assert tab.btn_empty_add_text.isHidden() is False


def test_empty_state_hint_filtered_hides_cta(qapp):
    _ = qapp
    note_window = _DummyNoteWindow(uuid="n-1")
    mw, _ = _make_main_window(task_windows=[], note_windows=[note_window])
    tab = InfoTab(mw)
    tab.edit_search.setText("no-match-keyword")
    tab.refresh_data(immediate=True)

    assert tab.empty_state_row.isHidden() is False
    assert tab.lbl_empty_state_hint.text() == tr("info_empty_state_filtered")
    assert tab.btn_empty_add_text.isHidden() is True


def test_refresh_data_reuses_cached_index_for_unchanged_windows(qapp):
    _ = qapp
    mw, _ = _make_main_window()
    tab = InfoTab(mw)

    with patch.object(tab.index_manager, "build_index", wraps=tab.index_manager.build_index) as build_index_spy:
        tab.refresh_data(immediate=True)
        tab.refresh_data(immediate=True)
        assert build_index_spy.call_count == 0


def test_refresh_data_rebuilds_index_when_window_snapshot_changes(qapp):
    _ = qapp
    task_window = _DummyTaskWindow(uuid="tw-cache")
    mw, _ = _make_main_window(task_windows=[task_window], note_windows=[])
    tab = InfoTab(mw)

    with patch.object(tab.index_manager, "build_index", wraps=tab.index_manager.build_index) as build_index_spy:
        task_window.text = "updated task body"
        tab.refresh_data(immediate=True)
        assert build_index_spy.call_count == 1
