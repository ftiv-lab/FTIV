import os

# Ensure we can import modules
import sys

sys.path.append(os.getcwd())

from models.spacing_settings import (
    DEFAULT_CHAR_SPACING,
    DEFAULT_MARGIN_TOP,
    DEFAULT_V_MARGIN_RIGHT,
    SpacingSettings,
)

# -----------------------------------------------------------------------------
# Unit Tests: SpacingSettings (Data Structure & Logic)
# -----------------------------------------------------------------------------


class TestSpacingSettings:
    def test_defaults(self):
        """Verify default values are correct for both modes."""
        settings = SpacingSettings()

        # Horizontal Defaults
        assert settings.horizontal.char_spacing == DEFAULT_CHAR_SPACING
        assert settings.horizontal.margin_top == DEFAULT_MARGIN_TOP

        # Vertical Defaults
        assert settings.vertical.margin_right == DEFAULT_V_MARGIN_RIGHT
        assert settings.vertical.margin_left == 0.0  # Default V Left

    def test_to_dict_structure(self):
        """Verify the new internal dictionary structure (Nested)."""
        settings = SpacingSettings()
        settings.horizontal.char_spacing = 1.5
        settings.vertical.margin_top = 2.0

        data = settings.to_dict()

        # Verify structure keys
        assert "horizontal" in data
        assert "vertical" in data

        # Verify nested values
        # Note: keys match field names in dataclass, not legacy "v_" names
        assert data["horizontal"]["char_spacing"] == 1.5
        assert data["vertical"]["margin_top"] == 2.0

    def test_from_dict_roundtrip(self):
        """Verify we can restore settings from a nested dictionary."""
        original = SpacingSettings()
        original.horizontal.margin_left = 4.2
        original.vertical.margin_bottom = 9.9

        data = original.to_dict()
        restored = SpacingSettings.from_dict(data)

        assert restored.horizontal.margin_left == 4.2
        assert restored.vertical.margin_bottom == 9.9

    def test_window_config_dict_export(self):
        """Verify export to TextWindow flat property dict structure."""
        settings = SpacingSettings()
        settings.horizontal.char_spacing = 1.0
        settings.vertical.margin_top = 2.0

        exported = settings.to_window_config_dict()

        # Check mapping logic
        assert exported["horizontal_margin_ratio"] == 1.0
        assert exported["v_margin_top_ratio"] == 2.0
        assert "margin_left_ratio" in exported

    def test_window_config_fields_import(self):
        """Verify initialization from TextWindow property components."""
        settings = SpacingSettings.from_window_config_fields(
            horizontal_margin_ratio=0.5,
            margin_top=0.8,
            # Vertical specific (optional)
            v_margin_right=1.2,
        )

        assert settings.horizontal.char_spacing == 0.5
        assert settings.horizontal.margin_top == 0.8
        assert settings.vertical.margin_right == 1.2
        # Should use defaults for unspecified
        assert settings.vertical.margin_left == 0.0


# -----------------------------------------------------------------------------
# Integration Tests: Persistence Compatibility
# -----------------------------------------------------------------------------


class TestPersistenceCompatibility:
    """
    Since BulkOperationManager handles saving/loading directly using window config keys,
    we must verify SpacingSettings is compatible with that data format.
    """

    def test_bulk_manager_json_compatibility(self):
        """
        Verify that JSON data structure used in BulkOperationManager
        can be correctly mapped to SpacingSettings.
        """
        # 1. Simulate the Dictionary created in BulkOperationManager.set_default_text_spacing
        # See bulk_manager.py line 210
        saved_json_data = {
            "h_margin": 0.5,  # Maps to char_spacing
            "v_margin": 1.2,  # Maps to line_spacing (vertical_margin_ratio)
            "margin_top": 0.3,
            "margin_bottom": 0.3,
            "margin_left": 0.3,
            "margin_right": 0.0,
        }

        # 2. Simulate Loading Logic
        # The app loads this JSON, creates a dict, and then applies it via set_undoable_property.
        # SpacingSettings.from_window_config_fields simulates how these properties map.

        settings = SpacingSettings.from_window_config_fields(
            horizontal_margin_ratio=saved_json_data["h_margin"],
            vertical_margin_ratio=saved_json_data["v_margin"],
            margin_top=saved_json_data["margin_top"],
            margin_bottom=saved_json_data["margin_bottom"],
            margin_left=saved_json_data["margin_left"],
            margin_right=saved_json_data["margin_right"],
        )

        # 3. Verify Mapping
        assert settings.horizontal.char_spacing == 0.5
        assert settings.horizontal.line_spacing == 1.2
        assert settings.horizontal.margin_top == 0.3

        # 4. Verify Vertical Isolation (line_spacing is intentionally shared).
        assert settings.vertical.line_spacing == 1.2

    def test_vertical_defaults_compatibility(self):
        """Verify vertical defaults loader compatibility."""
        # See bulk_manager.py line 279
        saved_vertical_json = {
            "v_margin_top": 0.8,
            "v_margin_bottom": 0.1,
            "v_margin_left": 0.2,
            "v_margin_right": 0.3,
        }

        settings = SpacingSettings.from_window_config_fields(
            v_margin_top=saved_vertical_json["v_margin_top"],
            v_margin_bottom=saved_vertical_json["v_margin_bottom"],
            v_margin_left=saved_vertical_json["v_margin_left"],
            v_margin_right=saved_vertical_json["v_margin_right"],
        )

        assert settings.vertical.margin_top == 0.8
        assert settings.vertical.margin_bottom == 0.1
        # Horizontal should correspond to defaults
        assert settings.horizontal.margin_top == DEFAULT_MARGIN_TOP
