# -*- coding: utf-8 -*-
"""models/ 層の未カバーモジュール完走テスト。

Sprint 1: app_mode, window_layer のEnum網羅 + spacing_settings の未カバーパス。
"""

from models.app_mode import AppMode
from models.spacing_settings import (
    DEFAULT_CHAR_SPACING,
    DEFAULT_LINE_SPACING,
    DEFAULT_V_CHAR_SPACING,
    DEFAULT_V_MARGIN_BOTTOM,
    DEFAULT_V_MARGIN_LEFT,
    DEFAULT_V_MARGIN_RIGHT,
    DEFAULT_V_MARGIN_TOP,
    HorizontalSpacing,
    SpacingSettings,
    VerticalSpacing,
)
from models.window_layer import WindowLayer


class TestAppMode:
    """AppMode Enum の全値テスト。"""

    def test_desktop_mode_exists(self) -> None:
        assert AppMode.DESKTOP is not None

    def test_mind_map_mode_exists(self) -> None:
        assert AppMode.MIND_MAP is not None

    def test_values_are_distinct(self) -> None:
        assert AppMode.DESKTOP != AppMode.MIND_MAP

    def test_enum_member_count(self) -> None:
        assert len(AppMode) == 2

    def test_enum_is_iterable(self) -> None:
        members = list(AppMode)
        assert AppMode.DESKTOP in members
        assert AppMode.MIND_MAP in members


class TestWindowLayer:
    """WindowLayer Enum の全値テスト。"""

    def test_desktop_layer_exists(self) -> None:
        assert WindowLayer.DESKTOP is not None

    def test_mind_map_layer_exists(self) -> None:
        assert WindowLayer.MIND_MAP is not None

    def test_values_are_distinct(self) -> None:
        assert WindowLayer.DESKTOP != WindowLayer.MIND_MAP

    def test_enum_member_count(self) -> None:
        assert len(WindowLayer) == 2


class TestSpacingSettingsFromDialogTuple:
    """SpacingSettings.from_dialog_tuple の水平/垂直パスをカバー。"""

    def test_from_dialog_tuple_horizontal(self) -> None:
        values = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        settings = SpacingSettings.from_dialog_tuple(values, is_vertical=False)
        assert settings.horizontal.char_spacing == 1.0
        assert settings.horizontal.line_spacing == 2.0
        assert settings.horizontal.margin_top == 3.0
        assert settings.horizontal.margin_bottom == 4.0
        assert settings.horizontal.margin_left == 5.0
        assert settings.horizontal.margin_right == 6.0
        # 垂直はデフォルトのまま
        assert settings.vertical.char_spacing == DEFAULT_V_CHAR_SPACING

    def test_from_dialog_tuple_vertical(self) -> None:
        values = (1.5, 2.5, 3.5, 4.5, 5.5, 6.5)
        settings = SpacingSettings.from_dialog_tuple(values, is_vertical=True)
        assert settings.vertical.char_spacing == 1.5
        assert settings.vertical.line_spacing == 2.5
        assert settings.vertical.margin_top == 3.5
        assert settings.vertical.margin_bottom == 4.5
        assert settings.vertical.margin_left == 5.5
        assert settings.vertical.margin_right == 6.5
        # 水平はデフォルトのまま
        assert settings.horizontal.char_spacing == DEFAULT_CHAR_SPACING


class TestSpacingSettingsToDialogTuple:
    """to_dialog_tuple の水平/垂直パス。"""

    def test_to_dialog_tuple_horizontal(self) -> None:
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        )
        result = settings.to_dialog_tuple(is_vertical=False)
        assert result == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

    def test_to_dialog_tuple_vertical(self) -> None:
        settings = SpacingSettings(
            vertical=VerticalSpacing(10.0, 20.0, 30.0, 40.0, 50.0, 60.0),
        )
        result = settings.to_dialog_tuple(is_vertical=True)
        assert result == (10.0, 20.0, 30.0, 40.0, 50.0, 60.0)


