from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class EdgeRouter(ABC):
    """エッジ（接続線）の経路を計算するインターフェース。"""

    @abstractmethod
    def create_path(self, source: "MindMapNode", target: "MindMapNode") -> QPainterPath:
        """ソースノードからターゲットノード等へのパスを生成する。"""
        pass

    def get_router_type(self) -> str:
        return "Unknown"

    def _get_connection_point(self, node: "MindMapNode", direction_to: QPointF) -> QPointF:
        """ノードの端における接続点を計算する（汎用）。"""
        center = node.center
        rect = node.boundingRect()
        width = rect.width()
        height = rect.height()

        dx = direction_to.x() - center.x()
        dy = direction_to.y() - center.y()

        if dx == 0 and dy == 0:
            return center

        if abs(dx) * height > abs(dy) * width:
            # 左右
            return (
                QPointF(center.x() + width / 2, center.y()) if dx > 0 else QPointF(center.x() - width / 2, center.y())
            )
        else:
            # 上下
            return (
                QPointF(center.x(), center.y() + height / 2) if dy > 0 else QPointF(center.x(), center.y() - height / 2)
            )


class BezierRouter(EdgeRouter):
    """ベジェ曲線による経路生成。"""

    def create_path(self, source: "MindMapNode", target: "MindMapNode") -> QPainterPath:
        source_center = source.center
        target_center = target.center

        source_point = self._get_connection_point(source, target_center)
        target_point = self._get_connection_point(target, source_center)

        path = QPainterPath()
        path.moveTo(source_point)

        dx = target_point.x() - source_point.x()
        dy = target_point.y() - source_point.y()
        distance = (dx**2 + dy**2) ** 0.5

        ctrl_offset = min(distance * 0.4, 100)

        if abs(dx) > abs(dy):
            ctrl1 = QPointF(source_point.x() + ctrl_offset, source_point.y())
            ctrl2 = QPointF(target_point.x() - ctrl_offset, target_point.y())
        else:
            ctrl1 = QPointF(source_point.x(), source_point.y() + ctrl_offset * (1 if dy > 0 else -1))
            ctrl2 = QPointF(target_point.x(), target_point.y() - ctrl_offset * (1 if dy > 0 else -1))

        path.cubicTo(ctrl1, ctrl2, target_point)
        return path

    def get_router_type(self) -> str:
        return "Bezier"


class OrthogonalRouter(EdgeRouter):
    """カギ線（直角）による経路生成。

    組織図（Org Chart）などで使用。
    ソースの下端 -> 中間Y -> ターゲットの上端 へと接続する。
    """

    def create_path(self, source: "MindMapNode", target: "MindMapNode") -> QPainterPath:
        # ソースは「下」、ターゲットは「上」に固定接続
        source_rect = source.boundingRect()
        target_rect = target.boundingRect()

        source_point = QPointF(source.center.x(), source.center.y() + source_rect.height() / 2)
        target_point = QPointF(target.center.x(), target.center.y() - target_rect.height() / 2)

        path = QPainterPath()
        path.moveTo(source_point)

        # 中間Y地点（親子の中間より少し上寄り、あるいは階層構造に合わせる）
        # 単純な中間点
        mid_y = source_point.y() + (target_point.y() - source_point.y()) / 2

        # パス: 下 -> 横 -> 下
        p1 = QPointF(source_point.x(), mid_y)
        p2 = QPointF(target_point.x(), mid_y)

        path.lineTo(p1)
        path.lineTo(p2)
        path.lineTo(target_point)

        return path

    def get_router_type(self) -> str:
        return "Orthogonal"
