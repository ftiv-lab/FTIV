# -*- coding: utf-8 -*-
"""FileManager のシリアライズ/デシリアライズテスト (Sprint 2).

UI部分 (QFileDialog等) はスコープ外。純粋な変換ロジックのみ。
"""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from managers.file_manager import FileManager
from models.enums import ArrowStyle
from models.window_config import TextWindowConfig


@pytest.fixture
def fm():
    """FileManager with mock MainWindow."""
    mw = MagicMock()
    mw.json_directory = "/tmp/test"
    mw.window_manager = MagicMock()
    return FileManager(mw)


class TestDumpConfigJson:
    def test_dump_returns_dict(self, fm):
        config = TextWindowConfig(text="Hello", font="Arial")
        result = fm._dump_config_json(config)
        assert isinstance(result, dict)
        assert result["text"] == "Hello"

    def test_dump_excludes_none(self, fm):
        config = TextWindowConfig(text="Test")
        config.parent_uuid = None
        result = fm._dump_config_json(config)
        assert "parent_uuid" not in result

    def test_dump_preserves_core_fields(self, fm):
        config = TextWindowConfig(
            text="Sample",
            font="Meiryo",
            font_size=32,
            font_color="#FFFFFF",
        )
        result = fm._dump_config_json(config)
        assert result["font"] == "Meiryo"
        assert result["font_size"] == 32
        assert result["font_color"] == "#FFFFFF"


class TestClearAbsoluteMoveFields:
    def test_clears_when_relative_mode(self, fm):
        config = MagicMock()
        config.move_use_relative = True
        config.start_position = {"x": 0, "y": 0}
        config.end_position = {"x": 100, "y": 100}
        fm._clear_absolute_move_fields_if_relative(config)
        assert config.start_position is None
        assert config.end_position is None

    def test_preserves_when_absolute_mode(self, fm):
        config = MagicMock()
        config.move_use_relative = False
        original_start = {"x": 0, "y": 0}
        config.start_position = original_start
        fm._clear_absolute_move_fields_if_relative(config)
        assert config.start_position == original_start

    def test_handles_missing_attributes(self, fm):
        config = MagicMock(spec=[])  # 属性なし
        fm._clear_absolute_move_fields_if_relative(config)  # クラッシュしない


class TestSerializePenStyle:
    def test_int_passthrough(self, fm):
        assert fm._serialize_pen_style(1) == 1

    def test_qt_pen_style_enum(self, fm):
        result = fm._serialize_pen_style(Qt.PenStyle.DashLine)
        assert isinstance(result, int)
        assert result == int(Qt.PenStyle.DashLine.value)

    def test_none_returns_solid_line(self, fm):
        result = fm._serialize_pen_style(None)
        assert isinstance(result, int)

    def test_invalid_returns_fallback(self, fm):
        result = fm._serialize_pen_style("garbage")
        assert isinstance(result, int)


class TestSerializeArrowStyle:
    def test_none_returns_none_str(self, fm):
        assert fm._serialize_arrow_style(None) == "none"

    def test_enum_value(self, fm):
        result = fm._serialize_arrow_style(ArrowStyle.END)
        assert result == "end"

    def test_string_passthrough(self, fm):
        assert fm._serialize_arrow_style("start") == "start"
        assert fm._serialize_arrow_style("both") == "both"

    def test_string_case_insensitive(self, fm):
        assert fm._serialize_arrow_style("END") == "end"
        assert fm._serialize_arrow_style("  Start  ") == "start"

    def test_prefixed_string(self, fm):
        assert fm._serialize_arrow_style("ArrowStyle.END") == "end"
        assert fm._serialize_arrow_style("ArrowStyle.NONE") == "none"

    def test_invalid_returns_none(self, fm):
        assert fm._serialize_arrow_style(12345) == "none"


class TestSerializeQColorHexArgb:
    def test_qcolor_object(self, fm):
        color = QColor(255, 0, 0, 128)
        result = fm._serialize_qcolor_hexargb(color)
        assert result.startswith("#")
        assert len(result) == 9  # #AARRGGBB

    def test_hex_string(self, fm):
        result = fm._serialize_qcolor_hexargb("#FF0000")
        assert result.startswith("#")
        assert "ff" in result.lower()

    def test_argb_string(self, fm):
        result = fm._serialize_qcolor_hexargb("#80FF0000")
        assert result.startswith("#")

    def test_invalid_returns_fallback(self, fm):
        result = fm._serialize_qcolor_hexargb("not-a-color")
        assert result.startswith("#")
        assert len(result) == 9


class TestGetSceneData:
    def test_empty_scene(self, fm):
        fm.window_manager.text_windows = []
        fm.window_manager.image_windows = []
        fm.window_manager.connectors = []
        result = fm.get_scene_data()
        assert result["format_version"] == 1
        assert result["windows"] == []
        assert result["connections"] == []

    def test_scene_with_text_window(self, fm):
        config = TextWindowConfig(text="Test")
        tw = MagicMock()
        tw.config = config
        tw.x.return_value = 10
        tw.y.return_value = 20
        fm.window_manager.text_windows = [tw]
        fm.window_manager.image_windows = []
        fm.window_manager.connectors = []
        result = fm.get_scene_data()
        assert len(result["windows"]) == 1
        assert result["windows"][0]["type"] == "text"
        assert result["windows"][0]["text"] == "Test"
