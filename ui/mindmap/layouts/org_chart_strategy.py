from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

from ui.mindmap.layouts.layout_strategy import LayoutStrategy

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class OrgChartStrategy(LayoutStrategy):
    """組織図（トップダウン）レイアウト。

    Reingold-Tilford (Vertical) アルゴリズム。
    親ノードの下に子ノードを水平に配置する。
    """

    VERTICAL_SPACING = 150  # 階層間の高さ
    HORIZONTAL_SPACING = 30  # 兄弟間の隙間

    def calculate_positions(self, root_node: "MindMapNode") -> None:
        """ルートノードを基点にノードの配置座標を計算する。"""
        if not root_node:
            return

        # 1. 必要な幅を計算
        self._calculate_dimensions(root_node)

        # 2. 座標を決定
        start_pos = root_node.pos()
        self._assign_positions(root_node, start_pos.x(), start_pos.y())

    def calculate_child_position(self, parent_node: "MindMapNode") -> QPointF:
        """子ノードの初期位置計算。"""
        # 親の下に配置
        offset_y = self.VERTICAL_SPACING

        children = parent_node.get_child_nodes()
        if children:
            last_child = children[-1]
            # 既存の子供の右に配置
            offset_x = last_child.x() - parent_node.x() + last_child._subtree_width + self.HORIZONTAL_SPACING
        else:
            offset_x = 0

        return QPointF(parent_node.x() + offset_x, parent_node.y() + offset_y)

    def calculate_root_sibling_position(self, node: "MindMapNode") -> QPointF:
        """ルート兄弟の初期位置計算。"""
        return QPointF(node.x() + 200, node.y())

    def get_layout_name(self) -> str:
        return "Org Chart"

    def get_recommended_router_type(self) -> str:
        return "Orthogonal"

    # ---------------------------------------------------------
    # Internal Logic
    # ---------------------------------------------------------

    def _calculate_dimensions(self, node: "MindMapNode") -> float:
        """サブツリーの幅を計算し、ノードに一時保存する。"""
        children = node.get_child_nodes()

        # MindMapNodeは _width 属性を持っている（resize時更新）。
        if hasattr(node, "_width"):
            current_w = node._width
        else:
            current_w = 100  # Fallback

        if not children:
            node._subtree_width = current_w + self.HORIZONTAL_SPACING
            return node._subtree_width

        children_width = 0
        for child in children:
            children_width += self._calculate_dimensions(child)

        node._subtree_width = max(current_w + self.HORIZONTAL_SPACING, children_width)
        return node._subtree_width

    def _assign_positions(self, node: "MindMapNode", x: float, y: float) -> None:
        """座標を割り当てる。"""
        node._layout_target_pos = QPointF(x, y)

        children = node.get_child_nodes()
        if not children:
            return

        # 次の階層のY
        next_y = y + self.VERTICAL_SPACING

        # 子供たちの総幅
        total_msg_width = 0
        for child in children:
            total_msg_width += child._subtree_width

        # 開始X座標 (親のXを中心として、総幅の半分を左へ)
        current_x = x - (total_msg_width / 2)

        for child in children:
            child_width = child._subtree_width
            child_center_x = current_x + (child_width / 2)

            self._assign_positions(child, child_center_x, next_y)

            current_x += child_width
