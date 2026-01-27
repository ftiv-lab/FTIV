from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QColor

from ui.controllers.connector_actions import ConnectorActions


class TestConnectorActions:
    @pytest.fixture
    def connector_actions(self, qapp):
        self.mw = MagicMock()
        # Mock connections_tab which is used in delete_selected
        self.mw.connections_tab = MagicMock()
        # Mock window_manager for bulk operations
        self.mw.window_manager = MagicMock()
        self.mw.window_manager.connectors = []

        return ConnectorActions(self.mw)

    def test_delete_selected_with_selection(self, connector_actions):
        # Setup selected connector
        mock_line = MagicMock()
        # Make it look like a ConnectorLine
        mock_line.__class__.__name__ = "ConnectorLine"

        # Determine selection via last_selected_connector logic
        connector_actions.mw.last_selected_connector = mock_line

        # Test deletion
        connector_actions.delete_selected()

        # Should call delete_line() if available (or close())
        # We didn't define delete_line on mock, so it might try close()
        # Wait, if we use MagicMock, it has delete_line by default? No, only matching spec if spec is used.
        # But MagicMock will just accept any call.
        # ConnectorActions.delete_selected checks hasattr("delete_line").
        # MagicMock has "delete_line"? Yes, accessing it creates a child mock.
        # So "if hasattr(line, 'delete_line')" will be True.

        mock_line.delete_line.assert_called_once()

        # Check UI reset
        connector_actions.mw.connections_tab.on_selection_changed.assert_called_with(None)

    def test_delete_selected_no_selection(self, connector_actions):
        connector_actions.mw.last_selected_connector = None
        connector_actions.mw.last_selected_window = None

        connector_actions.delete_selected()

        # Should do nothing
        connector_actions.mw.connections_tab.on_selection_changed.assert_not_called()

    @patch("ui.controllers.connector_actions.QColorDialog.getColor")
    def test_change_color_selected(self, mock_get_color, connector_actions):
        # Setup
        mock_line = MagicMock()
        connector_actions.mw.last_selected_connector = mock_line

        # Setup expected color
        expected_color = QColor(255, 0, 0)
        mock_get_color.return_value = expected_color

        # Execute
        connector_actions.change_color_selected()

        # Check
        assert mock_line.line_color == expected_color
        mock_line.update.assert_called_once()

    @patch("ui.controllers.connector_actions.QColorDialog.getColor")
    def test_bulk_change_color(self, mock_get_color, connector_actions):
        # Setup multiple lines
        line1 = MagicMock()
        line2 = MagicMock()

        # Bypass _get_all_lines logic which is hard to mock due to local import + isinstance
        connector_actions._get_all_lines = MagicMock(return_value=[line1, line2])

        # Setup return color
        expected_color = QColor(0, 255, 0)
        mock_get_color.return_value = expected_color

        # Execute
        connector_actions.bulk_change_color()

        # Check logic
        # Because MagicMock has all attributes, hasattr(line, "set_line_color") is True.
        # So it calls set_line_color(c).

        line1.set_line_color.assert_called()
        args1, _ = line1.set_line_color.call_args
        assert args1[0].name() == expected_color.name()

        line2.set_line_color.assert_called()
        args2, _ = line2.set_line_color.call_args
        assert args2[0].name() == expected_color.name()
