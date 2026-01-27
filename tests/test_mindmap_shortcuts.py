import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import pytest
from PySide6.QtCore import QPointF

from ui.mindmap.mindmap_canvas import MindMapCanvas
from ui.mindmap.mindmap_edge import MindMapEdge
from ui.mindmap.mindmap_node import MindMapNode


class TestMindMapShortcuts:
    @pytest.fixture
    def canvas(self, qapp):
        c = MindMapCanvas()
        return c

    def test_add_child_node(self, canvas):
        """子ノードの追加ロジックテスト"""
        # 親ノード作成
        parent = MindMapNode("Parent", position=QPointF(0, 0))
        canvas.scene().addItem(parent)
        parent.setSelected(True)

        # Action: 子ノード追加
        if not hasattr(canvas, "add_child_node"):
            pytest.skip("Method add_child_node not implemented yet")

        child = canvas.add_child_node()  # 引数なし＝選択ノードに対する操作

        # Verification
        assert child is not None
        assert isinstance(child, MindMapNode)

        # 親子関係が結ばれているか
        edges = [item for item in canvas.scene().items() if isinstance(item, MindMapEdge)]
        assert len(edges) == 1
        edge = edges[0]
        assert edge.source_node == parent
        assert edge.target_node == child

        # 位置確認 (親の右側にあるべき)
        assert child.x() > parent.x()

        # 選択状態の遷移
        assert child.isSelected()
        assert not parent.isSelected()

    def test_add_sibling_node(self, canvas):
        """兄弟ノードの追加ロジックテスト"""
        # 親作成
        root = MindMapNode("Root", position=QPointF(0, 0))
        canvas.scene().addItem(root)

        # 子A作成
        child_a = MindMapNode("A", position=QPointF(200, 0))
        canvas.scene().addItem(child_a)

        # 手動で接続
        edge = MindMapEdge(root, child_a)
        canvas.scene().addItem(edge)
        # Note: MindMapEdge automatically appends itself to nodes' edge lists

        child_a.setSelected(True)

        # Action: 兄弟追加
        if not hasattr(canvas, "add_sibling_node"):
            pytest.skip("Method add_sibling_node not implemented yet")

        sibling = canvas.add_sibling_node()

        # Verification
        assert sibling is not None
        assert sibling != child_a

        # ルートの子が2つになっているか
        child_nodes = root.get_child_nodes()
        assert len(child_nodes) == 2
        assert sibling in child_nodes

        # 位置確認 (兄弟の下にあるべき)
        assert sibling.y() != child_a.y()

        # 選択状態
        assert sibling.isSelected()

    def test_delete_selected_items(self, canvas):
        """削除機能テスト"""
        # ノードとエッジ作成
        n1 = MindMapNode("N1")
        n2 = MindMapNode("N2")
        canvas.scene().addItem(n1)
        canvas.scene().addItem(n2)
        edge = MindMapEdge(n1, n2)
        canvas.scene().addItem(edge)
        # Note: MindMapEdge automatically appends itself to nodes' edge lists

        # N2を選択して削除
        n2.setSelected(True)

        if not hasattr(canvas, "delete_selected_items"):
            pytest.skip("Method delete_selected_items not implemented yet")

        canvas.delete_selected_items()

        # 検証
        items = canvas.scene().items()
        assert n2 not in items
        assert edge not in items  # エッジも消えているべき
        assert n1 in items  # N1は残る
