# -*- coding: utf-8 -*-
"""Tests for ThemeManager and StyleManager.

Focuses on pure functions and data validation without mocking complex UI.
"""

from managers.style_manager import _TextRenderDummy
from managers.theme_manager import DARK_THEME
from models.window_config import TextWindowConfig


class TestDarkThemeTokens:
    """Test DARK_THEME design tokens."""

    def test_dark_theme_contains_required_tokens(self) -> None:
        """Test that DARK_THEME has all required color tokens."""
        required_tokens = [
            "@bg_primary",
            "@bg_secondary",
            "@surface",
            "@border",
            "@accent_primary",
            "@text_primary",
        ]
        for token in required_tokens:
            assert token in DARK_THEME, f"Missing token: {token}"

    def test_dark_theme_values_are_hex_colors(self) -> None:
        """Test that all token values are valid hex colors."""
        for token, value in DARK_THEME.items():
            assert value.startswith("#"), f"{token} should be hex color"
            assert len(value) in (4, 7), f"{token} has invalid hex length: {value}"

    def test_dark_theme_bg_primary_is_dark(self) -> None:
        """Test that background is actually dark (low brightness)."""
        bg = DARK_THEME["@bg_primary"]
        # Extract RGB and check brightness
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
        brightness = (r + g + b) / 3
        assert brightness < 100, f"Background too bright: {brightness}"


class TestTextRenderDummy:
    """Test _TextRenderDummy class for TextRenderer compatibility."""

    def test_dummy_creates_from_config(self) -> None:
        """Test that _TextRenderDummy can be created from TextWindowConfig."""
        config = TextWindowConfig()
        dummy = _TextRenderDummy(config)
        assert dummy is not None

    def test_dummy_exposes_font_family(self) -> None:
        """Test that dummy exposes font_family from config."""
        config = TextWindowConfig(font="Arial")
        dummy = _TextRenderDummy(config)
        assert dummy.font_family == "Arial"

    def test_dummy_exposes_font_size(self) -> None:
        """Test that dummy exposes font_size from config."""
        config = TextWindowConfig(font_size=24)
        dummy = _TextRenderDummy(config)
        assert dummy.font_size == 24

    def test_dummy_exposes_colors(self) -> None:
        """Test that dummy exposes color properties."""
        config = TextWindowConfig(font_color="#ff0000", background_color="#00ff00")
        dummy = _TextRenderDummy(config)
        assert dummy.font_color == "#ff0000"
        assert dummy.background_color == "#00ff00"

    def test_dummy_pos_returns_qpoint(self) -> None:
        """Test that dummy.pos() returns origin point."""
        config = TextWindowConfig()
        dummy = _TextRenderDummy(config)
        pos = dummy.pos()
        assert pos.x() == 0
        assert pos.y() == 0

    def test_dummy_shadow_properties(self) -> None:
        """Test shadow-related properties."""
        config = TextWindowConfig(
            shadow_enabled=True,
            shadow_blur=5,
            shadow_offset_x=2,
            shadow_offset_y=3,
        )
        dummy = _TextRenderDummy(config)
        assert dummy.shadow_enabled is True
        assert dummy.shadow_blur == 5
        assert dummy.shadow_offset_x == 2
        assert dummy.shadow_offset_y == 3

    def test_dummy_outline_properties(self) -> None:
        """Test outline-related properties."""
        config = TextWindowConfig(
            outline_enabled=True,
            outline_width=2.0,
        )
        dummy = _TextRenderDummy(config)
        assert dummy.outline_enabled is True
        assert dummy.outline_width == 2.0

    def test_dummy_text_gradient_properties(self) -> None:
        """Test text gradient properties."""
        config = TextWindowConfig(
            text_gradient_enabled=True,
            text_gradient_opacity=80,
        )
        dummy = _TextRenderDummy(config)
        assert dummy.text_gradient_enabled is True
        assert dummy.text_gradient_opacity == 80

    def test_dummy_vertical_mode(self) -> None:
        """Test vertical text mode property."""
        config = TextWindowConfig(is_vertical=True)
        dummy = _TextRenderDummy(config)
        assert dummy.is_vertical is True
