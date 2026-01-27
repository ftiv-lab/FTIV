from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

from ui.mindmap.layouts.layout_strategy import LayoutStrategy
from ui.mindmap.layouts.logical_strategy import LogicalStrategy

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class BalancedMapStrategy(LayoutStrategy):
    """バランス型マップレイアウト。

    ルートノードを中心に、左右均等にツリーを展開する。
    """

    def __init__(self):
        self.left_strategy = LogicalStrategy(direction=-1)
        self.right_strategy = LogicalStrategy(direction=1)

    def calculate_positions(self, root_node: "MindMapNode") -> None:
        """ルートノードを基点にノードの配置座標を計算する。"""
        if not root_node:
            return

        children = root_node.get_child_nodes()
        if not children:
            # 子供がいなければ配置不要（ルートの位置は維持）
            return

        # 左右に振り分け (偶数: 右, 奇数: 左)
        right_group = []
        left_group = []

        for i, child in enumerate(children):
            if i % 2 == 0:
                right_group.append(child)
            else:
                left_group.append(child)

        # 右側の計算 (ルートからのオフセット計算のため、擬似的に適用)
        if right_group:
            self.right_strategy._calculate_subtree_group(root_node, right_group)

        # 左側の計算
        if left_group:
            self.left_strategy._calculate_subtree_group(root_node, left_group)

    def calculate_child_position(self, parent_node: "MindMapNode") -> QPointF:
        """子ノードの初期位置計算。"""
        # 親がルートの場合、バランスを見て決定する必要があるが、
        # ここでは暫定的に右に追加して、あとで arrange_tree で再配置される前提。
        # あるいは現在の子供数を見て決定する？

        # 親がルートでなければ、親の配置方向に従うべきだが、
        # 親の配置方向を知る術が（再帰計算外では）難しい。
        # 親のX座標とルートのX座標を比較して判定する。

        root = self._find_root(parent_node)
        if root == parent_node:
            # ルートへの追加: 子供数で判定
            child_count = len(root.get_child_nodes())
            direction = 1 if child_count % 2 == 0 else -1
            strategy = self.right_strategy if direction == 1 else self.left_strategy
            return strategy.calculate_child_position(parent_node)

        # 親がルートより左なら左戦略、右なら右戦略
        if parent_node.x() < root.x():
            return self.left_strategy.calculate_child_position(parent_node)
        else:
            return self.right_strategy.calculate_child_position(parent_node)

    def calculate_root_sibling_position(self, node: "MindMapNode") -> QPointF:
        """ルート兄弟の初期位置計算。"""
        return QPointF(node.x(), node.y() + 100)

    def get_layout_name(self) -> str:
        return "Balanced Map"

    # ---------------------------------------------------------
    # Internal Logic
    # ---------------------------------------------------------

    def _find_root(self, node: "MindMapNode") -> "MindMapNode":
        """ルートを探す（簡易実装）。"""
        # Nodeクラスにget_rootがない場合のフォールバック
        # 実際にはControllerが持っているロジックだが、Strategy内で完結させるために再実装
        # あるいはnode.rootプロパティがあればそれを使う
        current = node
        while True:
            parent = None
            for edge in current.edges:
                if edge.target_node == current:
                    parent = edge.source_node
                    break
            if parent:
                current = parent
            else:
                break
        return current
