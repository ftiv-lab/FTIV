import json
import os
import sys
from unittest.mock import MagicMock

import pytest  # noqa: F401 (required for fixtures)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene

# Adjust path to find modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from managers.file_manager import FileManager
from models.default_node_style import DefaultNodeStyle
from ui.mindmap.mindmap_node import MindMapNode
from ui.mindmap.mindmap_widget import MindMapWidget


def test_default_node_style_model():
    """DefaultNodeStyleモデルの動作確認"""
    style = DefaultNodeStyle()

    # Defaults
    assert style.font_family == "Segoe UI"
    assert style.font_size == 14
    assert style.font_color == "#ffffff"
    assert style.background_color == "#3c3c5c"

    # Modification
    style.font_size = 20
    style.shadow_enabled = True

    # Dict conversion
    data = style.to_dict()
    assert data["font_size"] == 20
    assert data["shadow_enabled"] is True

    # Restore
    restored = DefaultNodeStyle.from_dict(data)
    assert restored.font_size == 20
    assert restored.shadow_enabled is True


def test_apply_to_config():
    """apply_to_config メソッドのテスト"""
    from models.mindmap_node_config import MindMapNodeConfig

    style = DefaultNodeStyle()
    style.font_family = "Impact"
    style.font_size = 24
    style.shadow_enabled = True
    style.outline_width = 5.0

    config = MindMapNodeConfig(uuid="test-uuid", text="Test")

    # Apply style to config
    style.apply_to_config(config)

    # Verify values were copied
    assert config.font_family == "Impact"
    assert config.font_size == 24
    assert config.shadow_enabled is True
    assert config.outline_width == 5.0


def test_copy_from_config():
    """copy_from_config メソッドのテスト"""
    from models.mindmap_node_config import MindMapNodeConfig

    config = MindMapNodeConfig(uuid="test-uuid", text="Test")
    config.font_family = "Arial"
    config.font_size = 18
    config.outline_enabled = True
    config.background_corner_ratio = 0.5

    style = DefaultNodeStyle()

    # Copy config to style
    style.copy_from_config(config)

    # Verify values were copied
    assert style.font_family == "Arial"
    assert style.font_size == 18
    assert style.outline_enabled is True
    assert style.background_corner_ratio == 0.5


def test_file_manager_persistence(qapp, tmp_path):
    """FileManagerによる保存と読み込みのテスト"""
    # Mock MainWindow
    mw = MagicMock()
    # Mock json_directory property or attribute
    mw.json_directory = str(tmp_path)
    mw.default_node_style = DefaultNodeStyle()

    fm = FileManager(mw)

    # Modify style
    mw.default_node_style.font_family = "Arial"
    mw.default_node_style.outline_enabled = True

    # Save
    fm.save_default_node_style()

    # Check file exists
    expected_file = tmp_path / "default_node_style.json"
    assert expected_file.exists()

    # Check content
    with open(expected_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["font_family"] == "Arial"
    assert saved_data["outline_enabled"] is True

    # Load (reset style first)
    mw.default_node_style = DefaultNodeStyle()
    assert mw.default_node_style.font_family == "Segoe UI"  # default

    fm.load_default_node_style()
    assert mw.default_node_style.font_family == "Arial"
    assert mw.default_node_style.outline_enabled is True


def test_mindmap_widget_applies_style(qapp):
    """MindMapWidgetが新規ノードにスタイルを適用することを確認"""
    # Mock MainWindow and style
    mw = MagicMock()
    mw.default_node_style = DefaultNodeStyle()
    mw.default_node_style.font_size = 24
    mw.default_node_style.font_color = "#ff0000"

    # Internal mock for canvas or other heavy dependencies if needed
    # base_directory etc. might be needed by MindMapWidget -> MindMapCanvas
    mw.base_directory = "."

    widget = MindMapWidget(mw)

    # Add node
    node = widget.add_node("Test")

    if hasattr(node, "config"):
        assert node.config.font_size == 24
        assert node.config.font_color == "#ff0000"
    else:
        # Fallback if properties are flattened
        assert node._font_size == 24
        # Color objects might need comparison
        if isinstance(node._text_color, QColor):
            assert node._text_color.name() == "#ff0000"
        else:
            assert node._text_color == "#ff0000"

    # Check default was used (Segoe UI)
    if hasattr(node, "config"):
        assert node.config.font_family == "Segoe UI"
    else:
        # Check actual QFont
        assert node.font().family() == "Segoe UI"


def test_set_as_default_from_node(qapp, tmp_path, monkeypatch):
    """ノードからデフォルトスタイルを設定する動作を確認 (Signal/Slot 方式)"""
    # Mock MainWindow stack
    mw = MagicMock()
    mw.json_directory = str(tmp_path)
    mw.default_node_style = DefaultNodeStyle()

    # FileManager needs to be real enough or mocked
    fm = FileManager(mw)
    mw.file_manager = fm

    # Setup Scene
    scene = QGraphicsScene()

    node = MindMapNode("Source Node")
    scene.addItem(node)

    # Verify preconditions
    assert node._config is not None, "node._config is None, cannot proceed with test"

    # Modify node config directly
    node._config.font_family = "Courier New"
    node._config.outline_width = 5.5

    # Verify modification locally
    assert node._config.font_family == "Courier New"

    # Connect signal to a handler that mimics MindMapWidget._handle_set_as_default
    def handle_set_as_default(config):
        mw.default_node_style.copy_from_config(config)
        mw.file_manager.save_default_node_style()

    node.sig_request_set_as_default.connect(handle_set_as_default)

    # Execute - this emits the signal
    node._set_as_default_style()

    # Verify MW style updated via signal handler
    assert mw.default_node_style.font_family == "Courier New"
    assert mw.default_node_style.outline_width == 5.5

    # Verify file saved
    expected_file = tmp_path / "default_node_style.json"
    assert expected_file.exists()
