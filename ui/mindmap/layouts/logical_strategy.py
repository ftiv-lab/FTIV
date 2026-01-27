from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

from ui.mindmap.layouts.layout_strategy import LayoutStrategy

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class LogicalStrategy(LayoutStrategy):
    """ロジカルツリーレイアウト（一方向展開）。

    Reingold-Tilford (Simplified) アルゴリズムを使用。
    direction により展開方向（右/左）を制御可能。
    """

    HORIZONTAL_SPACING = 250
    VERTICAL_SPACING = 20

    def __init__(self, direction: int = 1):
        """
        Args:
            direction: 1 (Right) or -1 (Left)
        """
        self.direction = direction

    def calculate_positions(self, root_node: "MindMapNode") -> None:
        """ルートノードを基点にノードの配置座標を計算する。"""
        if not root_node:
            return

        self._calculate_dimensions(root_node)

        start_pos = root_node.pos()
        self._assign_positions(root_node, start_pos.x(), start_pos.y())

    def calculate_child_position(self, parent_node: "MindMapNode") -> QPointF:
        """子ノードの初期位置計算。"""
        offset_x = self.HORIZONTAL_SPACING * self.direction

        children = parent_node.get_child_nodes()
        if children:
            last_child = children[-1]
            # Y方向は常に下へ (direction関係なし)
            offset_y = last_child.y() - parent_node.y() + last_child._height + self.VERTICAL_SPACING
        else:
            offset_y = 0

        return QPointF(parent_node.x() + offset_x, parent_node.y() + offset_y)

    def calculate_root_sibling_position(self, node: "MindMapNode") -> QPointF:
        """ルート兄弟の初期位置計算。"""
        return QPointF(node.x(), node.y() + 100)

    def get_layout_name(self) -> str:
        return "Right Logical" if self.direction == 1 else "Left Logical"

    # ---------------------------------------------------------
    # Internal Logic
    # ---------------------------------------------------------

    def _calculate_dimensions(self, node: "MindMapNode") -> float:
        """サブツリーの高さを計算し、ノードに一時保存する。"""
        children = node.get_child_nodes()
        node_height = node._height

        if not children:
            node._layout_subtree_height = node_height + self.VERTICAL_SPACING
            return node._layout_subtree_height

        children_height = 0
        for child in children:
            children_height += self._calculate_dimensions(child)

        node._layout_subtree_height = max(node_height + self.VERTICAL_SPACING, children_height)
        return node._layout_subtree_height

    def _assign_positions(self, node: "MindMapNode", x: float, y: float) -> None:
        """計算された高さに基づいて座標を割り当てる。"""
        node._layout_target_pos = QPointF(x, y)

        children = node.get_child_nodes()
        if not children:
            return

        # X方向のオフセットに direction を適用
        start_x = x + (self.HORIZONTAL_SPACING * self.direction)

        total_children_height = 0
        for child in children:
            total_children_height += child._layout_subtree_height

        current_y = y - (total_children_height / 2)

        for child in children:
            child_height = child._layout_subtree_height
            child_center_y = current_y + (child_height / 2)

            self._assign_positions(child, start_x, child_center_y)

            current_y += child_height

    def _calculate_subtree_group(self, root_node: "MindMapNode", children: list["MindMapNode"]) -> None:
        """特定の子供グループについて配置を計算する（BalancedMap用）。"""
        if not children:
            return

        # 1. 各子供の次元計算
        for child in children:
            self._calculate_dimensions(child)

        # 2. 配置
        start_pos = root_node.pos()
        x = start_pos.x()
        y = start_pos.y()

        # X方向オフセット
        start_x = x + (self.HORIZONTAL_SPACING * self.direction)

        total_children_height = 0
        for child in children:
            total_children_height += child._layout_subtree_height

        current_y = y - (total_children_height / 2)

        for child in children:
            child_height = child._layout_subtree_height
            child_center_y = current_y + (child_height / 2)

            # 再帰呼び出しは通常の _assign_positions
            self._assign_positions(child, start_x, child_center_y)

            current_y += child_height