class TestSpacingSettingsGetActiveSpacing:
    """get_active_spacing のモード切替テスト。"""

    def test_active_spacing_horizontal(self) -> None:
        h = HorizontalSpacing(char_spacing=99.0)
        v = VerticalSpacing(char_spacing=1.0)
        settings = SpacingSettings(horizontal=h, vertical=v)
        active = settings.get_active_spacing(is_vertical=False)
        assert active.char_spacing == 99.0

    def test_active_spacing_vertical(self) -> None:
        h = HorizontalSpacing(char_spacing=1.0)
        v = VerticalSpacing(char_spacing=99.0)
        settings = SpacingSettings(horizontal=h, vertical=v)
        active = settings.get_active_spacing(is_vertical=True)
        assert active.char_spacing == 99.0


class TestSpacingSettingsToWindowConfigDict:
    """to_window_config_dict のフィールドマッピング検証。"""

    def test_window_config_dict_contains_all_keys(self) -> None:
        settings = SpacingSettings(
            horizontal=HorizontalSpacing(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
            vertical=VerticalSpacing(10.0, 20.0, 30.0, 40.0, 50.0, 60.0),
        )
        d = settings.to_window_config_dict()
        assert d["horizontal_margin_ratio"] == 1.0
        assert d["vertical_margin_ratio"] == 2.0
        assert d["margin_top_ratio"] == 3.0
        assert d["margin_bottom_ratio"] == 4.0
        assert d["margin_left_ratio"] == 5.0
        assert d["margin_right_ratio"] == 6.0
        assert d["v_margin_top_ratio"] == 30.0
        assert d["v_margin_bottom_ratio"] == 40.0
        assert d["v_margin_left_ratio"] == 50.0
        assert d["v_margin_right_ratio"] == 60.0


class TestSpacingSettingsFromWindowConfigFields:
    """from_window_config_fields の各パスをカバー。"""

    def test_from_window_config_with_defaults(self) -> None:
        settings = SpacingSettings.from_window_config_fields()
        assert settings.horizontal.char_spacing == DEFAULT_CHAR_SPACING
        assert settings.horizontal.line_spacing == DEFAULT_LINE_SPACING
        assert settings.vertical.margin_top == DEFAULT_V_MARGIN_TOP

    def test_from_window_config_with_vertical_margins(self) -> None:
        settings = SpacingSettings.from_window_config_fields(
            horizontal_margin_ratio=1.0,
            vertical_margin_ratio=2.0,
            margin_top=3.0,
            margin_bottom=4.0,
            margin_left=5.0,
            margin_right=6.0,
            v_margin_top=10.0,
            v_margin_bottom=20.0,
            v_margin_left=30.0,
            v_margin_right=40.0,
        )
        assert settings.horizontal.char_spacing == 1.0
        assert settings.horizontal.line_spacing == 2.0
        assert settings.vertical.margin_top == 10.0
        assert settings.vertical.margin_bottom == 20.0
        assert settings.vertical.margin_left == 30.0
        assert settings.vertical.margin_right == 40.0
        assert settings.vertical.char_spacing == DEFAULT_V_CHAR_SPACING
        assert settings.vertical.line_spacing == 2.0

    def test_from_window_config_without_vertical_uses_defaults(self) -> None:
        settings = SpacingSettings.from_window_config_fields(
            horizontal_margin_ratio=5.0,
            vertical_margin_ratio=6.0,
        )
        assert settings.horizontal.char_spacing == 5.0
        assert settings.vertical.margin_top == DEFAULT_V_MARGIN_TOP
        assert settings.vertical.margin_bottom == DEFAULT_V_MARGIN_BOTTOM
        assert settings.vertical.margin_left == DEFAULT_V_MARGIN_LEFT
        assert settings.vertical.margin_right == DEFAULT_V_MARGIN_RIGHT

    def test_from_window_config_prefers_explicit_vertical_spacing_fields(self) -> None:
        settings = SpacingSettings.from_window_config_fields(
            vertical_margin_ratio=1.5,
            char_spacing_v=2.5,
            line_spacing_v=3.5,
        )
        assert settings.vertical.char_spacing == 2.5
        assert settings.vertical.line_spacing == 3.5
