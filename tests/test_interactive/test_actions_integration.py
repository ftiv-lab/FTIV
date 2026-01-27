
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from ui.controllers.image_actions import ImageActions
from windows.image_window import ImageWindow


# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

class TestActionsIntegration:
    @pytest.fixture
    def setup_env(self, qapp):
        """Setup a minimal environment."""
        mw = MagicMock()
        mw.window_manager = MagicMock()

        mw.undo_action = QAction("Undo", None)
        mw.redo_action = QAction("Redo", None)

        # Helper to execute undo commands
        def execute_command(command):
            try:
                command.redo()
            except Exception as e:
                # Log or re-raise
                print(f"Command execution error: {e}")

        mw.add_undo_command = MagicMock(side_effect=execute_command)
        mw.app_settings = MagicMock()
        mw.undo_stack = MagicMock() # For macros

        return mw

    def test_image_normalize_integration(self, setup_env):
        """
        Verify 'Normalize Images' action works on Real Objects.
        This checks if 'scale_factor' and 'size' access patterns are correct.
        """
        mw = setup_env
        actions = ImageActions(mw)

        # Create 2 windows
        # Note: image_path="dummy" triggers placeholder image (200x200)
        win1 = ImageWindow(mw, image_path="dummy_ref.png", position=QPoint(0, 0)) # Selected
        win2 = ImageWindow(mw, image_path="dummy_target.png", position=QPoint(100, 0)) # Target

        # Set different scales
        win1.scale_factor = 2.0  # Ref
        win2.scale_factor = 0.5

        # Verify frames exist (Debuging failure)
        assert len(win1.frames) > 0, "win1 has no frames (placeholder failed)"
        assert len(win2.frames) > 0, "win2 has no frames"

        # Determine actual size after scale
        # If running in headless/CI, sometimes resize events are delayed or behave differently?
        print(f"Win1 Size: {win1.width()}x{win1.height()}, Scale: {win1.scale_factor}")

        # Win2 Debug
        win2.update_image()
        QApplication.processEvents()
        print(f"Win2 Size: {win2.width()}x{win2.height()}, Scale: {win2.scale_factor}")

        # Setup selection behavior
        actions._get_selected_image = MagicMock(return_value=win1)

        # Register windows
        mw.window_manager.image_windows = [win1, win2]

        # Execute Normalize (same_pct)
        # Should make win2 scale = 2.0
        actions.normalize_all_images_by_selected(mode="same_pct")

        assert win2.scale_factor == 2.0

        # Execute Normalize (same_width)
        # Reset/Ensure states
        win1.scale_factor = 2.0
        win1.update_image()
        QApplication.processEvents()

        win2.scale_factor = 0.5
        win2.update_image()
        QApplication.processEvents()

        actions.normalize_all_images_by_selected(mode="same_width")

        # win2 should essentially become scale 2.0 to match win1's width
        # Precision might be slight issue
        assert abs(win2.scale_factor - 2.0) < 0.1

        win1.close()
        win2.close()

    def test_reset_all_flips(self, setup_env):
        """Verify reset_all_flips works on Real Objects."""
        mw = setup_env
        actions = ImageActions(mw)

        win1 = ImageWindow(mw, image_path="", position=QPoint(0,0))
        win2 = ImageWindow(mw, image_path="", position=QPoint(0,0))

        win1.flip_horizontal = True
        win2.flip_vertical = True

        mw.window_manager.image_windows = [win1, win2]

        actions.reset_all_flips()

        assert win1.flip_horizontal is False
        assert win2.flip_vertical is False

        win1.close()
        win2.close()
