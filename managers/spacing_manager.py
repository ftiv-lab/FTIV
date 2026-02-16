# -*- coding: utf-8 -*-
"""
SpacingManager - Unified spacing settings management for TextWindow.

This manager handles the coordination between SpacingSettings, TextWindowConfig,
and the TextSpacingDialog, providing a clean interface for spacing operations.
"""

import logging
from typing import TYPE_CHECKING, Dict, Tuple

from models.protocols import TextConfigurable
from models.spacing_settings import (
    DEFAULT_CHAR_SPACING,
    DEFAULT_LINE_SPACING,
    DEFAULT_MARGIN_BOTTOM,
    DEFAULT_MARGIN_LEFT,
    DEFAULT_MARGIN_RIGHT,
    DEFAULT_MARGIN_TOP,
    DEFAULT_V_MARGIN_BOTTOM,
    DEFAULT_V_MARGIN_LEFT,
    DEFAULT_V_MARGIN_RIGHT,
    DEFAULT_V_MARGIN_TOP,
    SpacingSettings,
)

if TYPE_CHECKING:
    from windows.text_window import TextWindow

logger = logging.getLogger(__name__)


class SpacingManager:
    """
    Manager for TextWindow spacing settings.

    Provides methods to:
    - Extract SpacingSettings from a TextWindow
    - Apply SpacingSettings to a TextWindow (with undo support)
    - Convert between dialog tuples and SpacingSettings
    - Validate spacing values
    """

    # Validation constants
    MIN_SPACING = -0.5
    MAX_SPACING = 5.0
    MIN_MARGIN = 0.0
    MAX_MARGIN = 5.0

    @staticmethod
    def extract_from_window(window: "TextWindow") -> SpacingSettings:
        """
        Extract current spacing settings from a TextWindow.

        Args:
            window: The TextWindow to extract settings from

        Returns:
            SpacingSettings populated from the window's current state
        """
        cfg = getattr(window, "config", None)
        if cfg is None:
            return SpacingSettings()

        return SpacingSettings.from_window_config_fields(
            horizontal_margin_ratio=getattr(cfg, "horizontal_margin_ratio", DEFAULT_CHAR_SPACING),
            vertical_margin_ratio=getattr(cfg, "vertical_margin_ratio", DEFAULT_LINE_SPACING),
            margin_top=getattr(cfg, "margin_top", DEFAULT_MARGIN_TOP),
            margin_bottom=getattr(cfg, "margin_bottom", DEFAULT_MARGIN_BOTTOM),
            margin_left=getattr(cfg, "margin_left", DEFAULT_MARGIN_LEFT),
            margin_right=getattr(cfg, "margin_right", DEFAULT_MARGIN_RIGHT),
            # Vertical-specific margins (new fields, may not exist)
            v_margin_top=getattr(cfg, "v_margin_top", None),
            v_margin_bottom=getattr(cfg, "v_margin_bottom", None),
            v_margin_left=getattr(cfg, "v_margin_left", None),
            v_margin_right=getattr(cfg, "v_margin_right", None),
        )

    @staticmethod
    def apply_to_window(
        window: "TextConfigurable",
        settings: SpacingSettings,
        use_undo: bool = True,
    ) -> None:
        """
        Apply SpacingSettings to a TextWindow.

        Args:
            window: The TextWindow to apply settings to
            settings: The SpacingSettings to apply
            use_undo: Whether to use undo stack (default True)
        """
        bridge_values = settings.to_window_config_dict()

        for prop_name, value in bridge_values.items():
            try:
                # FAIL FAST: We assume window confirms to UndoableConfigurable
                if use_undo:
                    window.set_undoable_property(prop_name, value, "update_text")
                else:
                    # Direct set for cases where undo is not needed
                    setattr(window, prop_name, value)
            except Exception as e:
                # Still catch runtime errors, but NOT AttributeError for missing method
                logger.warning(f"Failed to set {prop_name}: {e}")

        # Trigger update
        window.update_text()

    @staticmethod
    def apply_horizontal_only(
        window: "TextConfigurable",
        settings: SpacingSettings,
        use_undo: bool = True,
    ) -> None:
        """Apply only horizontal spacing settings (for horizontal text mode)."""
        h = settings.horizontal
        props = {
            "horizontal_margin_ratio": h.char_spacing,
            "vertical_margin_ratio": h.line_spacing,
            "margin_top_ratio": h.margin_top,
            "margin_bottom_ratio": h.margin_bottom,
            "margin_left_ratio": h.margin_left,
            "margin_right_ratio": h.margin_right,
        }

        for prop_name, value in props.items():
            try:
                if use_undo:
                    window.set_undoable_property(prop_name, value, "update_text")
                else:
                    setattr(window, prop_name, value)
            except Exception as e:
                logger.warning(f"Failed to set {prop_name}: {e}")

        window.update_text()

    @staticmethod
    def apply_vertical_only(
        window: "TextConfigurable",
        settings: SpacingSettings,
        use_undo: bool = True,
    ) -> None:
        """Apply only vertical spacing settings (for vertical text mode)."""
        v = settings.vertical
        props = {
            "v_margin_top_ratio": v.margin_top,
            "v_margin_bottom_ratio": v.margin_bottom,
            "v_margin_left_ratio": v.margin_left,
            "v_margin_right_ratio": v.margin_right,
        }

        for prop_name, value in props.items():
            try:
                if use_undo:
                    window.set_undoable_property(prop_name, value, "update_text")
                else:
                    setattr(window, prop_name, value)
            except Exception as e:
                logger.warning(f"Failed to set {prop_name}: {e}")

        window.update_text()

    @classmethod
    def validate_spacing_value(cls, value: float, is_margin: bool = False) -> float:
        """
        Validate and clamp a spacing value to acceptable range.

        Args:
            value: The value to validate
            is_margin: True if this is a margin value (non-negative)

        Returns:
            Clamped value within acceptable range
        """
        if is_margin:
            return max(cls.MIN_MARGIN, min(cls.MAX_MARGIN, value))
        return max(cls.MIN_SPACING, min(cls.MAX_SPACING, value))

    @classmethod
    def validate_settings(cls, settings: SpacingSettings) -> SpacingSettings:
        """
        Validate and clamp all values in SpacingSettings.

        Returns a new SpacingSettings with all values clamped to acceptable ranges.
        """
        from models.spacing_settings import HorizontalSpacing, VerticalSpacing

        h = settings.horizontal
        v = settings.vertical

        return SpacingSettings(
            horizontal=HorizontalSpacing(
                char_spacing=cls.validate_spacing_value(h.char_spacing, is_margin=False),
                line_spacing=cls.validate_spacing_value(h.line_spacing, is_margin=True),
                margin_top=cls.validate_spacing_value(h.margin_top, is_margin=True),
                margin_bottom=cls.validate_spacing_value(h.margin_bottom, is_margin=True),
                margin_left=cls.validate_spacing_value(h.margin_left, is_margin=True),
                margin_right=cls.validate_spacing_value(h.margin_right, is_margin=True),
            ),
            vertical=VerticalSpacing(
                char_spacing=cls.validate_spacing_value(v.char_spacing, is_margin=False),
                line_spacing=cls.validate_spacing_value(v.line_spacing, is_margin=True),
                margin_top=cls.validate_spacing_value(v.margin_top, is_margin=True),
                margin_bottom=cls.validate_spacing_value(v.margin_bottom, is_margin=True),
                margin_left=cls.validate_spacing_value(v.margin_left, is_margin=True),
                margin_right=cls.validate_spacing_value(v.margin_right, is_margin=True),
            ),
        )

    @staticmethod
    def dialog_tuple_to_window_config_dict(
        values: Tuple[float, float, float, float, float, float],
    ) -> Dict[str, float]:
        """
        Convert dialog tuple to TextWindowConfig property names.

        This is the preferred method for callers that need to apply spacing
        from dialog results.

        Args:
            values: Tuple from TextSpacingDialog.get_values()
                   (h_ratio, v_ratio, top, bottom, left, right)

        Returns:
            Dict with TextWindow property names as keys
        """
        h_ratio, v_ratio, top, bottom, left, right = values
        return {
            "horizontal_margin_ratio": h_ratio,
            "vertical_margin_ratio": v_ratio,
            "margin_top_ratio": top,
            "margin_bottom_ratio": bottom,
            "margin_left_ratio": left,
            "margin_right_ratio": right,
        }

    @staticmethod
    def dialog_tuple_to_legacy_dict(
        values: Tuple[float, float, float, float, float, float],
    ) -> Dict[str, float]:
        """
        Deprecated compatibility alias.

        Prefer `dialog_tuple_to_window_config_dict`.
        """
        return SpacingManager.dialog_tuple_to_window_config_dict(values)

    @staticmethod
    def get_defaults_for_mode(is_vertical: bool) -> Tuple[float, float, float, float, float, float]:
        """
        Get default spacing values for a text mode.

        Returns tuple suitable for TextSpacingDialog initialization.
        """
        if is_vertical:
            return (
                DEFAULT_CHAR_SPACING,
                DEFAULT_LINE_SPACING,
                DEFAULT_V_MARGIN_TOP,
                DEFAULT_V_MARGIN_BOTTOM,
                DEFAULT_V_MARGIN_LEFT,
                DEFAULT_V_MARGIN_RIGHT,
            )
        else:
            return (
                DEFAULT_CHAR_SPACING,
                DEFAULT_LINE_SPACING,
                DEFAULT_MARGIN_TOP,
                DEFAULT_MARGIN_BOTTOM,
                DEFAULT_MARGIN_LEFT,
                DEFAULT_MARGIN_RIGHT,
            )
