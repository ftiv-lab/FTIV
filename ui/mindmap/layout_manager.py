import logging
import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QEasingCurve, QPointF, QVariantAnimation

from ui.mindmap.layouts.layout_strategy import LayoutStrategy
from ui.mindmap.layouts.right_logical_strategy import RightLogicalStrategy

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode

logger = logging.getLogger(__name__)


class LayoutManager:
    """ノードの配置計算とアニメーションを担当するクラス。

    Strategy Pattern を採用し、実際の配置計算ロジックは LayoutStrategy に委譲する。
    本クラスはアニメーションの管理と Strategy の切り替えを担当する。
    """

    def __init__(self):
        # 処理中のアニメーションを保持（GC対策）
        self._animations = []
        # デフォルトのレイアウト戦略
        self.strategy: LayoutStrategy = RightLogicalStrategy()

    def set_strategy(self, strategy: LayoutStrategy) -> None:
        """レイアウト戦略を変更する。"""
        self.strategy = strategy
        logger.info(f"Layout strategy changed to: {strategy.get_layout_name()}")

    def arrange_tree(self, root_node: "MindMapNode", animate: bool = True) -> None:
        """ルートノードを起点としてツリーを自動整列させる。

        Args:
            root_node: ツリーのルートノード。
            animate: Trueの場合、移動をアニメーションさせる。
        """
        if not root_node:
            return

        # logger.debug(f"Arranging tree with {self.strategy.get_layout_name()}")

        # 1. Strategy に配置計算を委譲
        # 計算結果は各ノードの _layout_target_pos 属性などにセットされる
        self.strategy.calculate_positions(root_node)

        # 2. 計算結果を適用（アニメーション）
        self._apply_positions(root_node, animate)

    def calculate_child_position(self, parent_node: "MindMapNode") -> QPointF:
        """単一の子ノード追加時の仮位置を計算する。"""
        return self.strategy.calculate_child_position(parent_node)

    def calculate_root_sibling_position(self, node: "MindMapNode") -> QPointF:
        """ルート兄弟の仮位置。"""
        return self.strategy.calculate_root_sibling_position(node)

    # ---------------------------------------------------------
    # Internal Logic (Animation)
    # ---------------------------------------------------------

    def _apply_positions(self, node: "MindMapNode", animate: bool) -> None:
        """決定された座標を実際に適用する。"""
        # Test Mode Check: Override animation
        if os.environ.get("FTIV_TEST_MODE"):
            animate = False

        target_pos = getattr(node, "_layout_target_pos", None)

        if target_pos is not None:
            if animate and node.scene():
                # QVariantAnimationを使用
                anim = QVariantAnimation()
                anim.setDuration(300)
                anim.setStartValue(node.pos())
                anim.setEndValue(target_pos)
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.valueChanged.connect(node.setPos)
                anim.start()

                # 参照保持 (PythonのGC対策)
                self._animations.append(anim)
                anim.finished.connect(lambda: self._cleanup_animation(anim))
            else:
                # 即時適用
                node.setPos(target_pos)

        # 子要素にも適用
        for child in node.get_child_nodes():
            self._apply_positions(child, animate)

    def _cleanup_animation(self, anim):
        if anim in self._animations:
            self._animations.remove(anim)
