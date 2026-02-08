# -*- coding: utf-8 -*-
"""TextWindow の追加テスト (Sprint 5).

toggle_text/background_visibility, wheelEvent, keyPressEvent,
_open_slider_dialog, _restore_render_debounce_ms, toggle/change 系,
add_text_window, clone_text, hide_all_other_windows, open_spacing_settings,
save_text_to_json, load_text_from_json をカバー。
"""

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, Qt

from models.window_config import TextWindowConfig


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
    obj.main_window.undo_stack = MagicMock()
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    obj._previous_text_opacity = 100
    obj._previous_background_opacity = 100
    obj._is_editing = False
    obj._render_debounce_ms = 25
    obj._wheel_render_relax_timer = MagicMock()
    obj.canvas_size = MagicMock()
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# toggle_text_visibility
# ============================================================
class TestToggleTextVisibility:
    def test_hides_when_opacity_positive(self):
        w = _make_text_window()
        w.config.text_opacity = 80
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_text_visibility()
        mock_prop.assert_called_once_with("text_opacity", 0, "update_text")
        assert w._previous_text_opacity == 80

    def test_restores_previous_opacity(self):
        w = _make_text_window()
        w.config.text_opacity = 0
        w._previous_text_opacity = 75
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_text_visibility()
        mock_prop.assert_called_once_with("text_opacity", 75, "update_text")

    def test_defaults_to_100_if_no_previous(self):
        w = _make_text_window()
        w.config.text_opacity = 0
        # Remove _previous_text_opacity to test fallback
        del w._previous_text_opacity
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_text_visibility()
        mock_prop.assert_called_once_with("text_opacity", 100, "update_text")


# ============================================================
# toggle_background_visibility
# ============================================================
class TestToggleBackgroundVisibility:
    def test_hides_when_opacity_positive(self):
        w = _make_text_window()
        w.config.background_opacity = 60
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_background_visibility()
        mock_prop.assert_called_once_with("background_opacity", 0, "update_text")
        assert w._previous_background_opacity == 60

    def test_restores_previous_opacity(self):
        w = _make_text_window()
        w.config.background_opacity = 0
        w._previous_background_opacity = 50
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_background_visibility()
        mock_prop.assert_called_once_with("background_opacity", 50, "update_text")


# ============================================================
# _restore_render_debounce_ms_after_wheel
# ============================================================
class TestRestoreRenderDebounce:
    def test_restores_to_25(self):
        w = _make_text_window()
        w._render_debounce_ms = 80
        w._restore_render_debounce_ms_after_wheel()
        assert w._render_debounce_ms == 25


# ============================================================
# wheelEvent
# ============================================================
class TestWheelEvent:
    def _make_event(self, angle_y=120):
        event = MagicMock()
        delta = MagicMock()
        delta.y.return_value = angle_y
        event.angleDelta.return_value = delta
        return event

    def test_editing_mode_skips(self):
        w = _make_text_window()
        w._is_editing = True
        w.config.font_size = 24
        event = self._make_event(120)
        w.wheelEvent(event)
        # Font size should not change
        assert w.config.font_size == 24

    def test_locked_skips(self):
        w = _make_text_window()
        w.config.is_locked = True
        w.config.font_size = 24
        event = self._make_event(120)
        w.wheelEvent(event)
        event.accept.assert_called()

    def test_scroll_up_decreases_size(self):
        w = _make_text_window()
        w.config.font_size = 24
        event = self._make_event(120)  # angle > 0 → decrease
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.update_text_debounced = MagicMock()
            w.wheelEvent(event)
        mock_prop.assert_called_once_with("font_size", 22, None)
        w.update_text_debounced.assert_called()

    def test_scroll_down_increases_size(self):
        w = _make_text_window()
        w.config.font_size = 24
        event = self._make_event(-120)  # angle < 0 → increase
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.update_text_debounced = MagicMock()
            w.wheelEvent(event)
        mock_prop.assert_called_once_with("font_size", 26, None)

    def test_clamps_minimum(self):
        w = _make_text_window()
        w.config.font_size = 5
        event = self._make_event(120)  # try to decrease below 5
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.update_text_debounced = MagicMock()
            w.wheelEvent(event)
        # 5 - 2 = 3, clamped to 5 → no change → set_undoable not called
        mock_prop.assert_not_called()

    def test_clamps_maximum(self):
        w = _make_text_window()
        w.config.font_size = 500
        event = self._make_event(-120)  # try to increase above 500
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.update_text_debounced = MagicMock()
            w.wheelEvent(event)
        # 500 + 2 = 502, clamped to 500 → no change → not called
        mock_prop.assert_not_called()

    def test_angle_zero_returns(self):
        w = _make_text_window()
        w.config.font_size = 24
        event = self._make_event(0)
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.update_text_debounced = MagicMock()
            w.wheelEvent(event)
        mock_prop.assert_not_called()


