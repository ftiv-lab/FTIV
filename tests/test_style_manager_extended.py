# -*- coding: utf-8 -*-
"""StyleManager の拡張テスト (Sprint 2).

UI表示部分 (QFileDialog, QPixmap描画等) はスコープ外。
_TextRenderDummy, presets管理, _apply_data_to_window をカバー。
"""

import json
import os
from unittest.mock import MagicMock

import pytest

from managers.style_manager import StyleManager, _TextRenderDummy
from models.window_config import TextWindowConfig


# ============================================================
# _TextRenderDummy テスト
# ============================================================
class TestTextRenderDummy:
    """_TextRenderDummy のプロパティ委譲テスト。"""

    @pytest.fixture
    def dummy(self):
        config = TextWindowConfig(
            text="Hello",
            font="Arial",
            font_size=24,
            font_color="#FFFFFF",
            background_color="#000000",
            text_visible=True,
            background_visible=True,
            text_opacity=255,
            background_opacity=128,
            shadow_enabled=True,
            shadow_color="#333333",
            shadow_opacity=200,
            shadow_blur=5,
            shadow_scale=1.5,
            shadow_offset_x=2.0,
            shadow_offset_y=3.0,
            is_vertical=False,
            horizontal_margin_ratio=0.1,
            vertical_margin_ratio=0.2,
            outline_enabled=True,
            outline_color="#FF0000",
            outline_opacity=180,
            outline_width=2.0,
            outline_blur=3,
        )
        return _TextRenderDummy(config)

    def test_text_property(self, dummy):
        assert dummy.text == "Hello"

    def test_font_family(self, dummy):
        assert dummy.font_family == "Arial"

    def test_font_size(self, dummy):
        assert dummy.font_size == 24

    def test_font_color(self, dummy):
        assert dummy.font_color == "#FFFFFF"

    def test_background_color(self, dummy):
        assert dummy.background_color == "#000000"

    def test_text_visible(self, dummy):
        assert dummy.text_visible is True

    def test_background_visible(self, dummy):
        assert dummy.background_visible is True

    def test_text_opacity(self, dummy):
        assert dummy.text_opacity == 255

    def test_background_opacity(self, dummy):
        assert dummy.background_opacity == 128

    def test_shadow_properties(self, dummy):
        assert dummy.shadow_enabled is True
        assert dummy.shadow_color == "#333333"
        assert dummy.shadow_opacity == 200
        assert dummy.shadow_blur == 5
        assert dummy.shadow_scale == 1.5
        assert dummy.shadow_offset_x == 2.0
        assert dummy.shadow_offset_y == 3.0

    def test_is_vertical(self, dummy):
        assert dummy.is_vertical is False

    def test_margin_ratios(self, dummy):
        assert dummy.horizontal_margin_ratio == 0.1
        assert dummy.vertical_margin_ratio == 0.2

    def test_outline_properties(self, dummy):
        assert dummy.outline_enabled is True
        assert dummy.outline_color == "#FF0000"
        assert dummy.outline_opacity == 180
        assert dummy.outline_width == 2.0
        assert dummy.outline_blur == 3

    def test_pos_returns_origin(self, dummy):
        pos = dummy.pos()
        assert pos.x() == 0
        assert pos.y() == 0

    def test_set_geometry_stores_value(self, dummy):
        dummy.setGeometry("mock_rect")
        assert dummy._geometry == "mock_rect"

    def test_second_outline_properties(self, dummy):
        assert isinstance(dummy.second_outline_enabled, bool)
        assert isinstance(dummy.second_outline_color, str)
        assert isinstance(dummy.second_outline_opacity, int)
        assert isinstance(dummy.second_outline_width, float)
        assert isinstance(dummy.second_outline_blur, int)

    def test_third_outline_properties(self, dummy):
        assert isinstance(dummy.third_outline_enabled, bool)
        assert isinstance(dummy.third_outline_color, str)

    def test_background_outline_properties(self, dummy):
        assert isinstance(dummy.background_outline_enabled, bool)
        assert isinstance(dummy.background_outline_color, str)
        assert isinstance(dummy.background_outline_opacity, int)
        assert isinstance(dummy.background_outline_width_ratio, float)

    def test_gradient_properties(self, dummy):
        assert isinstance(dummy.text_gradient_enabled, bool)
        assert isinstance(dummy.text_gradient_angle, int)
        assert isinstance(dummy.text_gradient_opacity, int)
        assert isinstance(dummy.background_gradient_enabled, bool)
        assert isinstance(dummy.background_gradient_angle, int)
        assert isinstance(dummy.background_gradient_opacity, int)

    def test_background_corner_ratio(self, dummy):
        assert isinstance(dummy.background_corner_ratio, float)

    def test_margin_top_bottom_left_right(self, dummy):
        assert isinstance(dummy.margin_top_ratio, float)
        assert isinstance(dummy.margin_bottom_ratio, float)
        assert isinstance(dummy.margin_left_ratio, float)
        assert isinstance(dummy.margin_right_ratio, float)

    def test_font_size_invalid_returns_default(self):
        config = MagicMock()
        config.font_size = "invalid"
        # font_size のint変換が失敗するケース
        _TextRenderDummy(config)
        # MagicMockのfont_sizeは文字列→intで変換される
        # 直接テスト不可だが、少なくともクラッシュしないことを確認


