# -*- coding: utf-8 -*-
"""TextWindow の計算・状態ロジックテスト (Sprint 4).

load_text_defaults, propagate_scale_to_children,
set_undoable_property (font_size debounce), toggle 系をカバー。
"""

from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from models.window_config import TextWindowConfig
from utils.due_date import classify_due
from utils.translator import tr


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------
def _make_text_window(**overrides):
    """TextWindow を __init__ なしで作成。"""
    from windows.text_window import TextWindow

    with patch.object(TextWindow, "__init__", lambda self, *a, **kw: None):
        obj = TextWindow.__new__(TextWindow)
    obj.config = TextWindowConfig()
    obj.main_window = MagicMock()
    obj.main_window.json_directory = "/tmp/ftiv"
    obj.main_window.settings_manager = MagicMock()
    obj.main_window.settings_manager.load_text_archetype.return_value = None
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    obj._overlay_meta_tooltip_append = ""
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# load_text_defaults
# ============================================================
class TestLoadTextDefaults:
    @patch("os.path.exists", return_value=False)
    def test_basic_defaults_from_config(self, _):
        w = _make_text_window()
        defaults = w.load_text_defaults()
        assert isinstance(defaults, dict)
        # Must contain legacy compatibility keys
        assert "h_margin" in defaults
        assert "v_margin" in defaults

    @patch("os.path.exists", return_value=False)
    def test_returns_config_model_dump(self, _):
        w = _make_text_window()
        defaults = w.load_text_defaults()
        # Should contain standard TextWindowConfig fields
        assert "font_size" in defaults
        assert "font" in defaults

    @patch("builtins.open", mock_open(read_data='{"font_size": 48}'))
    @patch("os.path.exists", return_value=True)
    def test_loads_text_defaults_json(self, _):
        w = _make_text_window()
        defaults = w.load_text_defaults()
        assert defaults["font_size"] == 48

    @patch("builtins.open", mock_open(read_data='{"custom_key": "val"}'))
    @patch("os.path.exists", return_value=True)
    def test_loads_vertical_defaults_json(self, _):
        w = _make_text_window()
        defaults = w.load_text_defaults()
        # Should merge both files (horizontal + vertical)
        assert "custom_key" in defaults

    @patch("os.path.exists", return_value=False)
    def test_archetype_overrides(self, _):
        w = _make_text_window()
        w.main_window.settings_manager.load_text_archetype.return_value = {
            "font_size": 100,
            "font": "Gothic",
        }
        defaults = w.load_text_defaults()
        assert defaults["font_size"] == 100
        assert defaults["font"] == "Gothic"

    @patch("os.path.exists", return_value=False)
    def test_no_settings_manager(self, _):
        w = _make_text_window()
        w.main_window = MagicMock(spec=["json_directory"])
        w.main_window.json_directory = "/tmp"
        defaults = w.load_text_defaults()
        assert isinstance(defaults, dict)

    @patch("os.path.exists", return_value=True)
    def test_corrupt_json_fallback(self, _):
        w = _make_text_window()
        with patch("builtins.open", mock_open(read_data="NOT JSON")):
            defaults = w.load_text_defaults()
        assert isinstance(defaults, dict)


# ============================================================
# propagate_scale_to_children
# ============================================================
class TestPropagateScaleToChildren:
    def test_no_children_noop(self):
        w = _make_text_window()
        w.child_windows = []
        w.propagate_scale_to_children(2.0)  # No crash

    def test_text_child_not_scaled(self):
        w = _make_text_window()
        child = MagicMock()
        child.font_size = 24.0
        w.child_windows = [child]
        w.propagate_scale_to_children(2.0)
        assert child.font_size == 24.0
        child.update_text.assert_not_called()
        child.move.assert_not_called()

    def test_image_child_not_scaled(self):
        w = _make_text_window()
        child = MagicMock(
            spec=["scale_factor", "update_image", "geometry", "move", "width", "height", "propagate_scale_to_children"]
        )
        child.scale_factor = 1.0
        w.child_windows = [child]
        w.propagate_scale_to_children(2.0)
        assert child.scale_factor == 1.0
        child.update_image.assert_not_called()


