from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton

from ui.property_panel import PropertyPanel


class _DummyTarget:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def set_title_and_tags(self, title: str, tags: list[str]) -> None:
        self.calls.append(("set_title_and_tags", (title, list(tags))))

    def set_starred(self, value: bool) -> None:
        self.calls.append(("set_starred", bool(value)))

    def set_due_at(self, value: str) -> None:
        self.calls.append(("set_due_at", value))

    def clear_due_at(self) -> None:
        self.calls.append(("clear_due_at", None))

    def set_archived(self, value: bool) -> None:
        self.calls.append(("set_archived", bool(value)))


class _DummyTargetWithUndo(_DummyTarget):
    def __init__(self) -> None:
        super().__init__()
        self.undo_calls: list[tuple[str, object, object]] = []

    def set_undoable_property(self, key: str, value: object, action: object = None) -> None:
        self.undo_calls.append((key, value, action))


class _DummyOrientationTarget:
    def __init__(self, is_vertical: bool = False, task_mode: bool = False) -> None:
        self.calls: list[tuple[str, object, str]] = []
        self.is_vertical = is_vertical
        self._task_mode = task_mode
        self.text_opacity = 100
        self.background_opacity = 100
        self.background_corner_ratio = 0.0
        self.shadow_opacity = 100
        self.shadow_blur = 0
        self.shadow_enabled = False
        self.shadow_color = "#000000FF"
        self.shadow_offset_x = 0.0
        self.shadow_offset_y = 0.0

    def is_task_mode(self) -> bool:
        return self._task_mode

    def set_undoable_property(self, key: str, value: object, action: str) -> None:
        if key == "is_vertical":
            self.is_vertical = bool(value)
        self.calls.append((key, value, action))


def _make_panel():
    mw = SimpleNamespace(info_tab=SimpleNamespace(refresh_data=lambda: None))
    panel = PropertyPanel(main_window=mw)
    panel.edit_note_title = QLineEdit()
    panel.edit_note_tags = QLineEdit()
    panel.edit_note_due_at = QLineEdit()
    panel.cmb_note_due_precision = QComboBox()
    panel.cmb_note_due_precision.addItem("Date", "date")
    panel.cmb_note_due_precision.addItem("Datetime", "datetime")
    panel.edit_note_due_time = QLineEdit()
    panel.edit_note_due_timezone = QLineEdit()
    panel.btn_note_star = QPushButton()
    panel.btn_note_star.setCheckable(True)
    panel.btn_note_archived = QPushButton()
    panel.btn_note_archived.setCheckable(True)
    panel.btn_apply_note_meta = QPushButton()
    return panel


def test_pick_note_due_date_updates_line_edit(qapp):
    _ = qapp
    panel = _make_panel()
    panel.edit_note_due_at.setText("")

    with patch("ui.property_panel.DatePickerDialog.pick_date", return_value="2026-03-10"):
        panel._pick_note_due_date()

    assert panel.edit_note_due_at.text() == "2026-03-10"


def test_pick_note_due_date_cancel_keeps_value(qapp):
    _ = qapp
    panel = _make_panel()
    panel.edit_note_due_at.setText("2026-03-10")

    with patch("ui.property_panel.DatePickerDialog.pick_date", return_value=None):
        panel._pick_note_due_date()

    assert panel.edit_note_due_at.text() == "2026-03-10"


def test_quick_due_offset_and_clear_updates_input_only(qapp):
    _ = qapp
    panel = _make_panel()

    with patch.object(panel, "_due_text_for_offset", return_value="2026-03-11"):
        panel._set_quick_due_offset(1)
    assert panel.edit_note_due_at.text() == "2026-03-11"

    panel._clear_quick_due()
    assert panel.edit_note_due_at.text() == ""


