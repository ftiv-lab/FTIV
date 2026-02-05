# models/spacing_settings.py
"""
SpacingSettings dataclass for unified spacing management.

This module provides a clean abstraction for text window spacing settings,
separating horizontal and vertical text mode configurations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

# Default values as constants (Single Source of Truth)
DEFAULT_CHAR_SPACING = 0.0
DEFAULT_LINE_SPACING = 0.2
DEFAULT_MARGIN_TOP = 0.0
DEFAULT_MARGIN_BOTTOM = 0.0
DEFAULT_MARGIN_LEFT = 0.3
DEFAULT_MARGIN_RIGHT = 0.0

# Vertical mode has different defaults for better typography
DEFAULT_V_CHAR_SPACING = 0.0
DEFAULT_V_LINE_SPACING = 0.2
DEFAULT_V_MARGIN_TOP = 0.3
DEFAULT_V_MARGIN_BOTTOM = 0.0
DEFAULT_V_MARGIN_LEFT = 0.0
DEFAULT_V_MARGIN_RIGHT = 0.0


@dataclass
class HorizontalSpacing:
    """Spacing settings for horizontal text mode."""

    char_spacing: float = DEFAULT_CHAR_SPACING
    line_spacing: float = DEFAULT_LINE_SPACING
    margin_top: float = DEFAULT_MARGIN_TOP
    margin_bottom: float = DEFAULT_MARGIN_BOTTOM
    margin_left: float = DEFAULT_MARGIN_LEFT
    margin_right: float = DEFAULT_MARGIN_RIGHT

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "char_spacing": self.char_spacing,
            "line_spacing": self.line_spacing,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HorizontalSpacing":
        """Create from dictionary."""
        return cls(
            char_spacing=float(data.get("char_spacing", DEFAULT_CHAR_SPACING)),
            line_spacing=float(data.get("line_spacing", DEFAULT_LINE_SPACING)),
            margin_top=float(data.get("margin_top", DEFAULT_MARGIN_TOP)),
            margin_bottom=float(data.get("margin_bottom", DEFAULT_MARGIN_BOTTOM)),
            margin_left=float(data.get("margin_left", DEFAULT_MARGIN_LEFT)),
            margin_right=float(data.get("margin_right", DEFAULT_MARGIN_RIGHT)),
        )


@dataclass
class VerticalSpacing:
    """Spacing settings for vertical text mode."""

    char_spacing: float = DEFAULT_V_CHAR_SPACING
    line_spacing: float = DEFAULT_V_LINE_SPACING
    margin_top: float = DEFAULT_V_MARGIN_TOP
    margin_bottom: float = DEFAULT_V_MARGIN_BOTTOM
    margin_left: float = DEFAULT_V_MARGIN_LEFT
    margin_right: float = DEFAULT_V_MARGIN_RIGHT

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "char_spacing": self.char_spacing,
            "line_spacing": self.line_spacing,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerticalSpacing":
        """Create from dictionary."""
        return cls(
            char_spacing=float(data.get("char_spacing", DEFAULT_V_CHAR_SPACING)),
            line_spacing=float(data.get("line_spacing", DEFAULT_V_LINE_SPACING)),
            margin_top=float(data.get("margin_top", DEFAULT_V_MARGIN_TOP)),
            margin_bottom=float(data.get("margin_bottom", DEFAULT_V_MARGIN_BOTTOM)),
            margin_left=float(data.get("margin_left", DEFAULT_V_MARGIN_LEFT)),
            margin_right=float(data.get("margin_right", DEFAULT_V_MARGIN_RIGHT)),
        )


@dataclass
class SpacingSettings:
    """
    Unified spacing settings for TextWindow.

    Maintains separate configurations for horizontal and vertical text modes,
    providing a clean interface for the spacing dialog and TextRenderer.
    """

    horizontal: HorizontalSpacing = field(default_factory=HorizontalSpacing)
    vertical: VerticalSpacing = field(default_factory=VerticalSpacing)

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        """Convert to dictionary for serialization."""
        return {
            "horizontal": self.horizontal.to_dict(),
            "vertical": self.vertical.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpacingSettings":
        """Create from dictionary."""
        h_data = data.get("horizontal", {})
        v_data = data.get("vertical", {})
        return cls(
            horizontal=HorizontalSpacing.from_dict(h_data),
            vertical=VerticalSpacing.from_dict(v_data),
        )

    @classmethod
    def from_legacy_config(
        cls,
        horizontal_margin_ratio: float = DEFAULT_CHAR_SPACING,
        vertical_margin_ratio: float = DEFAULT_LINE_SPACING,
        margin_top: float = DEFAULT_MARGIN_TOP,
        margin_bottom: float = DEFAULT_MARGIN_BOTTOM,
        margin_left: float = DEFAULT_MARGIN_LEFT,
        margin_right: float = DEFAULT_MARGIN_RIGHT,
        v_margin_top: Optional[float] = None,
        v_margin_bottom: Optional[float] = None,
        v_margin_left: Optional[float] = None,
        v_margin_right: Optional[float] = None,
    ) -> "SpacingSettings":
        """
        Create SpacingSettings from legacy TextWindowConfig fields.

        This method provides backward compatibility by mapping old field names
        to the new structure.

        Args:
            horizontal_margin_ratio: Old name for horizontal char spacing
            vertical_margin_ratio: Old name for vertical line spacing (confusing!)
            margin_top/bottom/left/right: Horizontal mode margins
            v_margin_*: Vertical mode specific margins (new fields)
        """
        return cls(
            horizontal=HorizontalSpacing(
                char_spacing=horizontal_margin_ratio,
                line_spacing=vertical_margin_ratio,
                margin_top=margin_top,
                margin_bottom=margin_bottom,
                margin_left=margin_left,
                margin_right=margin_right,
            ),
            vertical=VerticalSpacing(
                char_spacing=v_margin_top if v_margin_top is not None else DEFAULT_V_CHAR_SPACING,
                line_spacing=vertical_margin_ratio,
                margin_top=v_margin_top if v_margin_top is not None else DEFAULT_V_MARGIN_TOP,
                margin_bottom=v_margin_bottom if v_margin_bottom is not None else DEFAULT_V_MARGIN_BOTTOM,
                margin_left=v_margin_left if v_margin_left is not None else DEFAULT_V_MARGIN_LEFT,
                margin_right=v_margin_right if v_margin_right is not None else DEFAULT_V_MARGIN_RIGHT,
            ),
        )

    def to_legacy_dict(self) -> Dict[str, float]:
        """
        Convert to legacy TextWindowConfig field names for backward compatibility.

        Returns dict with old field names that can be applied to TextWindow.
        """
        return {
            "horizontal_margin_ratio": self.horizontal.char_spacing,
            "vertical_margin_ratio": self.horizontal.line_spacing,
            "margin_top_ratio": self.horizontal.margin_top,
            "margin_bottom_ratio": self.horizontal.margin_bottom,
            "margin_left_ratio": self.horizontal.margin_left,
            "margin_right_ratio": self.horizontal.margin_right,
            # Vertical-specific (new fields)
            "v_margin_top_ratio": self.vertical.margin_top,
            "v_margin_bottom_ratio": self.vertical.margin_bottom,
            "v_margin_left_ratio": self.vertical.margin_left,
            "v_margin_right_ratio": self.vertical.margin_right,
        }

    def get_active_spacing(self, is_vertical: bool) -> HorizontalSpacing | VerticalSpacing:
        """Get the appropriate spacing settings based on text direction."""
        return self.vertical if is_vertical else self.horizontal

    @classmethod
    def from_dialog_tuple(
        cls,
        values: Tuple[float, float, float, float, float, float],
        is_vertical: bool = False,
    ) -> "SpacingSettings":
        """
        Create SpacingSettings from TextSpacingDialog.get_values() tuple.

        Args:
            values: Tuple of (h_ratio, v_ratio, top, bottom, left, right)
            is_vertical: Whether the current mode is vertical text
        """
        h_ratio, v_ratio, top, bottom, left, right = values

        if is_vertical:
            # In vertical mode, dialog edits vertical spacing
            return cls(
                horizontal=HorizontalSpacing(),  # Keep defaults
                vertical=VerticalSpacing(
                    char_spacing=h_ratio,
                    line_spacing=v_ratio,
                    margin_top=top,
                    margin_bottom=bottom,
                    margin_left=left,
                    margin_right=right,
                ),
            )
        else:
            # In horizontal mode, dialog edits horizontal spacing
            return cls(
                horizontal=HorizontalSpacing(
                    char_spacing=h_ratio,
                    line_spacing=v_ratio,
                    margin_top=top,
                    margin_bottom=bottom,
                    margin_left=left,
                    margin_right=right,
                ),
                vertical=VerticalSpacing(),  # Keep defaults
            )

    def to_dialog_tuple(self, is_vertical: bool) -> Tuple[float, float, float, float, float, float]:
        """
        Convert to tuple format for TextSpacingDialog initialization.

        Returns: (h_ratio, v_ratio, top, bottom, left, right)
        """
        spacing = self.get_active_spacing(is_vertical)
        return (
            spacing.char_spacing,
            spacing.line_spacing,
            spacing.margin_top,
            spacing.margin_bottom,
            spacing.margin_left,
            spacing.margin_right,
        )
