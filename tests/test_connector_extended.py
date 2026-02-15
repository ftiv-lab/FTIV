# -*- coding: utf-8 -*-
"""ConnectorLine / ConnectorLabel の追加テスト (Sprint 5).

delete_line, toggle_label_visibility, change_color, open_width/opacity_dialog,
ConnectorLabel の set_undoable_property, _apply_label_layout_change,
_toggle_label_visibility, _clear_label_text, _change_label_font/color をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont

from models.enums import ArrowStyle
from models.window_config import TextWindowConfig


# ------------------------------------------------------------------
# ヘルパー: ConnectorLine
# ------------------------------------------------------------------
def _make_connector_line(**overrides):
    """ConnectorLine を __init__ なしで作成。"""
    from windows.connector import ConnectorLine

    with patch.object(ConnectorLine, "__init__", lambda self, *a, **kw: None):
        obj = ConnectorLine.__new__(ConnectorLine)
    obj.start_window = MagicMock()
    obj.end_window = MagicMock()
    obj.line_color = QColor(100, 200, 255, 180)
    obj.line_width = 2
    obj.pen_style = MagicMock()
    obj.arrow_style = ArrowStyle.NONE
    obj.arrow_size = 15
    obj.is_selected = False
    obj.label_window = None
    obj.main_window = MagicMock()
    obj._label_forced_hidden = False
    obj._deleted = False
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


# ------------------------------------------------------------------
# ヘルパー: ConnectorLabel
# ------------------------------------------------------------------
def _make_connector_label(**overrides):
    """ConnectorLabel を __init__ なしで作成。"""
    from windows.connector import ConnectorLabel

    with patch.object(ConnectorLabel, "__init__", lambda self, *a, **kw: None):
        obj = ConnectorLabel.__new__(ConnectorLabel)
    obj.config = TextWindowConfig()
    obj.config.text = "Label"
    obj.main_window = MagicMock()
    obj.main_window.undo_stack = MagicMock()
    obj.connector = MagicMock()
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# ConnectorLine: delete_line
# ============================================================
class TestDeleteLine:
    def test_delegates_to_window_manager(self):
        conn = _make_connector_line()
        conn.delete_line()
        conn.main_window.window_manager.delete_connector.assert_called_once_with(conn)

    def test_fallback_when_no_window_manager(self):
        conn = _make_connector_line()
        conn.main_window = MagicMock(spec=[])
        conn.sig_connector_deleted = MagicMock()
        with patch.object(type(conn), "close"):
            conn.delete_line()
        conn.sig_connector_deleted.emit.assert_called_once_with(conn)

    def test_no_main_window(self):
        conn = _make_connector_line()
        conn.main_window = None
        conn.sig_connector_deleted = MagicMock()
        with patch.object(type(conn), "close"):
            conn.delete_line()
        conn.sig_connector_deleted.emit.assert_called_once_with(conn)


# ============================================================
# ConnectorLine: toggle_label_visibility
# ============================================================
class TestToggleLabelVisibility:
    def test_no_label_noop(self):
        conn = _make_connector_line()
        conn.label_window = None
        conn.toggle_label_visibility()  # No crash

    def test_empty_text_opens_edit(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = ""
        lw.isHidden.return_value = True
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.toggle_label_visibility()
        lw.show.assert_called()
        lw.edit_text_realtime.assert_called()

    def test_text_present_hidden_shows(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = "Hello"
        lw.isHidden.return_value = True
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.toggle_label_visibility()
        lw.show.assert_called()
        lw.raise_.assert_called()

    def test_text_present_visible_hides(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = "Hello"
        lw.isHidden.return_value = False
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.toggle_label_visibility()
        lw.hide_action.assert_called()


# ============================================================
# ConnectorLine: change_color
# ============================================================
class TestChangeColor:
    @patch("windows.connector.QColorDialog")
    def test_valid_color_sets(self, mock_dlg):
        conn = _make_connector_line()
        color = QColor(255, 0, 0, 255)
        mock_dlg.getColor.return_value = color
        mock_dlg.ShowAlphaChannel = 1
        with patch.object(type(conn), "update"):
            conn.change_color()
        assert conn.line_color == color

    @patch("windows.connector.QColorDialog")
    def test_invalid_color_noop(self, mock_dlg):
        conn = _make_connector_line()
        invalid = MagicMock()
        invalid.isValid.return_value = False
        mock_dlg.getColor.return_value = invalid
        mock_dlg.ShowAlphaChannel = 1
        original = QColor(conn.line_color)
        conn.change_color()
        assert conn.line_color == original


# ============================================================
# ConnectorLine: open_width_dialog
# ============================================================
class TestOpenWidthDialog:
    @patch("windows.connector.SliderSpinDialog")
    def test_creates_dialog(self, mock_dlg_cls):
        conn = _make_connector_line()
        conn.line_width = 5
        mock_dlg_cls.return_value.exec.return_value = None
        conn.open_width_dialog()
        mock_dlg_cls.assert_called_once()

    @patch("windows.connector.SliderSpinDialog")
    def test_callback_sets_width(self, mock_dlg_cls):
        conn = _make_connector_line()
        conn.line_width = 5
        mock_dlg_cls.return_value.exec.return_value = None
        with patch.object(type(conn), "update_position"):
            conn.open_width_dialog()
            # Extract callback
            call_args = mock_dlg_cls.call_args[0]
            cb = call_args[5]  # 6th positional arg
            cb(20)
        assert conn.line_width == 20


# ============================================================
# ConnectorLine: open_opacity_dialog
# ============================================================
class TestOpenOpacityDialog:
    @patch("windows.connector.SliderSpinDialog")
    def test_creates_dialog(self, mock_dlg_cls):
        conn = _make_connector_line()
        mock_dlg_cls.return_value.exec.return_value = None
        with patch.object(type(conn), "update"):
            conn.open_opacity_dialog()
        mock_dlg_cls.assert_called_once()

    @patch("windows.connector.SliderSpinDialog")
    def test_callback_sets_alpha(self, mock_dlg_cls):
        conn = _make_connector_line()
        conn.line_color = QColor(255, 0, 0, 255)
        mock_dlg_cls.return_value.exec.return_value = None
        with patch.object(type(conn), "update"):
            conn.open_opacity_dialog()
            call_args = mock_dlg_cls.call_args[0]
            cb = call_args[5]
            cb(50)  # 50% → alpha 127
        assert conn.line_color.alpha() == 127

    @patch("windows.connector.SliderSpinDialog")
    def test_initial_value_from_current_alpha(self, mock_dlg_cls):
        conn = _make_connector_line()
        conn.line_color = QColor(0, 0, 0, 128)  # 128/255*100 ≈ 50
        mock_dlg_cls.return_value.exec.return_value = None
        with patch.object(type(conn), "update"):
            conn.open_opacity_dialog()
        call_args = mock_dlg_cls.call_args[0]
        initial = call_args[4]  # 5th positional = current
        assert initial == 50


# ============================================================
# ConnectorLabel: set_undoable_property
# ============================================================
class TestLabelSetUndoableProperty:
    def test_font_size_uses_debounce(self):
        label = _make_connector_label()
        label.update_text_debounced = MagicMock()
        with patch("windows.base_window.BaseOverlayWindow.set_undoable_property"):
            with patch("windows.base_window.shiboken6") as mock_shib:
                mock_shib.isValid.return_value = True
                label.set_undoable_property("font_size", 48, "update_text")
        label.update_text_debounced.assert_called_once()

    def test_non_font_size_delegates(self):
        label = _make_connector_label()
        with patch("windows.base_window.BaseOverlayWindow.set_undoable_property") as mock_parent:
            with patch("windows.base_window.shiboken6") as mock_shib:
                mock_shib.isValid.return_value = True
                label.set_undoable_property("outline_enabled", True, "update_text")
        mock_parent.assert_called_with("outline_enabled", True, "update_text")


# ============================================================
# ConnectorLabel: _apply_label_layout_change
# ============================================================
class TestApplyLabelLayoutChange:
    def test_wraps_in_undo_macro(self):
        label = _make_connector_label()
        fn = MagicMock()
        label._apply_label_layout_change(fn, "Test Macro")
        label.main_window.undo_stack.beginMacro.assert_called_once_with("Test Macro")
        label.main_window.undo_stack.endMacro.assert_called_once()
        fn.assert_called_once()

    def test_no_undo_stack(self):
        label = _make_connector_label()
        label.main_window = MagicMock(spec=[])
        fn = MagicMock()
        label._apply_label_layout_change(fn, "Test")
        fn.assert_called_once()

    def test_endmacro_called_even_on_error(self):
        label = _make_connector_label()
        fn = MagicMock(side_effect=ValueError("test error"))
        with pytest.raises(ValueError):
            label._apply_label_layout_change(fn, "Test Macro")
        label.main_window.undo_stack.endMacro.assert_called_once()


# ============================================================
# ConnectorLabel: _toggle_label_visibility
# ============================================================
class TestLabelToggleVisibility:
    def test_text_present_clears_and_hides(self):
        label = _make_connector_label()
        label.config.text = "some text"
        label.hide_action = MagicMock()
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            with patch.object(type(label), "set_undoable_property"):
                label._toggle_label_visibility()
        mock_apply.assert_called_once()

    def test_empty_text_opens_edit(self):
        label = _make_connector_label()
        label.config.text = ""
        label.edit_text_realtime = MagicMock()
        with patch.object(type(label), "isHidden", return_value=True):
            with patch.object(type(label), "show"):
                label._toggle_label_visibility()
        label.edit_text_realtime.assert_called_once()


# ============================================================
# ConnectorLabel: mouseDoubleClickEvent (Dialog-only)
# ============================================================
class TestConnectorLabelDoubleClick:
    def test_left_double_click_uses_dialog_edit(self):
        label = _make_connector_label()
        label.edit_text_realtime = MagicMock()
        event = MagicMock()
        event.button.return_value = Qt.MouseButton.LeftButton

        label.mouseDoubleClickEvent(event)

        label.edit_text_realtime.assert_called_once()
        event.accept.assert_called_once()


# ============================================================
# ConnectorLabel: _clear_label_text
# ============================================================
class TestClearLabelText:
    def test_clears_and_hides(self):
        label = _make_connector_label()
        label.config.text = "something"
        label.hide_action = MagicMock()
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._clear_label_text()
        mock_apply.assert_called_once()
        label.hide_action.assert_called()

    def test_hide_fallback(self):
        label = _make_connector_label()
        label.config.text = "something"
        # No hide_action, should use hide() fallback
        with patch.object(type(label), "_apply_label_layout_change"):
            with patch.object(type(label), "hide"):
                # Remove hide_action
                label.hide_action = MagicMock(side_effect=Exception("nope"))
                label._clear_label_text()


# ============================================================
# ConnectorLabel: _change_label_font
# ============================================================
class TestChangeLabelFont:
    @patch("windows.connector.choose_font")
    def test_accepted_applies(self, mock_choose_font):
        label = _make_connector_label()
        mock_choose_font.return_value = QFont("Courier", 16)
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_font()
        mock_apply.assert_called_once()

    @patch("windows.connector.choose_font")
    def test_cancelled_noop(self, mock_choose_font):
        label = _make_connector_label()
        mock_choose_font.return_value = None
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_font()
        mock_apply.assert_not_called()


# ============================================================
# ConnectorLabel: _change_label_font_color
# ============================================================
class TestChangeLabelFontColor:
    @patch("windows.connector.QColorDialog")
    def test_valid_color_applies(self, mock_dlg):
        label = _make_connector_label()
        color = QColor(255, 0, 0, 255)
        mock_dlg.getColor.return_value = color
        mock_dlg.ShowAlphaChannel = 1
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_font_color()
        mock_apply.assert_called_once()

    @patch("windows.connector.QColorDialog")
    def test_invalid_color_noop(self, mock_dlg):
        label = _make_connector_label()
        invalid = MagicMock()
        invalid.isValid.return_value = False
        mock_dlg.getColor.return_value = invalid
        mock_dlg.ShowAlphaChannel = 1
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_font_color()
        mock_apply.assert_not_called()


# ============================================================
# ConnectorLabel: _change_label_bg_color
# ============================================================
class TestChangeLabelBgColor:
    @patch("windows.connector.QColorDialog")
    def test_valid_color_applies(self, mock_dlg):
        label = _make_connector_label()
        color = QColor(0, 255, 0, 128)
        mock_dlg.getColor.return_value = color
        mock_dlg.ShowAlphaChannel = 1
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_bg_color()
        mock_apply.assert_called_once()

    @patch("windows.connector.QColorDialog")
    def test_invalid_noop(self, mock_dlg):
        label = _make_connector_label()
        invalid = MagicMock()
        invalid.isValid.return_value = False
        mock_dlg.getColor.return_value = invalid
        mock_dlg.ShowAlphaChannel = 1
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_bg_color()
        mock_apply.assert_not_called()


# ============================================================
# ConnectorLabel: _change_label_bg_opacity
# ============================================================
class TestChangeLabelBgOpacity:
    @patch("windows.connector.QInputDialog")
    def test_accepted_applies(self, mock_dlg):
        label = _make_connector_label()
        label.config.background_opacity = 80
        mock_dlg.getInt.return_value = (50, True)
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_bg_opacity()
        mock_apply.assert_called_once()

    @patch("windows.connector.QInputDialog")
    def test_cancelled_noop(self, mock_dlg):
        label = _make_connector_label()
        mock_dlg.getInt.return_value = (50, False)
        with patch.object(type(label), "_apply_label_layout_change") as mock_apply:
            label._change_label_bg_opacity()
        mock_apply.assert_not_called()


# ============================================================
# ConnectorLabel: _open_parent_line_menu
# ============================================================
class TestOpenParentLineMenu:
    def test_no_connector_noop(self):
        label = _make_connector_label()
        label.connector = None
        label._open_parent_line_menu()  # No crash

    def test_calls_connector_menu(self):
        label = _make_connector_label()
        with patch.object(type(label), "mapToGlobal", return_value=QPoint(100, 200)):
            label._open_parent_line_menu()
        label.connector.show_context_menu.assert_called_once()