def test_apply_note_meta_invalid_due_shows_warning(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyTarget()
    panel.edit_note_due_at.setText("2026/03/10")

    with patch("ui.property_panel.QMessageBox.warning") as mock_warning:
        ok = panel._apply_note_metadata_to_target(target)

    assert ok is False
    mock_warning.assert_called_once()
    assert target.calls == []


def test_apply_note_meta_invalid_due_blur_is_soft_warning(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyTarget()
    panel.edit_note_due_at.setText("2026/03/10")

    with patch("ui.property_panel.QMessageBox.warning") as mock_warning:
        ok = panel._apply_note_metadata_to_target(target, trigger_source="blur")

    assert ok is False
    mock_warning.assert_not_called()
    assert panel.edit_note_due_at.property("inputInvalid") is True


def test_apply_note_meta_valid_due_updates_target(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyTarget()
    panel.edit_note_title.setText("Title")
    panel.edit_note_tags.setText("a, b, A")
    panel.edit_note_due_at.setText("2026-03-10")
    panel.btn_note_star.setChecked(True)
    panel.btn_note_archived.setChecked(True)

    with patch.object(panel, "update_property_values", MagicMock()):
        ok = panel._apply_note_metadata_to_target(target)

    assert ok is True
    assert ("set_title_and_tags", ("Title", ["a", "b"])) in target.calls
    assert ("set_starred", True) in target.calls
    assert ("set_due_at", "2026-03-10T00:00:00") in target.calls
    assert ("set_archived", True) in target.calls


def test_text_orientation_toggle_routes_to_undoable_property_and_resync(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyOrientationTarget(is_vertical=False, task_mode=False)

    with patch.object(panel, "update_property_values", MagicMock()) as mock_update:
        panel._on_text_orientation_toggled(True, target)

    assert ("is_vertical", True, "update_text") in target.calls
    mock_update.assert_called_once()


def test_update_text_values_syncs_orientation_toggle_in_task_mode(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyOrientationTarget(is_vertical=False, task_mode=True)
    panel.current_target = target

    panel.btn_task_mode = QPushButton()
    panel.btn_task_mode.setCheckable(True)
    panel.btn_task_mode.setChecked(True)

    panel.btn_text_orientation = QPushButton()
    panel.btn_text_orientation.setCheckable(True)
    panel.btn_text_orientation.setChecked(True)

    panel._update_text_values()

    assert panel.btn_text_orientation.isChecked() is False
    assert panel.btn_text_orientation.toolTip() != ""


def test_apply_note_meta_invalid_due_time_warns_but_saves_date(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyTargetWithUndo()
    panel.edit_note_due_at.setText("2026-03-10")
    panel.cmb_note_due_precision.setCurrentIndex(panel.cmb_note_due_precision.findData("datetime"))
    panel.edit_note_due_time.setText("99:99")
    panel.edit_note_due_timezone.setText("Asia/Tokyo")

    with (
        patch("ui.property_panel.QMessageBox.warning") as mock_warning,
        patch.object(panel, "update_property_values", MagicMock()),
    ):
        ok = panel._apply_note_metadata_to_target(target)

    assert ok is True
    assert ("set_due_at", "2026-03-10T00:00:00") in target.calls
    assert ("due_precision", "date", None) in target.undo_calls
    assert ("due_time", "", None) in target.undo_calls
    assert ("due_timezone", "", None) in target.undo_calls
    mock_warning.assert_called_once()


def test_apply_note_meta_invalid_timezone_warns_and_clears_timezone(qapp):
    _ = qapp
    panel = _make_panel()
    target = _DummyTargetWithUndo()
    panel.edit_note_due_at.setText("2026-03-10")
    panel.cmb_note_due_precision.setCurrentIndex(panel.cmb_note_due_precision.findData("datetime"))
    panel.edit_note_due_time.setText("09:30")
    panel.edit_note_due_timezone.setText("Mars/OlympusMons")

    with (
        patch("ui.property_panel.QMessageBox.warning") as mock_warning,
        patch.object(panel, "update_property_values", MagicMock()),
    ):
        ok = panel._apply_note_metadata_to_target(target)

    assert ok is True
    assert ("set_due_at", "2026-03-10T00:00:00") in target.calls
    assert ("due_precision", "datetime", None) in target.undo_calls
    assert ("due_time", "09:30", None) in target.undo_calls
    assert ("due_timezone", "", None) in target.undo_calls
    mock_warning.assert_called_once()


def test_property_panel_section_state_persists_to_app_settings(qapp):
    _ = qapp
    settings = SimpleNamespace(property_panel_section_state={})
    settings_manager = SimpleNamespace(save_app_settings=MagicMock())
    mw = SimpleNamespace(
        info_tab=SimpleNamespace(refresh_data=lambda: None), app_settings=settings, settings_manager=settings_manager
    )
    panel = PropertyPanel(main_window=mw)

    panel._save_property_panel_section_state("text_content", False)

    assert settings.property_panel_section_state["text_content"] is False
    settings_manager.save_app_settings.assert_called_once()


def test_create_collapsible_group_uses_saved_state(qapp):
    _ = qapp
    settings = SimpleNamespace(property_panel_section_state={"shadow": False})
    mw = SimpleNamespace(
        info_tab=SimpleNamespace(refresh_data=lambda: None), app_settings=settings, settings_manager=None
    )
    panel = PropertyPanel(main_window=mw)

    _ = panel.create_collapsible_group("Shadow", expanded=True, state_key="shadow")

    assert panel._section_boxes["shadow"].toggle_button.isChecked() is False


def test_editing_target_preview_label_elides_long_text_and_keeps_tooltip(qapp):
    _ = qapp
    panel = _make_panel()
    panel.lbl_editing_target = QLabel("")
    panel.lbl_editing_target_preview = QLabel("")
    panel.lbl_editing_target_preview.resize(80, 20)
    panel.lbl_editing_target_preview.setFixedWidth(80)

    raw = "A" * 200
    target = SimpleNamespace(text=raw)
    panel._update_editing_target_labels(target)

    assert panel.lbl_editing_target.text() != ""
    assert panel.lbl_editing_target_preview.toolTip().endswith(raw)
    assert len(panel.lbl_editing_target_preview.text()) < len(panel.lbl_editing_target_preview.toolTip())
    assert panel.lbl_editing_target_preview.isHidden() is False


def test_editing_target_preview_label_hides_for_empty_text(qapp):
    _ = qapp
    panel = _make_panel()
    panel.lbl_editing_target = QLabel("")
    panel.lbl_editing_target_preview = QLabel("")

    target = SimpleNamespace(text="   ")
    panel._update_editing_target_labels(target)

    assert panel.lbl_editing_target.text() != ""
    assert panel.lbl_editing_target_preview.text() == ""
    assert panel.lbl_editing_target_preview.toolTip() == ""
    assert panel.lbl_editing_target_preview.isHidden() is True