# ============================================================
# keyPressEvent
# ============================================================
class TestKeyPressEvent:
    def _make_event(self, key, modifiers=Qt.NoModifier):
        event = MagicMock()
        event.key.return_value = key
        event.modifiers.return_value = modifiers
        return event

    def test_delete_key_closes(self):
        w = _make_text_window()
        event = self._make_event(Qt.Key_Delete)
        with patch.object(type(w), "close") as mock_close:
            w.keyPressEvent(event)
        mock_close.assert_called_once()
        event.accept.assert_called()

    def test_h_key_hides(self):
        w = _make_text_window()
        w.hide_action = MagicMock()
        event = self._make_event(Qt.Key_H)
        w.keyPressEvent(event)
        w.hide_action.assert_called_once()
        event.accept.assert_called()

    def test_f_key_toggles_frontmost(self):
        w = _make_text_window()
        w.toggle_frontmost = MagicMock()
        event = self._make_event(Qt.Key_F)
        w.keyPressEvent(event)
        w.toggle_frontmost.assert_called_once()

    def test_locked_blocks_tab(self):
        w = _make_text_window()
        w.config.is_locked = True
        event = self._make_event(Qt.Key_Tab)
        w.keyPressEvent(event)
        event.accept.assert_called()
        # Should not call create_related_node
        w.main_window.window_manager.create_related_node.assert_not_called()

    def test_tab_creates_child_node(self):
        w = _make_text_window()
        w.config.is_locked = False
        event = self._make_event(Qt.Key_Tab)
        w.keyPressEvent(event)
        w.main_window.window_manager.create_related_node.assert_called_once_with(w, "child")

    def test_enter_creates_sibling_node(self):
        w = _make_text_window()
        w.config.is_locked = False
        event = self._make_event(Qt.Key_Return)
        w.keyPressEvent(event)
        w.main_window.window_manager.create_related_node.assert_called_once_with(w, "sibling")

    def test_arrow_key_navigates(self):
        w = _make_text_window()
        w.config.is_locked = False
        event = self._make_event(Qt.Key_Up)
        w.keyPressEvent(event)
        w.main_window.window_manager.navigate_selection.assert_called_once_with(w, Qt.Key_Up)

    def test_delete_works_even_when_locked(self):
        """Delete key should work even when locked (management key)."""
        w = _make_text_window()
        w.config.is_locked = True
        event = self._make_event(Qt.Key_Delete)
        with patch.object(type(w), "close") as mock_close:
            w.keyPressEvent(event)
        mock_close.assert_called_once()


# ============================================================
# toggle methods (additional ones not in Sprint 4)
# ============================================================
class TestAdditionalToggles:
    def test_toggle_shadow(self):
        w = _make_text_window()
        w.config.shadow_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_shadow()
        mock_prop.assert_called_once_with("shadow_enabled", True, "update_text")

    def test_toggle_text_gradient(self):
        w = _make_text_window()
        w.config.text_gradient_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_text_gradient()
        mock_prop.assert_called_once_with("text_gradient_enabled", True, "update_text")

    def test_toggle_background_gradient(self):
        w = _make_text_window()
        w.config.background_gradient_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_background_gradient()
        mock_prop.assert_called_once_with("background_gradient_enabled", True, "update_text")

    def test_toggle_background_outline(self):
        w = _make_text_window()
        w.config.background_outline_enabled = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_background_outline()
        mock_prop.assert_called_once_with("background_outline_enabled", True, "update_text")


