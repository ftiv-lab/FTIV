# -*- coding: utf-8 -*-
"""ConnectorActions の追加テスト (Sprint 5).

open_width_dialog_selected, open_opacity_dialog_selected,
bulk_open_width_dialog, bulk_open_opacity_dialog をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QColor

from ui.controllers.connector_actions import ConnectorActions


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.last_selected_connector = None
    mw.last_selected_window = None
    mw.window_manager = MagicMock()
    mw.window_manager.connectors = []
    mw.connections_tab = MagicMock()
    mw.undo_stack = MagicMock()
    return mw


@pytest.fixture
def ca(mock_mw):
    return ConnectorActions(mock_mw)


# ============================================================
# open_width_dialog_selected
# ============================================================
class TestOpenWidthDialogSelected:
    def test_no_line_noop(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        mock_mw.last_selected_window = None
        ca.open_width_dialog_selected()  # No crash

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_creates_dialog(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_width = 5
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None
        ca.open_width_dialog_selected()
        mock_dlg_cls.assert_called_once()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_preview_sets_width(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_width = 5
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_width_dialog_selected()
        # Extract on_preview from positional args
        call_args = mock_dlg_cls.call_args[0]
        on_preview = call_args[5]  # 6th arg
        on_preview(20.0)
        assert line.line_width == 20
        line.update_position.assert_called()

    @patch("ui.dialogs.PreviewCommitDialog")
    @patch("utils.commands.PropertyChangeCommand")
    def test_commit_pushes_undo(self, mock_cmd, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_width = 5
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_width_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_commit = call_args[6]  # 7th arg
        on_commit(20.0)
        mock_mw.undo_stack.beginMacro.assert_called_with("Change Connector Width")
        mock_mw.undo_stack.push.assert_called_once()
        mock_mw.undo_stack.endMacro.assert_called()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_commit_same_value_noop(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_width = 5
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_width_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_commit = call_args[6]
        on_commit(5.0)  # Same value
        mock_mw.undo_stack.push.assert_not_called()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_preview_fallback_to_update(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock(spec=["line_width", "update"])
        line.line_width = 5
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_width_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_preview = call_args[5]
        on_preview(10.0)
        line.update.assert_called()


# ============================================================
# open_opacity_dialog_selected
# ============================================================
class TestOpenOpacityDialogSelected:
    def test_no_line_noop(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        ca.open_opacity_dialog_selected()

    def test_no_color_noop(self, ca, mock_mw):
        line = MagicMock()
        line.line_color = None
        mock_mw.last_selected_connector = line
        ca.open_opacity_dialog_selected()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_creates_dialog_with_alpha_pct(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_color = QColor(255, 0, 0, 128)  # ~50%
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_opacity_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        initial_pct = call_args[4]  # old_pct
        assert initial_pct == 50

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_preview_applies_alpha(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_color = QColor(255, 0, 0, 255)
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_opacity_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_preview = call_args[5]
        on_preview(50.0)
        line.set_line_color.assert_called()

    @patch("ui.dialogs.PreviewCommitDialog")
    @patch("utils.commands.PropertyChangeCommand")
    def test_commit_pushes_undo(self, mock_cmd, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_color = QColor(255, 0, 0, 255)
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_opacity_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_commit = call_args[6]
        on_commit(50.0)  # Change from 100% to 50%
        mock_mw.undo_stack.beginMacro.assert_called_with("Change Connector Opacity")
        mock_mw.undo_stack.push.assert_called_once()

    @patch("ui.dialogs.PreviewCommitDialog")
    def test_commit_same_pct_noop(self, mock_dlg_cls, ca, mock_mw):
        line = MagicMock()
        line.line_color = QColor(255, 0, 0, 255)  # 100%
        mock_mw.last_selected_connector = line
        mock_dlg_cls.return_value.exec.return_value = None

        ca.open_opacity_dialog_selected()
        call_args = mock_dlg_cls.call_args[0]
        on_commit = call_args[6]
        on_commit(100.0)  # Same
        mock_mw.undo_stack.push.assert_not_called()


# ============================================================
# bulk_open_width_dialog
# ============================================================
class TestBulkOpenWidthDialog:
    def test_empty_lines_noop(self, ca, mock_mw):
        mock_mw.window_manager.connectors = []
        ca.bulk_open_width_dialog()  # No crash

    @patch("ui.dialogs.SliderSpinDialog")
    def test_creates_dialog(self, mock_dlg_cls, ca, mock_mw):
        from windows.connector import ConnectorLine

        line = MagicMock(spec=ConnectorLine)
        line.line_width = 3
        mock_mw.window_manager.connectors = [line]
        mock_dlg_cls.return_value.exec.return_value = None

        ca.bulk_open_width_dialog()
        mock_dlg_cls.assert_called_once()

    @patch("ui.dialogs.SliderSpinDialog")
    def test_callback_updates_all_lines(self, mock_dlg_cls, ca, mock_mw):
        from windows.connector import ConnectorLine

        line1 = MagicMock(spec=ConnectorLine)
        line1.line_width = 2
        line2 = MagicMock(spec=ConnectorLine)
        line2.line_width = 3
        mock_mw.window_manager.connectors = [line1, line2]
        mock_dlg_cls.return_value.exec.return_value = None

        ca.bulk_open_width_dialog()
        call_args = mock_dlg_cls.call_args[0]
        cb = call_args[5]  # callback
        cb(15)
        assert line1.line_width == 15
        assert line2.line_width == 15


# ============================================================
# bulk_open_opacity_dialog
# ============================================================
class TestBulkOpenOpacityDialog:
    def test_empty_lines_noop(self, ca, mock_mw):
        mock_mw.window_manager.connectors = []
        ca.bulk_open_opacity_dialog()

    @patch("ui.dialogs.SliderSpinDialog")
    def test_creates_dialog_with_first_alpha(self, mock_dlg_cls, ca, mock_mw):
        from windows.connector import ConnectorLine

        line = MagicMock(spec=ConnectorLine)
        line.line_color = QColor(0, 0, 0, 255)  # 100%
        mock_mw.window_manager.connectors = [line]
        mock_dlg_cls.return_value.exec.return_value = None

        ca.bulk_open_opacity_dialog()
        call_args = mock_dlg_cls.call_args[0]
        initial = call_args[4]
        assert initial == 100

    @patch("ui.dialogs.SliderSpinDialog")
    def test_callback_sets_alpha_all(self, mock_dlg_cls, ca, mock_mw):
        from windows.connector import ConnectorLine

        line1 = MagicMock(spec=ConnectorLine)
        line1.line_color = QColor(255, 0, 0, 255)
        line2 = MagicMock(spec=ConnectorLine)
        line2.line_color = QColor(0, 255, 0, 128)
        mock_mw.window_manager.connectors = [line1, line2]
        mock_dlg_cls.return_value.exec.return_value = None

        ca.bulk_open_opacity_dialog()
        call_args = mock_dlg_cls.call_args[0]
        cb = call_args[5]
        cb(50)  # 50% → alpha 127
        # Both lines should have set_line_color called
        line1.set_line_color.assert_called()
        line2.set_line_color.assert_called()

    @patch("ui.dialogs.SliderSpinDialog")
    def test_no_color_first_line_returns(self, mock_dlg_cls, ca, mock_mw):
        from windows.connector import ConnectorLine

        line = MagicMock(spec=ConnectorLine)
        line.line_color = None
        mock_mw.window_manager.connectors = [line]
        ca.bulk_open_opacity_dialog()
        mock_dlg_cls.assert_not_called()
