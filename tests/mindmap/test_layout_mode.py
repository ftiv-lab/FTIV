"""
レイアウトモード (Auto/Manual) の挙動テスト。

新設計では、is_manual_position フラグではなく、
コントローラー全体で layout_mode を管理する。
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from PySide6.QtCore import QPointF

from ui.controllers.mindmap_controller import MindMapController
from ui.mindmap.mindmap_canvas import MindMapCanvas


class MockMindMapWidget:
    """テスト用の簡易 MindMapWidget モック。"""

    def __init__(self, qapp):
        from PySide6.QtWidgets import QGraphicsScene

        self.canvas = MindMapCanvas(None)
        self.scene = QGraphicsScene()
        self.canvas.setScene(self.scene)
        self.mw = None  # MainWindow は不要


def test_manual_mode_no_auto_layout(qapp):
    """
    検証: Manualモードでは、ノード追加時に自動レイアウトが実行されない。
    """
    widget = MockMindMapWidget(qapp)
    controller = MindMapController(widget)

    # Manualモードを確認
    assert controller.layout_mode == "manual"

    # ルートノードを追加
    root = controller.add_node("Root", QPointF(0, 0))

    # 子ノードを追加
    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    child = controller.add_child_node(root)

    # 検証: 子ノードが自動レイアウトされていない (初期位置計算のみ)
    # Manualモードでは arrange_tree が呼ばれないので、
    # 子ノードは calculate_child_position で計算された位置にある
    initial_child_pos = child.pos()

    # ルートノードを手動で移動
    root.setPos(100, 100)

    # Manualモードでは、親を動かしても子は自動追従しない
    assert child.pos() == initial_child_pos


def test_auto_mode_applies_layout(qapp):
    """
    検証: Autoモードでは、ノード追加時に自動レイアウトが実行される。
    """
    widget = MockMindMapWidget(qapp)
    controller = MindMapController(widget)

    # Autoモードに切り替え
    controller.set_layout_mode("auto")
    assert controller.layout_mode == "auto"

    # ルートノードを追加
    root = controller.add_node("Root", QPointF(0, 0))

    # 子ノードを追加
    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    child = controller.add_child_node(root)

    # 検証: 自動レイアウトが適用されている
    # RightLogicalStrategy: 子は親の右側 (x + 250) に配置される
    assert child.x() == root.x() + 250
    # Y軸は親と同じ (子が1つのみの場合)
    assert abs(child.y() - root.y()) < 1


def test_mode_switch_triggers_layout(qapp):
    """
    検証: ManualからAutoへの切り替え時に、即座にレイアウトが適用される。
    """
    widget = MockMindMapWidget(qapp)
    controller = MindMapController(widget)

    # Manualモードでノードを作成
    root = controller.add_node("Root", QPointF(0, 0))

    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    child1 = controller.add_child_node(root)

    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    child2 = controller.add_child_node(root)

    # 手動で位置を変更
    child1.setPos(500, 500)
    child2.setPos(600, 600)

    # Autoモードに切り替え
    controller.set_layout_mode("auto")

    # 検証: 自動レイアウトが即座に適用される
    # 手動位置は上書きされ、整列される
    assert child1.x() == root.x() + 250
    assert child2.x() == root.x() + 250

    # Y座標は子2つがバランスよく配置される
    # (詳細な位置は戦略に依存するが、手動位置からは変更されているはず)
    assert child1.pos() != QPointF(500, 500)
    assert child2.pos() != QPointF(600, 600)


def test_manual_mode_preserves_positions(qapp):
    """
    検証: Manualモードでは、明示的に auto_layout_all を呼ぶまで位置が保持される。
    """
    widget = MockMindMapWidget(qapp)
    controller = MindMapController(widget)

    # Manualモード
    assert controller.layout_mode == "manual"

    # ノード作成
    root = controller.add_node("Root", QPointF(0, 0))
    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    child = controller.add_child_node(root)

    # 手動で位置変更
    manual_pos = QPointF(300, 300)
    child.setPos(manual_pos)

    # 別のノードを追加しても、既存ノードの位置は変わらない
    controller.canvas.scene().clearSelection()
    root.setSelected(True)
    controller.add_child_node(root)

    assert child.pos() == manual_pos

    # 明示的に auto_layout_all を呼ぶと、整列される
    controller.auto_layout_all(animate=False)

    # 手動位置は上書きされる
    assert child.pos() != manual_pos