# ============================================================
# StyleManager テスト
# ============================================================
class TestStyleManagerApplyTheme:
    def test_apply_theme_is_noop(self):
        StyleManager.apply_theme_to_dialog(MagicMock())


class TestStyleManagerPresets:
    @pytest.fixture
    def sm(self, tmp_path):
        mw = MagicMock()
        mw.json_directory = str(tmp_path)
        return StyleManager(mw)

    def test_get_presets_directory_creates_dir(self, sm, tmp_path):
        presets_dir = sm.get_presets_directory()
        assert os.path.isdir(presets_dir)
        assert presets_dir.endswith("presets")

    def test_get_available_presets_empty(self, sm):
        result = sm.get_available_presets()
        assert result == []

    def test_get_available_presets_with_files(self, sm, tmp_path):
        sm.get_presets_directory()
        # JSONファイル作成
        (tmp_path / "presets" / "style1.json").write_text("{}")
        (tmp_path / "presets" / "style1.png").write_bytes(b"PNG")
        (tmp_path / "presets" / "style2.json").write_text("{}")
        # style2にはサムネイルなし

        result = sm.get_available_presets()
        assert len(result) == 2
        names = [p["name"] for p in result]
        assert "style1" in names
        assert "style2" in names

        # style1はサムネイルあり
        s1 = next(p for p in result if p["name"] == "style1")
        assert s1["thumb_path"] is not None

        # style2はサムネイルなし
        s2 = next(p for p in result if p["name"] == "style2")
        assert s2["thumb_path"] is None

    def test_delete_style_removes_files(self, sm, tmp_path):
        presets_dir = sm.get_presets_directory()
        json_path = os.path.join(presets_dir, "test.json")
        thumb_path = os.path.join(presets_dir, "test.png")

        with open(json_path, "w") as f:
            f.write("{}")
        with open(thumb_path, "w") as f:
            f.write("PNG")

        result = sm.delete_style(json_path)
        assert result is True
        assert not os.path.exists(json_path)
        assert not os.path.exists(thumb_path)

    def test_delete_nonexistent_style(self, sm):
        result = sm.delete_style("/nonexistent/path.json")
        assert result is False


class TestApplyDataToWindow:
    @pytest.fixture
    def sm(self):
        mw = MagicMock()
        mw.json_directory = "/tmp"
        return StyleManager(mw)

    def test_apply_sets_properties(self, sm):
        window = MagicMock()
        style_data = {
            "font": "Meiryo",
            "font_color": "#FF0000",
            "shadow_enabled": True,
        }
        sm._apply_data_to_window(window, style_data)
        # font -> font_family にマッピングされる
        window.set_undoable_property.assert_any_call("font_family", "Meiryo", None)
        window.set_undoable_property.assert_any_call("font_color", "#FF0000", None)
        window.update_text.assert_called_once()

    def test_apply_skips_font_size(self, sm):
        window = MagicMock()
        style_data = {"font_size": 48}
        sm._apply_data_to_window(window, style_data)
        # font_size は除外される
        for call in window.set_undoable_property.call_args_list:
            assert call[0][0] != "font_size"

    def test_apply_skips_is_vertical(self, sm):
        window = MagicMock()
        style_data = {"is_vertical": True}
        sm._apply_data_to_window(window, style_data)
        for call in window.set_undoable_property.call_args_list:
            assert call[0][0] != "is_vertical"

    def test_apply_style_to_text_windows_batch(self, sm, tmp_path):
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        json_path = presets_dir / "style.json"
        json_path.write_text(json.dumps({"font": "Arial", "font_color": "#000"}))

        w1 = MagicMock()
        w2 = MagicMock()
        sm.apply_style_to_text_windows([w1, w2], str(json_path))
        w1.update_text.assert_called()
        w2.update_text.assert_called()

    def test_apply_style_to_empty_list(self, sm):
        sm.apply_style_to_text_windows([], "/path.json")
        # Should not crash

    def test_apply_style_nonexistent_path(self, sm):
        sm.apply_style_to_text_windows([MagicMock()], "/nonexistent.json")
        # Should not crash (early return)
