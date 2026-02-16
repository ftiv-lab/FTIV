from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QLabel

from ui.property_panel import PropertyPanel
from utils.translator import tr
from windows.text_renderer import TextRenderer
from windows.text_window_parts import tooltip_ops


def test_visual_task_title_divider_layout_contract() -> None:
    renderer = TextRenderer()
    fm = MagicMock()
    fm.height.return_value = 40

    window = MagicMock()
    window.title = "Task Title"
    window.is_vertical = False
    window.font_family = "Arial"
    window.font_size = 24

    layout = renderer._build_horizontal_meta_layout(
        window,
        fm,
        max_line_width=120,
        total_text_height=100,
        task_rail_width=16,
        m_top=8,
        m_bottom=8,
        m_left=8,
        m_right=8,
        outline_width=1.0,
    )

    assert layout["show_title"] is True
    assert layout["top_offset"] == layout["title_height"] + 1 + 4
    assert layout["canvas_height"] > 100


def test_visual_due_state_lines_include_today_and_overdue() -> None:
    window = SimpleNamespace(
        title="",
        due_at="2026-02-16T00:00:00",
        due_time="",
        due_timezone="",
        due_precision="date",
        tags=[],
        is_starred=False,
        is_archived=False,
        is_task_mode=lambda: False,
        _task_progress_counts=lambda: (0, 0),
    )

    with patch("windows.text_window_parts.tooltip_ops.classify_due", return_value="today"):
        lines_today = tooltip_ops.build_overlay_meta_tooltip_lines(window)
    assert tr("text_meta_due_today") in lines_today

    with patch("windows.text_window_parts.tooltip_ops.classify_due", return_value="overdue"):
        lines_overdue = tooltip_ops.build_overlay_meta_tooltip_lines(window)
    assert tr("text_meta_due_overdue") in lines_overdue


def test_visual_property_panel_summary_elides_long_text(qapp) -> None:
    _ = qapp
    mw = SimpleNamespace(info_tab=SimpleNamespace(refresh_data=lambda: None))
    panel = PropertyPanel(main_window=mw)

    panel.lbl_editing_target = QLabel("")
    panel.lbl_editing_target.resize(90, 20)
    panel.lbl_editing_target.setFixedWidth(90)
    panel.lbl_editing_target_preview = QLabel("")
    panel.lbl_editing_target_preview.resize(90, 20)
    panel.lbl_editing_target_preview.setFixedWidth(90)

    class ExtremelyLongEditingTargetNameForVisualRegression:
        def __init__(self, text: str) -> None:
            self.text = text

    target = ExtremelyLongEditingTargetNameForVisualRegression("A" * 240)
    panel._update_editing_target_labels(target)

    assert panel.lbl_editing_target is not None
    assert panel.lbl_editing_target_preview is not None
    assert panel.lbl_editing_target.toolTip() != ""
    assert panel.lbl_editing_target_preview.toolTip() != ""
    assert len(panel.lbl_editing_target.text()) < len(panel.lbl_editing_target.toolTip())
    assert len(panel.lbl_editing_target_preview.text()) < len(panel.lbl_editing_target_preview.toolTip())
    assert panel.lbl_editing_target_preview.isHidden() is False