# ============================================================
# set_undoable_property (font_size debounce)
# ============================================================
class TestSetUndoableProperty:
    def test_font_size_uses_debounce(self):
        w = _make_text_window()
        w.update_text_debounced = MagicMock()
        with patch("windows.base_window.BaseOverlayWindow.set_undoable_property"):
            with patch("windows.base_window.shiboken6") as mock_shib:
                mock_shib.isValid.return_value = True
                w.set_undoable_property("font_size", 48, "update_text")
        w.update_text_debounced.assert_called_once()

    def test_non_font_size_delegates_to_parent(self):
        w = _make_text_window()
        with patch("windows.base_window.BaseOverlayWindow.set_undoable_property") as mock_parent:
            with patch("windows.base_window.shiboken6") as mock_shib:
                mock_shib.isValid.return_value = True
                w.set_undoable_property("outline_enabled", True, "update_text")
        mock_parent.assert_called_with("outline_enabled", True, "update_text")


# ============================================================
# toggle methods
# ============================================================
class TestToggleMethods:
    def test_toggle_outline(self):
        w = _make_text_window()
        w.config.outline_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_outline()
        mock_prop.assert_called_once_with("outline_enabled", True, "update_text")

    def test_toggle_second_outline(self):
        w = _make_text_window()
        w.config.second_outline_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_second_outline()
        mock_prop.assert_called_once_with("second_outline_enabled", True, "update_text")

    def test_toggle_third_outline(self):
        w = _make_text_window()
        w.config.third_outline_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_third_outline()
        mock_prop.assert_called_once_with("third_outline_enabled", True, "update_text")

    def test_toggle_vertical_text(self):
        w = _make_text_window()
        w.config.is_vertical = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_vertical_text()
        mock_prop.assert_called_once_with("is_vertical", True, "update_text")


