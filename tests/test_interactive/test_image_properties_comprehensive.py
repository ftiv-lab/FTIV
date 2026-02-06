from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from windows.image_window import ImageWindow


# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


class TestImagePropertiesComprehensive:
    @pytest.fixture
    def setup_env(self, qapp):
        """Setup a minimal environment with real ImageWindow instances."""
        mw = MagicMock()
        mw.window_manager = MagicMock()

        # BaseOverlayWindow adds these actions
        mw.undo_action = QAction("Undo", None)
        mw.redo_action = QAction("Redo", None)

        # Mock add_undo_command to actually execute the command (Simulate Redo)
        def execute_command(command):
            try:
                command.redo()
            except Exception as e:
                pytest.fail(f"Command execution failed: {e}")

        mw.add_undo_command = MagicMock(side_effect=execute_command)

        # Config guardian mock
        mw.app_settings = MagicMock()

        return mw

    @pytest.mark.parametrize(
        "prop_name, test_value, initial_value, update_method",
        [
            ("opacity", 0.5, 1.0, "update_image"),
            ("rotation_angle", 45.0, 0.0, "update_image"),
            ("scale_factor", 1.5, 1.0, "update_image"),
            ("flip_horizontal", True, False, "update_image"),
            ("flip_vertical", True, False, "update_image"),
            ("animation_speed_factor", 2.0, 1.0, "_update_animation_timer"),
            ("is_locked", True, False, None),
            ("position", {"x": 50, "y": 50}, {"x": 0, "y": 0}, "update_position"),
        ],
    )
    def test_set_undoable_property_comprehensive(self, setup_env, prop_name, test_value, initial_value, update_method):
        """
        Verify that set_undoable_property works for ALL standard properties of ImageWindow.
        This ensures that:
        1. The property getter exists (@property).
        2. The property setter exists (@property.setter).
        3. The update method exists (if specified).
        4. No AttributeError is raised during the process.
        """
        mw = setup_env
        win = ImageWindow(mw, image_path="", position=QPoint(0, 0))

        # 1. Verify Initial Value (via Property Get)
        # Note: Position is special (QPoint vs dict), so we might need specific handling for checking
        try:
            _ = getattr(win, prop_name)
            # For position, the getter returns dict, so direct comparison might be ok if initial_value is dict
            # Relaxed check for floating point if needed, but for now exact or type check
        except AttributeError:
            pytest.fail(f"Property '{prop_name}' does not exist on ImageWindow!")

        # 2. Execute set_undoable_property
        try:
            # We assume initial state is 'initial_value' roughly, but we just care that setting works
            win.set_undoable_property(prop_name, test_value, update_method)
        except Exception as e:
            pytest.fail(f"set_undoable_property failed for '{prop_name}': {e}")

        # 3. Verify New Value (via Property Get)
        new_val_fetched = getattr(win, prop_name)

        # Special handling for position dict comparison or float comparison
        if prop_name == "position":
            assert new_val_fetched["x"] == test_value["x"]
            assert new_val_fetched["y"] == test_value["y"]
        elif isinstance(test_value, float):
            assert abs(new_val_fetched - test_value) < 0.001
        else:
            assert new_val_fetched == test_value

        win.close()