# ============================================================
# change_font_color / change_background_color / change_outline_color
# ============================================================
class TestColorChanges:
    @patch("windows.text_window.QColorDialog")
    def test_change_font_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_font_color()
        mock_prop.assert_called_once_with("font_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_font_color_cancelled(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = False
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_font_color()
        mock_prop.assert_not_called()

    @patch("windows.text_window.QColorDialog")
    def test_change_background_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_background_color()
        mock_prop.assert_called_once_with("background_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_outline_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_outline_color()
        mock_prop.assert_called_once_with("outline_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_shadow_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_shadow_color()
        mock_prop.assert_called_once_with("shadow_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_second_outline_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_second_outline_color()
        mock_prop.assert_called_once_with("second_outline_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_third_outline_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_third_outline_color()
        mock_prop.assert_called_once_with("third_outline_color", color, "update_text")

    @patch("windows.text_window.QColorDialog")
    def test_change_background_outline_color_valid(self, mock_dlg):
        w = _make_text_window()
        color = MagicMock()
        color.isValid.return_value = True
        mock_dlg.getColor.return_value = color
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_background_outline_color()
        mock_prop.assert_called_once_with("background_outline_color", color, "update_text")


# ============================================================
# add_text_window
# ============================================================
class TestAddTextWindow:
    def test_adds_via_window_manager(self):
        w = _make_text_window()
        with patch.object(type(w), "pos", return_value=QPoint(100, 200)):
            w.add_text_window()
        w.main_window.window_manager.add_text_window.assert_called_once()

    def test_no_window_manager(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=["json_directory"])
        w.main_window.json_directory = "/tmp"
        # Should not crash
        with patch("windows.text_window.QMessageBox"):
            w.add_text_window()


# ============================================================
# clone_text
# ============================================================
class TestCloneText:
    def test_clones_via_window_manager(self):
        w = _make_text_window()
        w.clone_text()
        w.main_window.window_manager.clone_text_window.assert_called_once_with(w)

    def test_no_window_manager(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=["json_directory"])
        w.main_window.json_directory = "/tmp"
        with patch("windows.text_window.QMessageBox"):
            w.clone_text()


# ============================================================
# hide_all_other_windows / close_all_other_windows
# ============================================================
class TestOtherWindowActions:
    def test_hide_all_other(self):
        w = _make_text_window()
        w.hide_all_other_windows()
        w.main_window.window_manager.hide_all_other_text_windows.assert_called_once_with(w)

    def test_close_all_other(self):
        w = _make_text_window()
        w.close_all_other_windows()
        w.main_window.window_manager.close_all_other_text_windows.assert_called_once_with(w)

    def test_hide_all_no_wm(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=[])
        w.hide_all_other_windows()  # No crash

    def test_close_all_no_wm(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=[])
        w.close_all_other_windows()  # No crash


# ============================================================
# save_text_to_json / load_text_from_json
# ============================================================
class TestJsonDelegation:
    def test_save_delegates(self):
        w = _make_text_window()
        w.main_window.file_manager = MagicMock()
        w.save_text_to_json()
        w.main_window.file_manager.save_window_to_json.assert_called_once_with(w)

    def test_load_delegates(self):
        w = _make_text_window()
        w.main_window.file_manager = MagicMock()
        w.load_text_from_json()
        w.main_window.file_manager.load_window_from_json.assert_called_once_with(w)

    def test_save_no_file_manager(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=["json_directory"])
        w.main_window.json_directory = "/tmp"
        w.save_text_to_json()  # No crash

    def test_load_no_file_manager(self):
        w = _make_text_window()
        w.main_window = MagicMock(spec=["json_directory"])
        w.main_window.json_directory = "/tmp"
        w.load_text_from_json()  # No crash


# ============================================================
# _open_slider_dialog
# ============================================================
class TestOpenSliderDialog:
    @patch("ui.dialogs.PreviewCommitDialog")
    def test_creates_dialog(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.text_opacity = 80
        mock_dlg_cls.return_value.exec.return_value = None
        w._open_slider_dialog("Title", "Label", 0, 100, 80, "text_opacity", "update_text")
        mock_dlg_cls.assert_called_once()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_preview_callback_sets_value(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.text_opacity = 80
        w.update_text = MagicMock()
        mock_dlg_cls.return_value.exec.return_value = None

        w._open_slider_dialog("Title", "Label", 0, 100, 80, "text_opacity", "update_text")
        # Extract on_preview callback from constructor call
        call_kwargs = mock_dlg_cls.call_args[1]
        on_preview = call_kwargs["on_preview"]
        on_preview(50.0)
        assert w.config.text_opacity == 50

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_commit_callback_calls_set_undoable(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.text_opacity = 80
        mock_dlg_cls.return_value.exec.return_value = None

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w._open_slider_dialog("Title", "Label", 0, 100, 80, "text_opacity", "update_text")
            call_kwargs = mock_dlg_cls.call_args[1]
            on_commit = call_kwargs["on_commit"]
            on_commit(50.0)
        mock_prop.assert_called_once_with("text_opacity", 50, "update_text")

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_commit_no_change_skips_undo(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.text_opacity = 80
        w.update_text = MagicMock()
        mock_dlg_cls.return_value.exec.return_value = None

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w._open_slider_dialog("Title", "Label", 0, 100, 80, "text_opacity", "update_text")
            call_kwargs = mock_dlg_cls.call_args[1]
            on_commit = call_kwargs["on_commit"]
            on_commit(80.0)  # Same value → no undo
        mock_prop.assert_not_called()


# ============================================================
# open_spacing_settings
# ============================================================
class TestOpenSpacingSettings:
    @patch("windows.text_window.TextSpacingDialog")
    def test_horizontal_mode(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.is_vertical = False
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 1  # QDialog.Accepted
        mock_dlg.get_values_dict.return_value = {"char_spacing_h": 0.1, "line_spacing_h": 0.2}
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.open_spacing_settings()
        assert mock_prop.call_count == 2
        # Last key should have update_text
        mock_prop.assert_any_call("line_spacing_h", 0.2, "update_text")

    @patch("windows.text_window.TextSpacingDialog")
    def test_vertical_mode(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.is_vertical = True
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 1
        mock_dlg.get_values_dict.return_value = {"char_spacing_v": 0.1}
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.open_spacing_settings()
        mock_prop.assert_called_once_with("char_spacing_v", 0.1, "update_text")

    @patch("windows.text_window.TextSpacingDialog")
    def test_cancelled_no_change(self, mock_dlg_cls):
        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 0  # Rejected
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.open_spacing_settings()
        mock_prop.assert_not_called()

    @patch("windows.text_window.TextSpacingDialog")
    def test_uses_undo_macro(self, mock_dlg_cls):
        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 1
        mock_dlg.get_values_dict.return_value = {"a": 1, "b": 2}
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property"):
            w.open_spacing_settings()
        w.main_window.undo_stack.beginMacro.assert_called_once_with("Change Spacing")
        w.main_window.undo_stack.endMacro.assert_called_once()


# ============================================================
# set_shadow_offsets
# ============================================================
class TestSetShadowOffsets:
    @patch("windows.text_window.ShadowOffsetDialog")
    def test_accepted_with_change(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.shadow_offset_x = 0.1
        w.config.shadow_offset_y = 0.2
        w.update_text = MagicMock()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 1  # Accepted
        mock_dlg.get_offsets.return_value = (0.3, 0.4)
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_shadow_offsets()
        assert mock_prop.call_count == 2
        mock_prop.assert_any_call("shadow_offset_x", 0.3, None)
        mock_prop.assert_any_call("shadow_offset_y", 0.4, "update_text")
        w.main_window.undo_stack.beginMacro.assert_called_with("Set Shadow Offsets")

    @patch("windows.text_window.ShadowOffsetDialog")
    def test_accepted_no_change_skips(self, mock_dlg_cls):
        w = _make_text_window()
        w.config.shadow_offset_x = 0.1
        w.config.shadow_offset_y = 0.2
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 1
        mock_dlg.get_offsets.return_value = (0.1, 0.2)  # Same
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_shadow_offsets()
        mock_prop.assert_not_called()


# ============================================================
# show_property_panel
# ============================================================
class TestShowPropertyPanel:
    def test_emits_signal(self):
        w = _make_text_window()
        w.sig_request_property_panel = MagicMock()
        w.show_property_panel()
        w.sig_request_property_panel.emit.assert_called_once_with(w)


# ============================================================
# change_font (QFontDialog)
# ============================================================
class TestChangeFont:
    @patch("windows.text_window.QFontDialog")
    def test_accepted_applies_font(self, mock_dlg_cls):
        from PySide6.QtGui import QFont

        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = mock_dlg_cls.Accepted
        selected_font = QFont("Courier", 16)
        mock_dlg.selectedFont.return_value = selected_font
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_font()
        mock_prop.assert_any_call("font_family", "Courier", None)
        mock_prop.assert_any_call("font_size", 16, None)

    @patch("windows.text_window.QFontDialog")
    def test_cancelled_no_change(self, mock_dlg_cls):
        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = 0  # Rejected
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.change_font()
        mock_prop.assert_not_called()


# ============================================================
# set_horizontal_margin_ratio / set_vertical_margin_ratio
# ============================================================
class TestMarginRatioDialogs:
    @patch("windows.text_window.MarginRatioDialog")
    def test_set_h_margin_accepted(self, mock_dlg_cls):
        from PySide6.QtWidgets import QDialog

        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.Accepted
        mock_dlg.get_value.return_value = 0.5
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_horizontal_margin_ratio()
        mock_prop.assert_called_once_with("horizontal_margin_ratio", 0.5, "update_text")

    @patch("windows.text_window.MarginRatioDialog")
    def test_set_v_margin_accepted(self, mock_dlg_cls):
        from PySide6.QtWidgets import QDialog

        w = _make_text_window()
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.Accepted
        mock_dlg.get_value.return_value = 0.3
        mock_dlg_cls.return_value = mock_dlg

        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.set_vertical_margin_ratio()
        mock_prop.assert_called_once_with("vertical_margin_ratio", 0.3, "update_text")
