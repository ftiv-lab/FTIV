# -*- coding: utf-8 -*-
"""Boundary value tests to verify edge case handling.

This module focuses on testing values at the boundaries of valid input ranges.
Industry standard: test at min, max, min-1, max+1, and typical values.
"""

from models.enums import AnchorPosition, ArrowStyle
from models.window_config import ImageWindowConfig, TextWindowConfig, WindowConfigBase


class TestWindowConfigBoundaryValues:
    """Test boundary values for WindowConfigBase model."""

    def test_scale_factor_min_boundary(self) -> None:
        """Test scale at minimum practical value."""
        config = ImageWindowConfig(scale_factor=0.01)
        assert config.scale_factor == 0.01

    def test_scale_factor_max_boundary(self) -> None:
        """Test scale at maximum practical value."""
        config = ImageWindowConfig(scale_factor=10.0)
        assert config.scale_factor == 10.0

    def test_scale_factor_zero(self) -> None:
        """Test scale at zero (edge case)."""
        config = ImageWindowConfig(scale_factor=0.0)
        assert config.scale_factor == 0.0

    def test_fade_speed_min(self) -> None:
        """Test fade speed at minimum (0ms)."""
        config = WindowConfigBase(fade_speed=0)
        assert config.fade_speed == 0

    def test_move_speed_max(self) -> None:
        """Test move speed at large value."""
        config = WindowConfigBase(move_speed=100000)
        assert config.move_speed == 100000


class TestImageWindowConfigBoundary:
    """Test boundary values for ImageWindowConfig."""

    def test_opacity_min_boundary(self) -> None:
        """Test opacity at minimum boundary (0.0)."""
        config = ImageWindowConfig(opacity=0.0)
        assert config.opacity == 0.0

    def test_opacity_max_boundary(self) -> None:
        """Test opacity at maximum boundary (1.0)."""
        config = ImageWindowConfig(opacity=1.0)
        assert config.opacity == 1.0

    def test_opacity_below_zero(self) -> None:
        """Test opacity below valid range."""
        config = ImageWindowConfig(opacity=-0.1)
        # Document current behavior - Pydantic accepts it
        assert config.opacity == -0.1

    def test_opacity_above_one(self) -> None:
        """Test opacity above valid range."""
        config = ImageWindowConfig(opacity=1.5)
        assert config.opacity == 1.5

    def test_rotation_angle_min_boundary(self) -> None:
        """Test rotation at minimum (0 degrees)."""
        config = ImageWindowConfig(rotation_angle=0.0)
        assert config.rotation_angle == 0.0

    def test_rotation_angle_max_boundary(self) -> None:
        """Test rotation at maximum (360 degrees)."""
        config = ImageWindowConfig(rotation_angle=360.0)
        assert config.rotation_angle == 360.0

    def test_rotation_angle_negative(self) -> None:
        """Test negative rotation angle."""
        config = ImageWindowConfig(rotation_angle=-90.0)
        assert config.rotation_angle == -90.0

    def test_animation_speed_factor_zero(self) -> None:
        """Test animation speed at zero (paused)."""
        config = ImageWindowConfig(animation_speed_factor=0.0)
        assert config.animation_speed_factor == 0.0

    def test_animation_speed_factor_high(self) -> None:
        """Test very high animation speed."""
        config = ImageWindowConfig(animation_speed_factor=5.0)
        assert config.animation_speed_factor == 5.0


class TestTextWindowConfigBoundary:
    """Test boundary values for TextWindowConfig."""

    def test_font_size_min(self) -> None:
        """Test minimum font size."""
        config = TextWindowConfig(font_size=1)
        assert config.font_size == 1

    def test_font_size_zero(self) -> None:
        """Test zero font size (edge case)."""
        config = TextWindowConfig(font_size=0)
        assert config.font_size == 0

    def test_font_size_large(self) -> None:
        """Test very large font size."""
        config = TextWindowConfig(font_size=1000)
        assert config.font_size == 1000

    def test_outline_width_zero(self) -> None:
        """Test zero outline width."""
        config = TextWindowConfig(outline_width=0.0)
        assert config.outline_width == 0.0

    def test_shadow_offset_negative(self) -> None:
        """Test negative shadow offset."""
        config = TextWindowConfig(shadow_offset_x=-10.0, shadow_offset_y=-10.0)
        assert config.shadow_offset_x == -10.0
        assert config.shadow_offset_y == -10.0

    def test_text_opacity_min(self) -> None:
        """Test text opacity at minimum (0%)."""
        config = TextWindowConfig(text_opacity=0)
        assert config.text_opacity == 0

    def test_text_opacity_max(self) -> None:
        """Test text opacity at maximum (100%)."""
        config = TextWindowConfig(text_opacity=100)
        assert config.text_opacity == 100

    def test_content_mode_default(self) -> None:
        """Task mode default must remain note for backward compatibility."""
        config = TextWindowConfig()
        assert config.content_mode == "note"

    def test_metadata_defaults(self) -> None:
        """Information-management metadata should have stable defaults."""
        config = TextWindowConfig()
        assert config.title == ""
        assert config.tags == []
        assert config.is_starred is False
        assert config.created_at == ""
        assert config.updated_at == ""
        assert config.task_states == []
        assert config.task_schema_version == 1
        assert config.note_vertical_preference is False


class TestEnumBoundary:
    """Test enum values at boundaries."""

    def test_all_anchor_positions_valid(self) -> None:
        """Verify all AnchorPosition enum values are accessible."""
        positions = list(AnchorPosition)
        assert len(positions) > 0
        assert AnchorPosition.AUTO in positions
        assert AnchorPosition.TOP in positions

    def test_all_arrow_styles_valid(self) -> None:
        """Verify all ArrowStyle enum values are accessible."""
        styles = list(ArrowStyle)
        assert len(styles) > 0
        assert ArrowStyle.NONE in styles
        assert ArrowStyle.END in styles
