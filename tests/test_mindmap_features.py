import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from models.app_mode import AppMode
from models.mindmap_data import MindMapData
from ui.main_window import MainWindow
from ui.mindmap.mindmap_canvas import MindMapCanvas
from ui.mindmap.mindmap_edge import MindMapEdge
from ui.mindmap.mindmap_node import MindMapNode


def test_mindmap_data_model():
    """MindMapDataのシリアライズ・デシリアライズをテスト"""
    data = MindMapData()
    node1 = {"uuid": "n1", "text": "Root", "x": 0, "y": 0}
    data.nodes.append(node1)

    serialized = data.to_dict()
    assert serialized.get("format_version") is None
    assert serialized["name"] == "Untitled Mind Map"
    assert len(serialized["nodes"]) == 1
    assert serialized["nodes"][0]["uuid"] == "n1"

    restored = MindMapData.from_dict(serialized)
    assert len(restored.nodes) == 1
    assert restored.nodes[0]["text"] == "Root"


def test_mindmap_node_creation(qapp):
    """MindMapNodeの作成とプロパティテスト"""
    node = MindMapNode("Test Node")
    assert node.text == "Test Node"
    assert node.flags() & MindMapNode.GraphicsItemFlag.ItemIsMovable
    assert node.flags() & MindMapNode.GraphicsItemFlag.ItemIsSelectable

    node._bg_color = QColor("red")
    node._text_color = QColor("white")
    assert node._bg_color == QColor("red")
    assert node._text_color == QColor("white")


def test_mindmap_edge_creation(qapp):
    """MindMapEdgeの作成と接続テスト"""
    node1 = MindMapNode("Start")
    node2 = MindMapNode("End")
    node1.setPos(0, 0)
    node2.setPos(100, 100)

    edge = MindMapEdge(node1, node2)
    assert edge.source_node == node1
    assert edge.target_node == node2

    edge.update_path()
    path = edge.path()
    assert not path.isEmpty()


def test_mindmap_canvas_operations(qapp):
    """MindMapCanvasへのアイテム追加・削除テスト"""
    canvas = MindMapCanvas()
    scene = canvas.scene()

    node = MindMapNode("Center")
    node.setPos(0, 0)
    scene.addItem(node)

    assert node in scene.items()

    nodes = [item for item in scene.items() if isinstance(item, MindMapNode)]
    assert len(nodes) == 1

    scene.removeItem(node)
    assert node not in scene.items()

    nodes_after = [item for item in scene.items() if isinstance(item, MindMapNode)]
    assert len(nodes_after) == 0


def test_app_mode_manager(qapp):
    """モード切替のテスト"""
    mw = MainWindow()
    manager = mw.app_mode_manager

    assert manager.current_mode == AppMode.DESKTOP

    manager.switch_to_mindmap()
    assert manager.current_mode == AppMode.MIND_MAP
    assert mw.mindmap_widget.isVisible()

    manager.switch_to_desktop()
    assert manager.current_mode == AppMode.DESKTOP

    mw.close()


def test_file_manager_mindmap_integration(qapp, tmp_path):
    """FileManagerのマインドマップ保存/読み込み統合テスト"""
    mw = MainWindow()
    fm = mw.file_manager

    # original_path = fm.mindmap_db_path
    # temp_db = tmp_path / "mindmaps.json"

    test_data = {
        "format_version": 1,
        "nodes": [{"uuid": "test_n1", "text": "Hello", "x": 10, "y": 20}],
        "edges": [],
        "canvas_settings": {},
    }

    mw.mindmaps = {"test_category": {"test_map": test_data}}

    fm.deserialize_mindmap(test_data)

    scene = mw.mindmap_widget.canvas.scene()
    nodes = [item for item in scene.items() if isinstance(item, MindMapNode)]
    assert len(nodes) == 1
    node = nodes[0]
    assert node.text == "Hello"
    assert node.pos() == QPointF(10, 20)

    serialized = fm.serialize_mindmap()
    assert len(serialized["nodes"]) == 1
    assert serialized["nodes"][0]["text"] == "Hello"

    mw.close()


def test_mindmap_node_text_renderer_mode(qapp):
    """TextRenderer モードのテスト"""
    from models.mindmap_node_config import MindMapNodeConfig

    node_default = MindMapNode("Default Node")
    assert node_default.use_text_renderer is True
    assert node_default.config is not None

    node_styled = MindMapNode("Styled Node", use_text_renderer=True)
    assert node_styled.use_text_renderer is True
    assert node_styled.config is not None
    assert isinstance(node_styled.config, MindMapNodeConfig)
    assert node_styled.config.text == "Styled Node"

    node_default._disable_text_renderer()
    assert node_default.use_text_renderer is False

    node_default._enable_text_renderer()
    assert node_default.use_text_renderer is True
    assert node_default.config is not None
    assert node_default.config.text == "Default Node"

    data = node_styled.to_dict()
    assert data["use_text_renderer"] is True
    assert "config" in data

    restored = MindMapNode.from_dict(data)
    assert restored.use_text_renderer is True
    assert restored.config is not None
    assert restored.config.text == "Styled Node"


