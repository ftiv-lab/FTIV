
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QApplication

from models.enums import OffsetMode
from windows.text_window import TextWindow


# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

class TestTextPropertiesComprehensive:
    @pytest.fixture
    def setup_env(self, qapp):
        """Setup a minimal environment with real TextWindow instances."""
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
                # We want to catch this in the test report
                raise RuntimeError(f"Command execution failed: {e}")

        mw.add_undo_command = MagicMock(side_effect=execute_command)

        # Config guardian mock
        mw.app_settings = MagicMock()

        return mw

    @pytest.mark.parametrize("prop_name, test_value, initial_value, update_method", [
        # Basic
        ("text", "New Text", "Default", "update_text"),
        ("font_family", "Arial", "DefaultFont", None),
        ("font_size", 24, 12, None), # Special handling in TextWindow (debounced)

        # Colors (Hex String or QColor -> stored as Hex)
        ("font_color", "#ff0000", "#000000", "update_text"),
        ("background_color", "#00ff00", "#ffffff", "update_text"),

        # Visibility & Opacity
        ("text_visible", False, True, None),
        ("background_visible", False, True, None),
        ("text_opacity", 50, 100, "update_text"),
        ("background_opacity", 50, 100, "update_text"),

        # Shadow
        ("shadow_enabled", True, False, "update_text"),
        ("shadow_color", "#0000ff", "#000000", "update_text"),
        ("shadow_opacity", 80, 0, "update_text"),
        ("shadow_blur", 5, 0, "update_text"),
        ("shadow_scale", 1.1, 1.0, "update_text"),
        ("shadow_offset_x", 2.0, 0.0, None),
        ("shadow_offset_y", 2.0, 0.0, "update_text"),

        # Outline 1
        ("outline_enabled", True, False, "update_text"),
        ("outline_color", "#ff00ff", "#000000", "update_text"),
        ("outline_opacity", 90, 100, "update_text"),
        ("outline_width", 2.0, 0.0, "update_text"),
        ("outline_blur", 1, 0, "update_text"),

        # Outline 2
        ("second_outline_enabled", True, False, "update_text"),
        ("second_outline_color", "#ffff00", "#000000", "update_text"),
        ("second_outline_opacity", 80, 100, "update_text"),
        ("second_outline_width", 3.0, 0.0, "update_text"),
        ("second_outline_blur", 2, 0, "update_text"),

        # Outline 3
        ("third_outline_enabled", True, False, "update_text"),
        ("third_outline_color", "#00ffff", "#000000", "update_text"),
        ("third_outline_opacity", 70, 100, "update_text"),
        ("third_outline_width", 4.0, 0.0, "update_text"),
        ("third_outline_blur", 3, 0, "update_text"),

        # Background Outline
        ("background_outline_enabled", True, False, "update_text"),
        ("background_outline_color", "#123456", "#000000", "update_text"),
        ("background_outline_opacity", 60, 100, "update_text"),
        ("background_outline_width_ratio", 0.1, 0.0, "update_text"), # This might verify differently?

        # Gradients (Scalars)
        ("text_gradient_enabled", True, False, "update_text"),
        ("text_gradient_angle", 45, 0, "update_text"),
        ("text_gradient_opacity", 90, 100, "update_text"),
        ("background_gradient_enabled", True, False, "update_text"),
        ("background_gradient_angle", 90, 0, "update_text"),
        ("background_gradient_opacity", 80, 100, "update_text"),

        # Margins & Layout
        ("is_vertical", True, False, "update_text"),
        ("offset_mode", OffsetMode.PROP, OffsetMode.MONO, "update_text"),
        ("horizontal_margin_ratio", 0.5, 0.0, "update_text"),
        ("vertical_margin_ratio", 0.5, 0.0, "update_text"),
        ("margin_top_ratio", 0.1, 0.0, None),
        ("margin_bottom_ratio", 0.1, 0.0, None),
        ("margin_left_ratio", 0.1, 0.0, None),
        ("margin_right_ratio", 0.1, 0.0, None),
        ("background_corner_ratio", 0.2, 0.0, None),

        # Inherited from BaseOverlayWindow
        ("position", {"x": 100, "y": 100}, {"x": 0, "y": 0}, "update_position"),
    ])
    def test_set_undoable_property_text_comprehensive(self, setup_env, prop_name, test_value, initial_value, update_method):
        """
        Verify that set_undoable_property works for ALL properties of TextWindow.
        """
        mw = setup_env
        win = TextWindow(mw, text="Default", pos=QPoint(0, 0))

        # 1. Verify Property Existence
        if not hasattr(win, prop_name):
            pytest.fail(f"Property '{prop_name}' does not exist on TextWindow!")

        # 2. Execute set_undoable_property
        try:
            win.set_undoable_property(prop_name, test_value, update_method)
        except Exception as e:
            pytest.fail(f"set_undoable_property failed for '{prop_name}': {e}")

        # 3. Verify New Value
        try:
            new_val_fetched = getattr(win, prop_name)
        except Exception as e:
             pytest.fail(f"Failed to get property '{prop_name}' after setting: {e}")

        # Verification Logic
        if prop_name == "position":
            assert new_val_fetched["x"] == test_value["x"]
            assert new_val_fetched["y"] == test_value["y"]

        elif "color" in prop_name:
            # Color might be returned as QColor or Hex String depending on getter implementation
            # TextWindow getters usually return QColor, but config stores string.
            # Let's check:
            #   @property def font_color(self) -> QColor: return self._get_color(...)
            # So getter returns QColor.
            # But we passed Hex String "#ff0000".
            # QColor("#ff0000") should equal fetched QColor.

            if isinstance(new_val_fetched, QColor):
                expected_col = QColor(test_value)
                # Compare hex strings to avoid alpha/format minor differences if any
                assert new_val_fetched.name(QColor.HexArgb) == expected_col.name(QColor.HexArgb)
            else:
                # If it returned string
                assert new_val_fetched == test_value

        elif isinstance(test_value, float):
            assert abs(new_val_fetched - test_value) < 0.001

        else:
            assert new_val_fetched == test_value

        win.close()
