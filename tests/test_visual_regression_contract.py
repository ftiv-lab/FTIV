from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QLabel

from models.window_config import TextWindowConfig
from ui.property_panel import PropertyPanel
from ui.tabs.about_tab import AboutTab
from utils.translator import tr
from windows.text_renderer import TextRenderer
from windows.text_window import TextWindow
from windows.text_window_parts import tooltip_ops


def _load_visual_profiles() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = root / "config" / "ui" / "phase10b_visual_profiles.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["cases"]


def _visual_assert(condition: bool, *, case_id: str, widget_state: dict[str, Any]) -> None:
    if condition:
        return
    profile = _load_visual_profiles()[case_id]
    message = json.dumps(
        {
            "case_id": case_id,
            "profile": profile,
            "widget_state": widget_state,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    pytest.fail(f"visual regression contract violated\n{message}")


def _make_main_window_stub_for_property_panel() -> SimpleNamespace:
    return SimpleNamespace(info_tab=SimpleNamespace(refresh_data=lambda: None))


def _make_main_window_stub_for_about_tab() -> SimpleNamespace:
    settings = SimpleNamespace(
        about_section_state={},
        render_debounce_ms=25,
        wheel_debounce_ms=50,
        glyph_cache_size=512,
    )
    settings_manager = SimpleNamespace(save_app_settings=MagicMock())
    return SimpleNamespace(
        app_settings=settings,
        settings_manager=settings_manager,
        show_manual_dialog=MagicMock(),
        show_license_dialog=MagicMock(),
        show_about_dialog=MagicMock(),
        open_log_folder=MagicMock(),
        open_shop_page=MagicMock(),
        copy_shop_url=MagicMock(),
        apply_performance_settings=MagicMock(),
    )


def _make_text_window() -> TextWindow:
    with patch.object(TextWindow, "__init__", lambda self, *a, **kw: None):
        obj = TextWindow.__new__(TextWindow)
    obj.config = TextWindowConfig()
    obj.main_window = MagicMock()
    obj.main_window.json_directory = "."
    obj.main_window.settings_manager = MagicMock()
    obj.main_window.settings_manager.load_text_archetype.return_value = None
    obj.main_window.undo_stack = MagicMock()
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    obj._previous_text_opacity = 100
    obj._previous_background_opacity = 100
    obj._render_debounce_ms = 25
    obj._wheel_render_relax_timer = MagicMock()
    obj.canvas_size = MagicMock()
    return obj


def test_visual_contract_task_title_divider_horizontal() -> None:
    renderer = TextRenderer()
    fm = MagicMock()
    fm.height.return_value = 40

    window = MagicMock()
    window.title = "Task title"
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

    _visual_assert(
        layout["show_title"] is True and layout["top_offset"] > 0,
        case_id="task_title_divider_horizontal",
        widget_state={"show_title": layout["show_title"], "top_offset": layout["top_offset"]},
    )


def test_visual_contract_task_title_divider_vertical_hidden() -> None:
    renderer = TextRenderer()
    fm = MagicMock()
    fm.height.return_value = 40

    window = MagicMock()
    window.title = "Task title"
    window.is_vertical = True
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

    _visual_assert(
        layout["show_title"] is False and layout["top_offset"] == 0,
        case_id="task_title_divider_vertical",
        widget_state={"show_title": layout["show_title"], "top_offset": layout["top_offset"]},
    )


def _make_due_window(due_at: str) -> SimpleNamespace:
    return SimpleNamespace(
        title="",
        due_at=due_at,
        due_time="",
        due_timezone="",
        due_precision="date",
        tags=[],
        is_starred=False,
        is_archived=False,
        is_task_mode=lambda: False,
        _task_progress_counts=lambda: (0, 0),
    )


def test_visual_contract_due_state_today_line() -> None:
    window = _make_due_window("2026-02-16T00:00:00")
    with patch("windows.text_window_parts.tooltip_ops.classify_due", return_value="today"):
        lines = tooltip_ops.build_overlay_meta_tooltip_lines(window)
    _visual_assert(
        tr("text_meta_due_today") in lines,
        case_id="due_state_today",
        widget_state={"lines": lines},
    )


def test_visual_contract_due_state_overdue_line() -> None:
    window = _make_due_window("2026-02-16T00:00:00")
    with patch("windows.text_window_parts.tooltip_ops.classify_due", return_value="overdue"):
        lines = tooltip_ops.build_overlay_meta_tooltip_lines(window)
    _visual_assert(
        tr("text_meta_due_overdue") in lines,
        case_id="due_state_overdue",
        widget_state={"lines": lines},
    )


def test_visual_contract_due_state_none_has_no_due_badge() -> None:
    window = _make_due_window("")
    lines = tooltip_ops.build_overlay_meta_tooltip_lines(window)
    _visual_assert(
        tr("text_meta_due_today") not in lines and tr("text_meta_due_overdue") not in lines,
        case_id="due_state_none",
        widget_state={"lines": lines},
    )


def test_visual_contract_property_panel_summary_short(qapp) -> None:
    _ = qapp
    panel = PropertyPanel(main_window=_make_main_window_stub_for_property_panel())
    panel.lbl_editing_target = QLabel("")
    panel.lbl_editing_target.resize(220, 20)
    panel.lbl_editing_target.setFixedWidth(220)
    panel.lbl_editing_target_preview = QLabel("")
    panel.lbl_editing_target_preview.resize(220, 20)
    panel.lbl_editing_target_preview.setFixedWidth(220)

    target = SimpleNamespace(text="short summary")
    panel._update_editing_target_labels(target)

    _visual_assert(
        bool(panel.lbl_editing_target_preview.text()) and not panel.lbl_editing_target_preview.isHidden(),
        case_id="property_panel_summary_short",
        widget_state={
            "target_text": panel.lbl_editing_target.text(),
            "preview_text": panel.lbl_editing_target_preview.text(),
            "preview_hidden": panel.lbl_editing_target_preview.isHidden(),
        },
    )
    panel.deleteLater()


def test_visual_contract_property_panel_summary_long_elides(qapp) -> None:
    _ = qapp
    panel = PropertyPanel(main_window=_make_main_window_stub_for_property_panel())
    panel.lbl_editing_target = QLabel("")
    panel.lbl_editing_target.resize(84, 20)
    panel.lbl_editing_target.setFixedWidth(84)
    panel.lbl_editing_target_preview = QLabel("")
    panel.lbl_editing_target_preview.resize(84, 20)
    panel.lbl_editing_target_preview.setFixedWidth(84)

    target = SimpleNamespace(text=("LONG_" * 60))
    panel._update_editing_target_labels(target)

    _visual_assert(
        len(panel.lbl_editing_target_preview.text()) < len(panel.lbl_editing_target_preview.toolTip()),
        case_id="property_panel_summary_long",
        widget_state={
            "preview_text": panel.lbl_editing_target_preview.text(),
            "preview_tooltip": panel.lbl_editing_target_preview.toolTip(),
            "geometry": str(panel.lbl_editing_target_preview.geometry()),
        },
    )
    panel.deleteLater()


def test_visual_contract_dialog_only_textwindow_context_menu() -> None:
    window = _make_text_window()

    class DummyBuilder:
        last_instance = None

        def __init__(self, *_args, **_kwargs):
            self.submenus = []
            DummyBuilder.last_instance = self

        def add_connect_group_menu(self):
            return None

        def add_action(self, *_args, **_kwargs):
            return MagicMock()

        def add_submenu(self, text_key, **_kwargs):
            self.submenus.append(text_key)
            return MagicMock()

        def add_separator(self, **_kwargs):
            return None

        def exec(self, *_args, **_kwargs):
            return None

    with patch("windows.text_window.ContextMenuBuilder", DummyBuilder):
        with patch.object(type(window), "mapToGlobal", return_value=QPoint(0, 0)):
            window.show_context_menu(QPoint(0, 0))

    submenus = [] if DummyBuilder.last_instance is None else DummyBuilder.last_instance.submenus
    _visual_assert(
        "menu_text_editing_mode" not in submenus,
        case_id="dialog_only_routes_textwindow",
        widget_state={"submenus": submenus},
    )


def test_visual_contract_about_compact_hides_hints(qapp) -> None:
    _ = qapp
    tab = AboutTab(_make_main_window_stub_for_about_tab())
    tab.set_compact_mode(True)
    qapp.processEvents()

    _visual_assert(
        tab.hint_debounce.isHidden() and tab.hint_wheel.isHidden() and tab.hint_cache.isHidden(),
        case_id="density_about_compact",
        widget_state={
            "hint_debounce_hidden": tab.hint_debounce.isHidden(),
            "hint_wheel_hidden": tab.hint_wheel.isHidden(),
            "hint_cache_hidden": tab.hint_cache.isHidden(),
        },
    )
    tab.deleteLater()


def test_visual_contract_about_comfortable_restores_hints(qapp) -> None:
    _ = qapp
    tab = AboutTab(_make_main_window_stub_for_about_tab())
    tab.perf_group.toggle_button.setChecked(True)
    tab.set_compact_mode(True)
    qapp.processEvents()
    tab.set_compact_mode(False)
    qapp.processEvents()

    _visual_assert(
        (not tab.hint_debounce.isHidden()) and (not tab.hint_wheel.isHidden()) and (not tab.hint_cache.isHidden()),
        case_id="density_about_comfortable",
        widget_state={
            "hint_debounce_hidden": tab.hint_debounce.isHidden(),
            "hint_wheel_hidden": tab.hint_wheel.isHidden(),
            "hint_cache_hidden": tab.hint_cache.isHidden(),
        },
    )
    tab.deleteLater()
