# -*- coding: utf-8 -*-
"""ConnectorActions のテスト (Sprint 3).

_get_selected_line, delete, set_arrow_style, label_action, _get_all_lines をカバー。
QColorDialog/Dialog 系はスコープ外。
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
# _get_selected_line
# ============================================================
class TestGetSelectedLine:
    def test_returns_none_when_nothing_selected(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        mock_mw.last_selected_window = None
        assert ca._get_selected_line() is None

    def test_returns_last_selected_connector(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        assert ca._get_selected_line() is line

    def test_non_connector_window_returns_none(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        w = MagicMock()
        mock_mw.last_selected_window = w
        assert ca._get_selected_line() is None


# ============================================================
# delete_selected
# ============================================================
class TestDeleteSelected:
    def test_none_line_is_noop(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        mock_mw.last_selected_window = None
        ca.delete_selected()
        mock_mw.connections_tab.on_selection_changed.assert_not_called()

    def test_deletes_with_delete_line(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.delete_selected()
        line.delete_line.assert_called_once()
        mock_mw.connections_tab.on_selection_changed.assert_called_with(None)

    def test_fallback_to_close(self, ca, mock_mw):
        line = MagicMock(spec=["close"])
        mock_mw.last_selected_connector = line
        ca.delete_selected()
        line.close.assert_called_once()


# ============================================================
# change_color_selected
# ============================================================
class TestChangeColorSelected:
    @patch("ui.controllers.connector_actions.QColorDialog.getColor")
    def test_changes_color(self, mock_get_color, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        expected_color = QColor(255, 0, 0)
        mock_get_color.return_value = expected_color
        ca.change_color_selected()
        assert line.line_color == expected_color
        line.update.assert_called_once()

    @patch("ui.controllers.connector_actions.QColorDialog.getColor")
    def test_cancel_does_nothing(self, mock_get_color, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        invalid_color = MagicMock()
        invalid_color.isValid.return_value = False
        mock_get_color.return_value = invalid_color
        ca.change_color_selected()
        line.update.assert_not_called()

    def test_none_is_noop(self, ca, mock_mw):
        mock_mw.last_selected_connector = None
        mock_mw.last_selected_window = None
        ca.change_color_selected()


# ============================================================
# set_arrow_style_selected
# ============================================================
class TestSetArrowStyleSelected:
    def test_none_line_is_noop(self, ca):
        ca.set_arrow_style_selected("end")

    def test_sets_end_style(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("end")
        line.set_arrow_style.assert_called_once()

    def test_sets_none_style(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("none")
        line.set_arrow_style.assert_called_once()

    def test_sets_start_style(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("start")
        line.set_arrow_style.assert_called_once()

    def test_sets_both_style(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("both")
        line.set_arrow_style.assert_called_once()

    def test_invalid_style_returns_early(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("invalid_style")
        line.set_arrow_style.assert_not_called()

    def test_updates_position_after_set(self, ca, mock_mw):
        line = MagicMock()
        mock_mw.last_selected_connector = line
        ca.set_arrow_style_selected("end")
        line.update_position.assert_called()


# ============================================================
# label_action_selected
# ============================================================
class TestLabelActionSelected:
    def test_none_line_is_noop(self, ca):
        ca.label_action_selected("edit")

    def test_no_label_is_noop(self, ca, mock_mw):
        line = MagicMock()
        line.label_window = None
        mock_mw.last_selected_connector = line
        ca.label_action_selected("edit")

    def test_edit_shows_label(self, ca, mock_mw):
        line = MagicMock()
        label = MagicMock()
        label.isHidden.return_value = True
        line.label_window = label
        mock_mw.last_selected_connector = line
        ca.label_action_selected("edit")
        label.show.assert_called_once()
        label.edit_text_realtime.assert_called_once()

    def test_toggle_with_text_clears(self, ca, mock_mw):
        line = MagicMock()
        label = MagicMock()
        label.text = "some text"
        line.label_window = label
        mock_mw.last_selected_connector = line
        ca.label_action_selected("toggle")
        label.set_undoable_property.assert_called()

    def test_toggle_empty_text_shows_edit(self, ca, mock_mw):
        line = MagicMock()
        label = MagicMock()
        label.text = ""
        label.isHidden.return_value = True
        line.label_window = label
        mock_mw.last_selected_connector = line
        ca.label_action_selected("toggle")
        label.show.assert_called()
        label.edit_text_realtime.assert_called()

    def test_toggle_whitespace_shows_edit(self, ca, mock_mw):
        line = MagicMock()
        label = MagicMock()
        label.text = "   "
        label.isHidden.return_value = False
        line.label_window = label
        mock_mw.last_selected_connector = line
        ca.label_action_selected("toggle")
        label.edit_text_realtime.assert_called()


# ============================================================
# _get_all_lines
# ============================================================
class TestGetAllLines:
    def test_empty_connectors(self, ca, mock_mw):
        mock_mw.window_manager.connectors = []
        assert ca._get_all_lines() == []

    def test_filters_none(self, ca, mock_mw):
        mock_mw.window_manager.connectors = [None]
        assert ca._get_all_lines() == []

    def test_non_connector_filtered(self, ca, mock_mw):
        mock_mw.window_manager.connectors = [MagicMock()]
        assert len(ca._get_all_lines()) == 0

    def test_fallback_to_mw(self):
        mw = MagicMock(spec=["connectors"])
        mw.connectors = []
        ca_limited = ConnectorActions(mw)
        assert ca_limited._get_all_lines() == []


# ============================================================
# bulk_change_color
# ============================================================
class TestBulkChangeColor:
    @patch("ui.controllers.connector_actions.QColorDialog.getColor")
    def test_changes_all_colors(self, mock_get_color, ca):
        line1 = MagicMock()
        line2 = MagicMock()
        ca._get_all_lines = MagicMock(return_value=[line1, line2])

        expected_color = QColor(0, 255, 0)
        mock_get_color.return_value = expected_color

        ca.bulk_change_color()
        line1.set_line_color.assert_called()
        line2.set_line_color.assert_called()

    def test_empty_lines_is_noop(self, ca):
        ca._get_all_lines = MagicMock(return_value=[])
        ca.bulk_change_color()
