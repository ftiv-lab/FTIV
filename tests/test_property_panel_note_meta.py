from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QLineEdit, QPushButton

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


def _make_panel():
    mw = SimpleNamespace(info_tab=SimpleNamespace(refresh_data=lambda: None))
    panel = PropertyPanel(main_window=mw)
    panel.edit_note_title = QLineEdit()
    panel.edit_note_tags = QLineEdit()
    panel.edit_note_due_at = QLineEdit()
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
