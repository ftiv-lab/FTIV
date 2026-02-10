from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ui.tabs.text_tab import TextTab


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
