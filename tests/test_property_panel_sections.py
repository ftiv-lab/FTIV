from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QFont

from ui.property_panel import PropertyPanel
from ui.property_panel_sections.text_content_section import build_text_content_section, build_text_header_controls
from ui.property_panel_sections.text_style_section import build_text_style_section


class _DummyTextTarget:
    def __init__(self, *, task_mode: bool = False) -> None:
        self._task_mode = task_mode
        self.mode_calls: list[str] = []
        self.undo_calls: list[tuple[str, object, object]] = []
        self.update_text_calls = 0

        self.is_vertical = False
        self.title = "Section Title"
        self.tags = ["alpha", "beta"]
        self.due_at = "2026-03-10T00:00:00"
        self.due_precision = "datetime"
        self.due_time = "09:30"
        self.due_timezone = "Asia/Tokyo"
        self.is_starred = True
        self.is_archived = False

        self.font_family = "Arial"
        self.font_size = 24
        self.font_color = "#FFFFFFFF"
        self.text_opacity = 85
        self.text_gradient_enabled = True
        self.text_gradient_opacity = 70

    def is_task_mode(self) -> bool:
        return self._task_mode

    def set_content_mode(self, mode: str) -> None:
        self.mode_calls.append(mode)
        self._task_mode = mode == "task"

    def get_task_progress(self) -> tuple[int, int]:
        return 1, 3

    def complete_all_tasks(self) -> None:
        return None

    def uncomplete_all_tasks(self) -> None:
        return None

    def set_undoable_property(self, key: str, value: object, action: object = None) -> None:
        self.undo_calls.append((key, value, action))
        setattr(self, key, value)

    def update_text(self) -> None:
        self.update_text_calls += 1


def _make_panel() -> PropertyPanel:
    mw = SimpleNamespace(
        info_tab=SimpleNamespace(refresh_data=lambda: None),
        main_controller=SimpleNamespace(txt_actions=SimpleNamespace(save_as_default=MagicMock())),
    )
    panel = PropertyPanel(main_window=mw)
    panel.current_target = None
    return panel


def test_text_content_section_builds_core_widgets_and_due_fields(qapp) -> None:
    _ = qapp
    panel = _make_panel()
    target = _DummyTextTarget(task_mode=False)
    panel.current_target = target

    build_text_header_controls(panel, target)
    build_text_content_section(panel, target)

    assert panel.btn_task_mode is not None
    assert panel.btn_text_orientation is not None
    assert panel.edit_note_title.text() == "Section Title"
    assert panel.edit_note_tags.text() == "alpha, beta"
    assert panel.edit_note_due_at.text() == "2026-03-10"
    assert panel.cmb_note_due_precision.currentData() == "datetime"
    assert panel.edit_note_due_time.text() == "09:30"
    assert panel.edit_note_due_timezone.text() == "Asia/Tokyo"
    assert panel.edit_note_due_time.isEnabled() is True
    assert panel.btn_note_star.isChecked() is True
    assert panel.btn_note_archived.isChecked() is False


def test_text_content_section_task_mode_adds_progress_widgets(qapp) -> None:
    _ = qapp
    panel = _make_panel()
    target = _DummyTextTarget(task_mode=True)
    panel.current_target = target

    build_text_header_controls(panel, target)
    build_text_content_section(panel, target)

    assert panel.btn_task_mode.isChecked() is True
    assert panel.lbl_task_progress is not None
    assert panel.btn_complete_all is not None
    assert panel.btn_uncomplete_all is not None
    assert panel.btn_text_orientation.toolTip() != ""


def test_text_content_task_mode_button_invokes_set_content_mode(qapp) -> None:
    _ = qapp
    panel = _make_panel()
    target = _DummyTextTarget(task_mode=False)
    panel.current_target = target

    build_text_header_controls(panel, target)
    panel.btn_task_mode.click()

    assert "task" in target.mode_calls


def test_text_style_section_font_button_applies_selected_font(qapp) -> None:
    _ = qapp
    panel = _make_panel()
    target = _DummyTextTarget(task_mode=False)

    with patch("ui.property_panel_sections.text_style_section.choose_font", return_value=QFont("Times New Roman", 30)):
        build_text_style_section(panel, target)
        panel.btn_text_font.click()

    assert ("font_family", "Times New Roman", None) in target.undo_calls
    assert ("font_size", 30, None) in target.undo_calls
    assert target.update_text_calls == 1


def test_text_style_section_initial_state_and_save_default_button(qapp) -> None:
    _ = qapp
    panel = _make_panel()
    target = _DummyTextTarget(task_mode=False)

    build_text_style_section(panel, target)

    assert panel.btn_text_font.text() == "Arial (24pt)"
    assert panel.btn_text_gradient_toggle.isCheckable() is True
    assert panel.btn_text_gradient_toggle.isChecked() is True
    assert panel.btn_save_text_default is not None
    assert "💾" in panel.btn_save_text_default.text()
    panel.btn_save_text_default.click()
    panel.mw.main_controller.txt_actions.save_as_default.assert_called_once()
