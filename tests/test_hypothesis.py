# -*- coding: utf-8 -*-
"""Property-based tests using Hypothesis.

This module uses Hypothesis to generate random test cases and find edge cases
that traditional unit tests might miss.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from models.enums import AnchorPosition, ArrowStyle
from models.window_config import ImageWindowConfig, TextWindowConfig, WindowConfigBase


class TestWindowConfigHypothesis:
    """Property-based tests for WindowConfig models."""

    @given(
        move_speed=st.integers(min_value=0, max_value=10000),
        fade_speed=st.integers(min_value=0, max_value=10000),
        move_pause=st.integers(min_value=0, max_value=5000),
    )
    @settings(max_examples=50)
    def test_window_config_base_accepts_valid_ints(self, move_speed: int, fade_speed: int, move_pause: int) -> None:
        """Test that WindowConfigBase accepts valid integer ranges."""
        config = WindowConfigBase(
            move_speed=move_speed,
            fade_speed=fade_speed,
            move_pause_time=move_pause,
        )
        assert config.move_speed == move_speed
        assert config.fade_speed == fade_speed
        assert config.move_pause_time == move_pause

    @given(
        anchor=st.sampled_from(list(AnchorPosition)),
        is_hidden=st.booleans(),
        is_locked=st.booleans(),
    )
    @settings(max_examples=30)
    def test_window_config_base_flags_and_anchor(
        self, anchor: AnchorPosition, is_hidden: bool, is_locked: bool
    ) -> None:
        """Test boolean flags and anchor position combinations."""
        config = WindowConfigBase(
            anchor_position=anchor,
            is_hidden=is_hidden,
            is_locked=is_locked,
        )
        assert config.is_hidden == is_hidden
        assert config.is_locked == is_locked


class TestImageWindowConfigHypothesis:
    """Property-based tests for ImageWindowConfig."""

    @given(
        opacity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        rotation=st.floats(min_value=-360.0, max_value=360.0, allow_nan=False, allow_infinity=False),
        scale=st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_image_config_valid_ranges(self, opacity: float, rotation: float, scale: float) -> None:
        """Test ImageWindowConfig with valid parameter ranges."""
        config = ImageWindowConfig(
            opacity=opacity,
            rotation_angle=rotation,
            scale_factor=scale,
        )
        assert config.opacity == opacity
        assert config.rotation_angle == rotation
        assert config.scale_factor == scale

    @given(
        anim_speed=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        flip_h=st.booleans(),
        flip_v=st.booleans(),
    )
    @settings(max_examples=30)
    def test_image_animation_and_flip(self, anim_speed: float, flip_h: bool, flip_v: bool) -> None:
        """Test animation speed and flip combinations."""
        config = ImageWindowConfig(
            animation_speed_factor=anim_speed,
            flip_horizontal=flip_h,
            flip_vertical=flip_v,
        )
        assert config.animation_speed_factor == anim_speed
        assert config.flip_horizontal == flip_h
        assert config.flip_vertical == flip_v


class TestTextWindowConfigHypothesis:
    """Property-based tests for TextWindowConfig."""

    @given(
        font_size=st.integers(min_value=1, max_value=500),
        text_opacity=st.integers(min_value=0, max_value=100),
        outline_width=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_text_config_valid_ranges(self, font_size: int, text_opacity: int, outline_width: float) -> None:
        """Test TextWindowConfig with valid parameter ranges."""
        config = TextWindowConfig(
            font_size=font_size,
            text_opacity=text_opacity,
            outline_width=outline_width,
        )
        assert config.font_size == font_size
        assert config.text_opacity == text_opacity
        assert config.outline_width == outline_width

    @given(
        bg_visible=st.booleans(),
        shadow_enabled=st.booleans(),
        gradient_enabled=st.booleans(),
    )
    @settings(max_examples=20)
    def test_boolean_flags_combination(self, bg_visible: bool, shadow_enabled: bool, gradient_enabled: bool) -> None:
        """Test all combinations of boolean flags."""
        config = TextWindowConfig(
            background_visible=bg_visible,
            shadow_enabled=shadow_enabled,
            text_gradient_enabled=gradient_enabled,
        )
        assert config.background_visible == bg_visible
        assert config.shadow_enabled == shadow_enabled
        assert config.text_gradient_enabled == gradient_enabled

    @given(
        offset_x=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        offset_y=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        blur=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=30)
    def test_shadow_parameters(self, offset_x: float, offset_y: float, blur: int) -> None:
        """Test shadow offset and blur parameters."""
        config = TextWindowConfig(
            shadow_offset_x=offset_x,
            shadow_offset_y=offset_y,
            shadow_blur=blur,
        )
        assert config.shadow_offset_x == offset_x
        assert config.shadow_offset_y == offset_y
        assert config.shadow_blur == blur


class TestArrowStyleHypothesis:
    """Property-based tests for ArrowStyle enum."""

    @given(style=st.sampled_from(list(ArrowStyle)))
    @settings(max_examples=10)
    def test_all_arrow_styles_valid(self, style: ArrowStyle) -> None:
        """Test that all ArrowStyle values are valid."""
        assert style in ArrowStyle
        assert isinstance(style.value, str)
