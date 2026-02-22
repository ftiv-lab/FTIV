# -*- coding: utf-8 -*-
"""Tests for SpacingManager class.

Focuses on pure methods that don't require TextWindow mock.
"""

from managers.spacing_manager import SpacingManager
from models.spacing_settings import SpacingSettings


class TestSpacingManagerValidation:
    """Test SpacingManager validation methods."""

    def test_validate_spacing_value_clamped_to_max(self) -> None:
        """Test that values above max are clamped to 5.0."""
        result = SpacingManager.validate_spacing_value(200.0)
        assert result == 5.0

    def test_validate_spacing_value_clamped_to_min(self) -> None:
        """Test that values below min are clamped to -0.5."""
        result = SpacingManager.validate_spacing_value(-200.0)
        assert result == -0.5

    def test_validate_spacing_value_margin_non_negative(self) -> None:
        """Test that margin values are non-negative."""
        result = SpacingManager.validate_spacing_value(-5.0, is_margin=True)
        assert result >= 0.0

    def test_validate_spacing_value_passthrough_valid(self) -> None:
        """Test that valid values within range pass through unchanged."""
        result = SpacingManager.validate_spacing_value(2.5)
        assert result == 2.5

    def test_validate_settings_returns_spacing_settings(self) -> None:
        """Test that validate_settings returns a SpacingSettings object."""
        settings = SpacingSettings()
        result = SpacingManager.validate_settings(settings)
        assert isinstance(result, SpacingSettings)


class TestSpacingManagerDialogConversion:
    """Test dialog tuple conversion methods."""

    def test_dialog_tuple_to_window_config_dict_structure(self) -> None:
        """Test that new API returns correct dict keys."""
        values = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        result = SpacingManager.dialog_tuple_to_window_config_dict(values)

        assert isinstance(result, dict)
        expected_keys = [
            "horizontal_margin_ratio",
            "vertical_margin_ratio",
            "margin_top_ratio",
            "margin_bottom_ratio",
        ]
        for key in expected_keys:
            assert key in result

    def test_dialog_tuple_preserves_values(self) -> None:
        """Test that values are correctly mapped."""
        values = (1.0, 2.0, 0.3, 0.4, 0.1, 0.1)
        result = SpacingManager.dialog_tuple_to_window_config_dict(values)

        # Check horizontal spacing values
        assert result["horizontal_margin_ratio"] == 1.0
        assert result["vertical_margin_ratio"] == 2.0


class TestSpacingManagerDefaults:
    """Test default value retrieval."""

    def test_get_defaults_for_mode_horizontal(self) -> None:
        """Test defaults for horizontal text mode."""
        result = SpacingManager.get_defaults_for_mode(is_vertical=False)
        assert isinstance(result, tuple)
        assert len(result) == 6

    def test_get_defaults_for_mode_vertical(self) -> None:
        """Test defaults for vertical text mode."""
        result = SpacingManager.get_defaults_for_mode(is_vertical=True)
        assert isinstance(result, tuple)
        assert len(result) == 6

    def test_defaults_match_expected_order(self) -> None:
        """Test that defaults tuple matches expected order."""
        # Horizontal mode
        h_result = SpacingManager.get_defaults_for_mode(is_vertical=False)
        # Tuple should be: (char_h, line_h, char_v, line_v, margin_h, margin_v)
        assert all(isinstance(v, (int, float)) for v in h_result)
