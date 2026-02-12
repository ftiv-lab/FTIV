from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ui.tabs.text_tab import TextTab
from utils.translator import tr


class TextWindow:
    def __init__(self) -> None:
        self.mode_calls: list[str] = []

    def set_content_mode(self, mode: str) -> None:
        self.mode_calls.append(mode)


class ConnectorLabel:
    pass


def _make_main_window():
    mw = SimpleNamespace()
    mw.main_controller = MagicMock()
    mw.toggle_property_panel = MagicMock()
    mw.apply_preset_to_all_text_windows = MagicMock()
    mw._txt_open_style_gallery_selected = MagicMock()
    mw.file_manager = SimpleNamespace(load_scene_from_json=MagicMock())
    mw.last_selected_window = None
    return mw


def test_pick_due_date_sets_value(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())
    tab.edit_note_due_at.setText("")

    with patch("ui.tabs.text_tab.DatePickerDialog.pick_date", return_value="2026-03-01"):
        tab._pick_due_date_for_note()

    assert tab.edit_note_due_at.text() == "2026-03-01"


def test_pick_due_date_clear(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())
    tab.edit_note_due_at.setText("2026-03-01")

    with patch("ui.tabs.text_tab.DatePickerDialog.pick_date", return_value=""):
        tab._pick_due_date_for_note()

    assert tab.edit_note_due_at.text() == ""


def test_pick_due_date_cancel_keeps_previous(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())
    tab.edit_note_due_at.setText("2026-03-01")

    with patch("ui.tabs.text_tab.DatePickerDialog.pick_date", return_value=None):
        tab._pick_due_date_for_note()

    assert tab.edit_note_due_at.text() == "2026-03-01"


def test_text_tab_priority_menu_close_selected_routes_to_existing_handler(qapp):
    _ = qapp
    mw = _make_main_window()
    tab = TextTab(mw)

    tab.act_txt_close_selected.setEnabled(True)
    tab.act_txt_close_selected.trigger()

    mw.main_controller.txt_actions.run_selected_visibility_action.assert_called_once_with("close")


def test_text_tab_compact_labels_switch(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())

    tab.set_compact_mode(True)
    assert tab.txt_btn_manage_save_selected_json.text() == tr("menu_save_json_short")
    assert tab.txt_btn_manage_save_selected_json.toolTip() != ""

    tab.set_compact_mode(False)
    assert tab.txt_btn_manage_save_selected_json.text() == tr("menu_save_json")


def test_text_tab_uses_single_task_mode_toggle(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())

    assert hasattr(tab, "btn_content_mode_task")
    assert not hasattr(tab, "btn_content_mode_note")


def test_text_tab_task_mode_toggle_switches_task_and_note(qapp):
    _ = qapp
    mw = _make_main_window()
    selected = TextWindow()
    mw.window_manager = SimpleNamespace(last_selected_window=selected)
    tab = TextTab(mw)

    with patch.object(tab, "_sync_check_states") as mock_sync:
        tab._set_content_mode(True)
        tab._set_content_mode(False)

    assert selected.mode_calls == ["task", "note"]
    assert mock_sync.call_count == 2


def test_text_tab_task_mode_toggle_enabled_only_for_text_window(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())

    tab.update_enabled_state(TextWindow())
    assert tab.btn_content_mode_task.isEnabled() is True

    tab.update_enabled_state(ConnectorLabel())
    assert tab.btn_content_mode_task.isEnabled() is False

    tab.update_enabled_state(None)
    assert tab.btn_content_mode_task.isEnabled() is False


def test_text_tab_quick_due_buttons_update_due_input(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())
    tab.edit_note_due_at.setText("")

    with patch.object(tab, "_due_text_for_offset", return_value="2026-03-02"):
        tab._set_quick_due_offset(1)

    assert tab.edit_note_due_at.text() == "2026-03-02"

    tab._clear_quick_due()
    assert tab.edit_note_due_at.text() == ""


def test_text_tab_selected_label_tooltip_includes_property_panel_hint(qapp):
    _ = qapp
    tab = TextTab(_make_main_window())
    selected = TextWindow()
    selected.text = "first line\nsecond line"

    with patch.object(tab, "_sync_check_states"), patch.object(tab, "update_enabled_state"):
        tab.on_selection_changed(selected)

    assert tr("hint_shared_target_with_property_panel") in tab.txt_selected_label.toolTip()
