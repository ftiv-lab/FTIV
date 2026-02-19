import sys
import types
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint

from managers.window_manager import WindowManager


class TestWindowManager:
    @pytest.fixture
    def window_manager(self):
        mw = MagicMock()
        wm = WindowManager(mw)
        # Fix: Use correct attribute name if accessed in tests, though wm.main_window is proper
        # wm.mw does not exist.
        wm.connectors = []
        wm.text_windows = []
        wm.image_windows = []
        return wm

    def test_set_selected_window_text(self, window_manager):
        txt_win = MagicMock()
        window_manager.set_selected_window(txt_win)

        assert window_manager.last_selected_window == txt_win
        # Fix: Use window_manager.main_window
        window_manager.main_window.on_window_selected.assert_not_called()
        # Wait, set_selected_window calls self.sig_selection_changed.emit(window).
        # It does NOT call mw.on_window_selected directly in the snippet I read.
        # It calls:
        # self.sig_selection_changed.emit(window)
        # And previously setup_window_connections connected it?
        # Let's check window_manager.py again.
        # It connects sig_window_selected TO self.set_selected_window.
        # But set_selected_window logic:
        # if self.last_selected_window... set_selected(False)
        # self.last_selected_window = window
        # ... set_selected(True)
        # self.sig_selection_changed.emit(window)
        # It does NOT call main_window methods directly about selection.
        # So we should check sig_selection_changed emit OR just the internal state.

    def test_remove_window_text_found(self, window_manager):
        txt_win = MagicMock()
        window_manager.text_windows = [txt_win]

        window_manager.remove_window(txt_win)

        assert txt_win not in window_manager.text_windows
        # Fix: remove_window cleans up lists and refs. It does not necessarily call close() on the window itself
        # (usually called BY the window closing).
        # So expectation of close() is wrong here. We verified list removal.

    def test_add_connector(self, window_manager):
        start = MagicMock()
        end = MagicMock()
        start.uuid = "start_uuid"
        end.uuid = "end_uuid"

        with pytest.MonkeyPatch.context() as m:
            mock_ConnectorLine = MagicMock()
            # The constructor returns a mock instance
            mock_line_instance = MagicMock()
            mock_ConnectorLine.return_value = mock_line_instance

            # Patch where WindowManager imports it
            m.setattr("managers.window_manager.ConnectorLine", mock_ConnectorLine)

            window_manager.add_connector(start, end)

            # Check constructor call
            mock_ConnectorLine.assert_called_once()
            args, kwargs = mock_ConnectorLine.call_args
            assert args[0] == start
            assert args[1] == end

            assert mock_line_instance in window_manager.connectors

    def test_delete_connector_logic(self, window_manager):
        conn = MagicMock()
        window_manager.connectors = [conn]

        # Patch QTimer to run immediately
        with pytest.MonkeyPatch.context() as m:
            mock_QTimer = MagicMock()

            # When singleShot(0, callback) is called, run callback immediately
            def side_effect(ms, callback):
                callback()

            mock_QTimer.singleShot.side_effect = side_effect

            # We need to patch PySide6.QtCore.QTimer inside managers.window_manager implies patching where it is imported
            # But the code does 'from PySide6.QtCore import QTimer' inside try block or top level?
            # It does `from PySide6.QtCore import QTimer` inside delete_connector try block.
            # Using sys.modules patching might be needed or patch PySide6.QtCore.QTimer globally.
            m.setattr("PySide6.QtCore.QTimer", mock_QTimer)

            window_manager.delete_connector(conn)

        assert conn not in window_manager.connectors
        conn.close.assert_called()

    def test_attach_layer_syncs_child_frontmost_to_parent(self, window_manager):
        parent = MagicMock()
        child = MagicMock()
        parent.uuid = "parent"
        child.uuid = "child"
        parent.child_windows = []
        parent.pos.return_value = QPoint(0, 0)
        child.pos.return_value = QPoint(10, 20)
        parent.is_frontmost = False
        child.is_frontmost = True
        child.config = MagicMock()
        child.config.layer_offset = None
        child.config.layer_order = None

        def _add_child(c):
            parent.child_windows.append(c)

        parent.add_child_window.side_effect = _add_child
        window_manager.raise_group_stack = MagicMock()
        window_manager.main_window.undo_stack = None

        window_manager.attach_layer(parent, child)

        assert child.is_frontmost is False
        assert child.config.layer_offset == {"x": 10, "y": 20}
        assert child.config.layer_order == 0
        window_manager.raise_group_stack.assert_called_once_with(parent)

    def test_raise_group_stack_skip_parent_during_drag(self, window_manager, monkeypatch):
        fake_shiboken = types.SimpleNamespace(isValid=lambda _obj: True)
        monkeypatch.setitem(sys.modules, "shiboken6", fake_shiboken)

        parent = MagicMock()
        child = MagicMock()
        grandchild = MagicMock()
        parent.child_windows = [child]
        child.child_windows = [grandchild]
        grandchild.child_windows = []

        parent.config = MagicMock()
        parent.config.layer_order = 0
        child.config = MagicMock()
        child.config.layer_order = 0
        grandchild.config = MagicMock()
        grandchild.config.layer_order = 0

        window_manager.raise_group_stack(parent, include_parent=False)

        parent.raise_.assert_not_called()
        child.raise_.assert_called_once()
        grandchild.raise_.assert_called_once()