# ============================================================
# task mode helpers
# ============================================================
class TestTaskModeHelpers:
    def test_set_content_mode_uses_undoable_property(self):
        w = _make_text_window()
        w.config.content_mode = "note"
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_content_mode("task")
        mock_prop.assert_any_call("content_mode", "task", "update_text")

    def test_toggle_task_line_by_index(self):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.config.text = "one\ntwo"
        w.config.task_states = [False, True]
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w._toggle_task_line_by_index(1)
        mock_prop.assert_called_once_with("task_states", [False, False], "update_text")

    @patch("windows.text_window.QMessageBox.information")
    def test_toggle_vertical_text_blocked_in_task_mode(self, mock_info):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.toggle_vertical_text()
        mock_info.assert_called_once()

    def test_iter_task_items_returns_refs(self):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.config.text = "one\ntwo"
        w.config.task_states = [True, False]

        items = w.iter_task_items()
        assert len(items) == 2
        assert items[0].line_index == 0
        assert items[0].text == "one"
        assert items[0].done is True
        assert items[1].line_index == 1
        assert items[1].done is False

    def test_set_task_line_state_updates_states(self):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.config.text = "one\ntwo"
        w.config.task_states = [False, False]
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_task_line_state(0, True)

        mock_prop.assert_called_once_with("task_states", [True, False], "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_title_and_tags_normalizes_tags(self):
        w = _make_text_window()
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_title_and_tags("  Hello  ", ["A", "a", "", "B "])

        mock_prop.assert_any_call("title", "Hello", "update_text")
        mock_prop.assert_any_call("tags", ["A", "B"], "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_tags_normalizes_and_updates(self):
        w = _make_text_window()
        w.config.tags = ["One"]
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_tags([" one ", "Two", "two", ""])

        mock_prop.assert_called_once_with("tags", ["one", "Two"], "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_tags_no_change_is_noop(self):
        w = _make_text_window()
        w.config.tags = ["One", "Two"]
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_tags(["One", "Two", "one"])

        mock_prop.assert_not_called()
        w._touch_updated_at.assert_not_called()

    def test_set_due_at_normalizes_date(self):
        w = _make_text_window()
        w.config.due_at = ""
        w.config.due_time = ""
        w.config.due_timezone = ""
        w.config.due_precision = "date"
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_due_at("2026-03-01")

        mock_prop.assert_any_call("due_at", "2026-03-01T00:00:00", "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_due_at_invalid_is_noop(self):
        w = _make_text_window()
        w.config.due_at = ""
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_due_at("2026/03/01")

        mock_prop.assert_not_called()
        w._touch_updated_at.assert_not_called()

    def test_clear_due_at(self):
        w = _make_text_window()
        w.config.due_at = "2026-03-01T00:00:00"
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.clear_due_at()

        mock_prop.assert_any_call("due_at", "", "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_due_at_clears_datetime_detail_fields(self):
        w = _make_text_window()
        w.config.due_at = "2026-03-01T00:00:00"
        w.config.due_time = "09:30"
        w.config.due_timezone = "Asia/Tokyo"
        w.config.due_precision = "datetime"
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_due_at("2026-03-02")

        mock_prop.assert_any_call("due_at", "2026-03-02T00:00:00", "update_text")
        mock_prop.assert_any_call("due_precision", "date", None)
        mock_prop.assert_any_call("due_time", "", None)
        mock_prop.assert_any_call("due_timezone", "", None)
        w._touch_updated_at.assert_called_once()

    def test_clear_due_at_clears_datetime_detail_fields(self):
        w = _make_text_window()
        w.config.due_at = "2026-03-01T00:00:00"
        w.config.due_time = "09:30"
        w.config.due_timezone = "Asia/Tokyo"
        w.config.due_precision = "datetime"
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.clear_due_at()

        mock_prop.assert_any_call("due_at", "", "update_text")
        mock_prop.assert_any_call("due_precision", "date", None)
        mock_prop.assert_any_call("due_time", "", None)
        mock_prop.assert_any_call("due_timezone", "", None)
        w._touch_updated_at.assert_called_once()

    def test_classify_due_datetime_uses_time_threshold(self):
        state = classify_due(
            "2026-03-01T00:00:00",
            due_time="09:30",
            due_precision="datetime",
            now=datetime(2026, 3, 1, 10, 0),
        )
        assert state == "overdue"

    def test_classify_due_datetime_today_when_time_not_passed(self):
        state = classify_due(
            "2026-03-01T00:00:00",
            due_time="23:00",
            due_precision="datetime",
            now=datetime(2026, 3, 1, 10, 0),
        )
        assert state == "today"

    def test_bulk_set_task_done_updates_selected_indices(self):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.config.text = "one\ntwo\nthree"
        w.config.task_states = [False, True, False]
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.bulk_set_task_done([0, 2], True)

        mock_prop.assert_called_once_with("task_states", [True, True, True], "update_text")
        w._touch_updated_at.assert_called_once()

    def test_set_title_and_tags_no_change_is_noop(self):
        w = _make_text_window()
        w.config.title = "Title"
        w.config.tags = ["a"]
        w.main_window.undo_stack = MagicMock()
        w._touch_updated_at = MagicMock()

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_title_and_tags("Title", ["a"])

        mock_prop.assert_not_called()
        w._touch_updated_at.assert_not_called()
        w.main_window.undo_stack.beginMacro.assert_not_called()


class TestSelectionSync:
    def test_set_selected_triggers_update_text_only_on_change(self):
        w = _make_text_window()
        w.is_selected = False
        w.update_text = MagicMock()

        with patch("windows.base_window.BaseOverlayWindow.set_selected", autospec=True) as mock_base_set_selected:
            mock_base_set_selected.side_effect = lambda self_obj, selected: setattr(self_obj, "is_selected", selected)
            w.set_selected(True)
            w.set_selected(True)

        w.update_text.assert_called_once()


class TestMetaTooltip:
    def test_build_overlay_meta_tooltip_lines_quiet_note_when_empty(self):
        w = _make_text_window()
        w.config.content_mode = "note"
        w.config.title = ""
        w.config.tags = []
        w.config.due_at = ""
        w.config.is_starred = False
        w.config.is_archived = False

        lines = w._build_overlay_meta_tooltip_lines()
        assert lines == []

    def test_build_overlay_meta_tooltip_lines_task_includes_progress(self):
        w = _make_text_window()
        w.config.content_mode = "task"
        w.config.text = "a\nb\nc"
        w.config.task_states = [True, False, True]

        lines = w._build_overlay_meta_tooltip_lines()
        assert w.get_task_progress() == (2, 3)
        expected = str(tr("label_task_progress_fmt")).format(done=2, total=3)
        assert expected in lines

    def test_refresh_overlay_meta_tooltip_appends_lines(self):
        w = _make_text_window()
        w._overlay_meta_tooltip_append = ""
        w.toolTip = MagicMock(return_value="")
        w.setToolTip = MagicMock()
        w._build_overlay_meta_tooltip_lines = MagicMock(return_value=["0/1", "#alpha"])

        w._refresh_overlay_meta_tooltip()

        w.setToolTip.assert_called_once_with("0/1\n#alpha")
        assert w._overlay_meta_tooltip_append == "0/1\n#alpha"

    def test_refresh_overlay_meta_tooltip_removes_previous_append(self):
        w = _make_text_window()
        w._overlay_meta_tooltip_append = "\n\n0/1"
        w.toolTip = MagicMock(return_value="Base\n\n0/1")
        w.setToolTip = MagicMock()
        w._build_overlay_meta_tooltip_lines = MagicMock(return_value=[])

        w._refresh_overlay_meta_tooltip()

        w.setToolTip.assert_called_once_with("Base")
        assert w._overlay_meta_tooltip_append == ""