def test_mindmap_widget_signal_integration(qapp):
    """MindMapWidget のシグナル統合と選択伝播の E2E テスト (Bug Fix Verification)"""
    mw = MainWindow()
    widget = mw.mindmap_widget
    canvas = widget.canvas
    wm = mw.window_manager
    prop_panel = mw.property_panel

    test_pos = QPointF(150, 250)
    canvas.sig_add_node_requested.emit(test_pos)

    scene = canvas.scene()
    nodes = [item for item in scene.items() if isinstance(item, MindMapNode)]
    assert len(nodes) == 1
    new_node = nodes[0]
    assert new_node.pos() == test_pos
    assert new_node.isSelected()
    assert wm.last_selected_window == new_node
    assert prop_panel.current_target == new_node

    new_node.setSelected(False)
    assert not new_node.isSelected()
    assert wm.last_selected_window is None
    assert prop_panel.current_target is None

    mw.close()


def test_mindmap_node_z_ordering(qapp):
    """MindMapNode.raise_() / lower() の動作確認 (Z-Ordering)"""
    from ui.mindmap.mindmap_canvas import MindMapCanvas

    canvas = MindMapCanvas()
    scene = canvas.scene()

    node1 = MindMapNode("Node 1")
    node2 = MindMapNode("Node 2")
    scene.addItem(node1)
    scene.addItem(node2)

    node1.setZValue(1.0)
    node2.setZValue(2.0)
    assert node1.zValue() < node2.zValue()

    node1.raise_()
    assert node1.zValue() > node2.zValue()

    node1.lower()
    assert node1.zValue() < node2.zValue()


def test_mindmap_toolbar_property_button(qapp):
    """MindMapWidget のプロパティパネルボタンの動作確認"""
    from PySide6.QtWidgets import QPushButton

    from ui.main_window import MainWindow
    from ui.mindmap.mindmap_widget import MindMapWidget

    mw = MainWindow()
    mw.show()
    mw.app_mode_manager.switch_to_mindmap()

    widget: MindMapWidget = mw.mindmap_widget
    btn: QPushButton = widget._btn_property

    mw.is_property_panel_active = False
    btn.setChecked(False)

    btn.click()
    assert mw.is_property_panel_active is True
    assert btn.isChecked() is True

    mw.toggle_property_panel()
    assert mw.is_property_panel_active is False
    assert btn.isChecked() is False

    mw.toggle_property_panel()
    assert mw.is_property_panel_active is True
    assert btn.isChecked() is True

    mw.close()


def test_mindmap_property_panel_interactions(qapp):
    """MindMapNodeに対するPropertyPanelの操作テスト (E2E)"""
    from unittest.mock import patch

    from PySide6.QtGui import QFont

    from ui.main_window import MainWindow
    from ui.mindmap.mindmap_canvas import MindMapCanvas
    from ui.mindmap.mindmap_node import MindMapNode

    mw = MainWindow()
    mw.show()
    mw.app_mode_manager.switch_to_mindmap()

    canvas: MindMapCanvas = mw.mindmap_widget.canvas
    node = MindMapNode("Test Node")
    canvas.scene().addItem(node)
    node.setSelected(True)

    prop_panel = mw.property_panel
    assert prop_panel.current_target == node

    # 1. テキストコンテンツの更新 (未実装のためスキップ)
    # 2. 数値プロパティの更新 (QSpinBox -> Node Config)
    if node.config:
        assert hasattr(prop_panel, "spin_text_opacity")
        spin = prop_panel.spin_text_opacity
        spin.setValue(50)
        assert node.config.text_opacity == 50

    # 3. フォント変更のテスト (Mocking QFontDialog)
    assert hasattr(prop_panel, "btn_text_font")
    btn_font = prop_panel.btn_text_font

    with patch("PySide6.QtWidgets.QFontDialog.getFont") as mock_get_font:
        test_font = QFont("Arial", 24)
        mock_get_font.return_value = (True, test_font)
        btn_font.click()
        if node.config:
            assert node.config.font_family == "Arial"
            assert node.config.font_size == 24

    # 4. フォントサイズスライダーのテスト
    assert hasattr(prop_panel, "slider_text_font_size")
    slider = prop_panel.slider_text_font_size
    assert slider is not None
    slider.setValue(48)
    slider.sliderReleased.emit()
    assert node.config.font_size == 48

    # 5. リアルタイム座標更新のテスト
    assert hasattr(prop_panel, "spin_x")
    spin_x = prop_panel.spin_x
    initial_x_val = spin_x.value()

    # ノード移動 simulate
    new_pos = node.pos() + QPointF(10, 10)
    node.setPos(new_pos)

    # PropertyPanel should update coordinate spinbox immediately
    assert spin_x.value() == new_pos.x()
    assert spin_x.value() != initial_x_val

    mw.close()


def test_zoom_synchronization(qapp):
    """ズーム操作（Canvas -> Widget）の同期テスト"""
    mw = MainWindow()
    mw.show()
    mw.app_mode_manager.switch_to_mindmap()

    widget = mw.mindmap_widget
    canvas = widget.canvas
    slider = widget._zoom_slider
    label = widget._zoom_label

    # 1. Canvas側でズーム変更
    assert slider.value() == 100

    # reset_zoom 呼び出し
    canvas.reset_zoom()
    assert slider.value() == 100
    assert label.text() == "100%"

    # アイテムを追加してエリアを広げる
    node = MindMapNode("Test Node")
    node.setPos(1000, 1000)
    canvas.scene().addItem(node)

    canvas.fit_all_nodes()

    # fit_all_nodes でズームが変わったはず
    new_zoom = canvas.transform().m11()
    expected_slider_val = int(new_zoom * 100)

    assert slider.value() == expected_slider_val
    assert label.text() == f"{expected_slider_val}%"

    mw.close()
