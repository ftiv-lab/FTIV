# -*- coding: utf-8 -*-
"""SpacingManager の未カバーパス拡張テスト (Sprint 2)."""

from unittest.mock import MagicMock

import pytest

from managers.spacing_manager import SpacingManager
from models.spacing_settings import (
    DEFAULT_CHAR_SPACING,
    DEFAULT_MARGIN_TOP,
    DEFAULT_V_MARGIN_TOP,
    HorizontalSpacing,
    SpacingSettings,
    VerticalSpacing,
)


@pytest.fixture
def mock_window():
    """TextWindow互換のMock。"""
    w = MagicMock()
    w.config = MagicMock()
    w.config.horizontal_margin_ratio = 1.0
    w.config.vertical_margin_ratio = 2.0
    w.config.margin_top = 0.1
    w.config.margin_bottom = 0.2
    w.config.margin_left = 0.3
    w.config.margin_right = 0.4
    w.config.v_margin_top = 0.5
    w.config.v_margin_bottom = 0.6
    w.config.v_margin_left = 0.7
    w.config.v_margin_right = 0.8
    return w


class TestExtractFromWindow:
    def test_extract_returns_correct_values(self, mock_window):
        result = SpacingManager.extract_from_window(mock_window)
        assert result.horizontal.char_spacing == 1.0
        assert result.horizontal.line_spacing == 2.0
        assert result.horizontal.margin_top == 0.1

    def test_extract_with_no_config_returns_defaults(self):
        w = MagicMock(spec=[])  # configなし
        w.config = None
        result = SpacingManager.extract_from_window(w)
        assert result.horizontal.char_spacing == DEFAULT_CHAR_SPACING

    def test_extract_vertical_margins(self, mock_window):
        result = SpacingManager.extract_from_window(mock_window)
        assert result.vertical.margin_top == 0.5
        assert result.vertical.margin_bottom == 0.6


class TestApplyToWindow:
    def test_apply_calls_set_undoable_property(self):
        w = MagicMock()
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        )
        SpacingManager.apply_to_window(w, settings, use_undo=True)
        assert w.set_undoable_property.call_count > 0
        w.update_text.assert_called_once()

    def test_apply_without_undo_uses_setattr(self):
        w = MagicMock()
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        )
        SpacingManager.apply_to_window(w, settings, use_undo=False)
        w.set_undoable_property.assert_not_called()
        w.update_text.assert_called_once()


class TestApplyHorizontalOnly:
    def test_apply_horizontal_sets_6_properties(self):
        w = MagicMock()
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        )
        SpacingManager.apply_horizontal_only(w, settings, use_undo=True)
        assert w.set_undoable_property.call_count == 6
        w.update_text.assert_called_once()

    def test_apply_horizontal_without_undo(self):
        w = MagicMock()
        settings = SpacingSettings()
        SpacingManager.apply_horizontal_only(w, settings, use_undo=False)
        w.set_undoable_property.assert_not_called()
        w.update_text.assert_called_once()


class TestApplyVerticalOnly:
    def test_apply_vertical_sets_4_properties(self):
        w = MagicMock()
        settings = SpacingSettings(
            vertical=VerticalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        )
        SpacingManager.apply_vertical_only(w, settings, use_undo=True)
        assert w.set_undoable_property.call_count == 4
        w.update_text.assert_called_once()

    def test_apply_vertical_without_undo(self):
        w = MagicMock()
        settings = SpacingSettings()
        SpacingManager.apply_vertical_only(w, settings, use_undo=False)
        w.set_undoable_property.assert_not_called()
        w.update_text.assert_called_once()


class TestValidateSpacingValue:
    def test_clamps_spacing_below_min(self):
        assert SpacingManager.validate_spacing_value(-1.0) == SpacingManager.MIN_SPACING

    def test_clamps_spacing_above_max(self):
        assert SpacingManager.validate_spacing_value(10.0) == SpacingManager.MAX_SPACING

    def test_spacing_in_range_unchanged(self):
        assert SpacingManager.validate_spacing_value(0.5) == 0.5

    def test_margin_clamps_below_zero(self):
        assert SpacingManager.validate_spacing_value(-1.0, is_margin=True) == SpacingManager.MIN_MARGIN

    def test_margin_clamps_above_max(self):
        assert SpacingManager.validate_spacing_value(10.0, is_margin=True) == SpacingManager.MAX_MARGIN

    def test_margin_in_range_unchanged(self):
        assert SpacingManager.validate_spacing_value(2.5, is_margin=True) == 2.5


class TestValidateSettings:
    def test_clamps_out_of_range_values(self):
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(
                char_spacing=-10.0,  # below MIN_SPACING
                line_spacing=100.0,  # above MAX_MARGIN
                margin_top=-5.0,  # below MIN_MARGIN
                margin_bottom=0.0,
                margin_left=0.0,
                margin_right=0.0,
            ),
        )
        validated = SpacingManager.validate_settings(settings)
        assert validated.horizontal.char_spacing == SpacingManager.MIN_SPACING
        assert validated.horizontal.line_spacing == SpacingManager.MAX_MARGIN
        assert validated.horizontal.margin_top == SpacingManager.MIN_MARGIN

    def test_valid_values_unchanged(self):
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
            vertical=VerticalSpacing(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
        )
        validated = SpacingManager.validate_settings(settings)
        assert validated.horizontal.char_spacing == 0.1
        assert validated.vertical.char_spacing == 0.1


class TestDialogTupleToLegacyDict:
    def test_converts_correctly(self):
        values = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        result = SpacingManager.dialog_tuple_to_legacy_dict(values)
        assert result["horizontal_margin_ratio"] == 1.0
        assert result["vertical_margin_ratio"] == 2.0
        assert result["margin_top_ratio"] == 3.0
        assert result["margin_bottom_ratio"] == 4.0
        assert result["margin_left_ratio"] == 5.0
        assert result["margin_right_ratio"] == 6.0


class TestGetDefaultsForMode:
    def test_horizontal_defaults(self):
        result = SpacingManager.get_defaults_for_mode(is_vertical=False)
        assert len(result) == 6
        assert result[0] == DEFAULT_CHAR_SPACING
        assert result[2] == DEFAULT_MARGIN_TOP

    def test_vertical_defaults(self):
        result = SpacingManager.get_defaults_for_mode(is_vertical=True)
        assert len(result) == 6
        assert result[0] == DEFAULT_CHAR_SPACING
        assert result[2] == DEFAULT_V_MARGIN_TOP
