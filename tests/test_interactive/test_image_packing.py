from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from ui.controllers.image_actions import ImageActions
from windows.image_window import ImageWindow


# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


class TestImagePacking:
    @pytest.fixture
    def setup_env(self, qapp):
        """Setup a minimal environment with real ImageWindow instances."""
        mw = MagicMock()
        mw.window_manager = MagicMock()

        mw.undo_action = QAction("Undo", None)
        mw.redo_action = QAction("Redo", None)

        # Mock add_undo_command to actually execute the command
        def execute_command(command):
            command.redo()

        mw.add_undo_command = MagicMock(side_effect=execute_command)

        return mw
        # But for local run, real monitors exist.
        # We'll use patch to simulate a standard screen just in case.

        return mw

    def test_pack_all_left_top_real_objects(self, setup_env):
        """
        Verify pack_all_left_top works with REAL ImageWindow instances,
        ensuring 'position' property exists and is accessible via set_undoable_property.
        """
        mw = setup_env
        actions = ImageActions(mw)

        # Create Real Witnesses
        # Note: image_path="" creates a placeholder (valid window)
        win1 = ImageWindow(mw, image_path="", position=QPoint(0, 0))
        win2 = ImageWindow(mw, image_path="", position=QPoint(0, 0))

        win1.resize(100, 100)
        win2.resize(100, 100)

        # Register them
        mw.window_manager.image_windows = [win1, win2]

        # Call the target method
        # screen_index=0, space=10
        # We mock QApplication.screens to return a predictable screen geometry
        mock_screen = MagicMock()
        mock_screen.geometry.return_value = QRect(0, 0, 1920, 1080)

        with patch("PySide6.QtWidgets.QApplication.screens", return_value=[mock_screen]):
            actions.pack_all_left_top(0, space=10)

        # Verify positions
        # Standard logic:
        # Start (0,0) -> +space(10) -> (10, 10)
        # First window at (10, 10). Width 100.
        # Next x = 10 + 100 + 10 = 120.
        # Second window at (120, 10).

        print(f"Win1 Pos: {win1.pos()}")
        print(f"Win2 Pos: {win2.pos()}")

        assert win1.x() == 10
        assert win1.y() == 10
        assert win2.x() == 120
        assert win2.y() == 10

        win1.close()
        win2.close()

    def test_pack_all_center_real_objects(self, setup_env):
        """Verify pack_all_center works with REAL ImageWindow instances."""
        mw = setup_env
        actions = ImageActions(mw)

        win1 = ImageWindow(mw, image_path="")  # 100x100 default
        mw.window_manager.image_windows = [win1]

        mock_screen = MagicMock()
        # Small screen 200x200
        mock_screen.geometry.return_value = QRect(0, 0, 200, 200)

        with patch("PySide6.QtWidgets.QApplication.screens", return_value=[mock_screen]):
            actions.pack_all_center(0, space=0)

        # Center of 200 is 100.
        # Window is 100.
        # Start x = (200 - 100) / 2 = 50.
        # Start y = (200 - 100) / 2 = 50.

        assert win1.x() == 50
        assert win1.y() == 50

        win1.close()
