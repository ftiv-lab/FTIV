# ui/mindmap/mindmap_edge.py
"""
マインドマップ用エッジ（接続線）。

QGraphicsPathItem ベースで、2つのノード間を接続する。
描画ロジックは EdgeRouter に委譲されている。
"""

import logging
import uuid
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

from ui.mindmap.styles.edge_routers import BezierRouter, EdgeRouter
from utils.translator import tr

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode

logger = logging.getLogger(__name__)


class MindMapEdge(QGraphicsPathItem):
    """マインドマップ用エッジ（接続線）。

    2つのノード間を接続し、ノードのドラッグ移動に追従する。
    描画スタイルは Router Pattern により切り替え可能。
    """

    # Style Defaults
    DEFAULT_COLOR: str = "#5c7caa"
    HOVER_COLOR: str = "#7c9cca"
    SELECTED_COLOR: str = "#6c9fff"
    LINE_WIDTH: float = 2.5
    ARROW_SIZE: float = 12.0

    def __init__(
        self,
        source_node: "MindMapNode",
        target_node: "MindMapNode",
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        """MindMapEdgeを初期化する。

        Args:
            source_node: 接続元ノード。
            target_node: 接続先ノード。
            parent: 親アイテム。
        """
        super().__init__(parent)

        self._uuid: str = str(uuid.uuid4())
        self._source: "MindMapNode" = source_node
        self._target: "MindMapNode" = target_node

        # Router Pattern
        self._router: EdgeRouter = BezierRouter()

        # Style
        self._color: QColor = QColor(self.DEFAULT_COLOR)
        self._line_width: float = self.LINE_WIDTH
        self._show_arrow: bool = True

        # State
        self._is_hovered: bool = False

        # ノードにエッジを登録
        self._source.add_edge(self)
        self._target.add_edge(self)

        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)  # ノードより下に描画

        # 初期パスを計算
        self.update_path()

        logger.debug(
            f"MindMapEdge created: {self._uuid[:8]}... from {source_node.uuid[:8]}... to {target_node.uuid[:8]}..."
        )

    # ==========================================
    # Properties
    # ==========================================

    @property
    def uuid(self) -> str:
        """エッジの一意識別子。"""
        return self._uuid

    @property
    def source_node(self) -> "MindMapNode":
        """接続元ノード。"""
        return self._source

    @property
    def target_node(self) -> "MindMapNode":
        """接続先ノード。"""
        return self._target

    # ==========================================
    # Path Calculation
    # ==========================================

    def set_router(self, router: EdgeRouter) -> None:
        """描画ルーターを変更する。"""
        self._router = router
        self.update_path()

    def update_path(self) -> None:
        """ノード位置に基づいてパスを再計算する。"""
        if self._source is None or self._target is None:
            return

        # Router に委譲
        path = self._router.create_path(self._source, self._target)

        self.setPath(path)
        self.update_visibility()

    def update_visibility(self) -> None:
        """接続ノードの表示状態に基づいてエッジの表示を更新する。"""
        if self._source is None or self._target is None:
            return

        # 両方のノードが表示されている場合のみエッジを表示
        visible = self._source.isVisible() and self._target.isVisible()
        self.setVisible(visible)

    # ==========================================
    # QGraphicsItem Override
    # ==========================================

    def boundingRect(self) -> QRectF:
        """バウンディングボックスを返す。"""
        rect = super().boundingRect()
        # マージンを追加
        margin = self._line_width + self.ARROW_SIZE
        return rect.adjusted(-margin, -margin, margin, margin)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """エッジを描画する。"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 色（選択/ホバー/通常）
        if self.isSelected():
            color = QColor(self.SELECTED_COLOR)
            width = self._line_width + 1
        elif self._is_hovered:
            color = QColor(self.HOVER_COLOR)
            width = self._line_width + 0.5
        else:
            color = self._color
            width = self._line_width

        # パス描画
        pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        # 矢印描画
        if self._show_arrow:
            self._draw_arrow(painter, color)

    def _draw_arrow(self, painter: QPainter, color: QColor) -> None:
        """矢印を描画する。"""
        path = self.path()
        if path.isEmpty():
            return

        # パスの終端の方向を取得
        length = path.length()
        if length < 10:
            return

        # 終点と少し手前の点
        end_point = path.pointAtPercent(1.0)
        prev_point = path.pointAtPercent(max(0, (length - 15) / length))

        # 方向ベクトル
        dx = end_point.x() - prev_point.x()
        dy = end_point.y() - prev_point.y()
        dist = (dx**2 + dy**2) ** 0.5

        if dist == 0:
            return

        # 正規化
        dx /= dist
        dy /= dist

        # 矢印のサイズ
        arrow_size = self.ARROW_SIZE

        # 矢印の頂点を計算
        arrow_p1 = QPointF(
            end_point.x() - arrow_size * dx + (arrow_size / 2) * dy,
            end_point.y() - arrow_size * dy - (arrow_size / 2) * dx,
        )
        arrow_p2 = QPointF(
            end_point.x() - arrow_size * dx - (arrow_size / 2) * dy,
            end_point.y() - arrow_size * dy + (arrow_size / 2) * dx,
        )

        # 矢印を描画
        arrow = QPolygonF([end_point, arrow_p1, arrow_p2])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow)

    # ==========================================
    # Event Handlers
    # ==========================================

    def hoverEnterEvent(self, event) -> None:
        """ホバー開始。"""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """ホバー終了。"""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event) -> None:
        """右クリックメニュー。"""
        menu = QMenu()

        # 削除
        delete_action = menu.addAction(tr("mm_menu_delete_conn"))
        delete_action.triggered.connect(self.remove)

        # 方向反転
        reverse_action = menu.addAction(tr("mm_menu_reverse_conn"))
        reverse_action.triggered.connect(self._reverse_direction)

        menu.exec(event.screenPos())
        event.accept()

    # ==========================================
    # Public Methods
    # ==========================================

    def remove(self) -> None:
        """エッジを削除する。"""
        # ノードからの参照を解除
        self._source.remove_edge(self)
        self._target.remove_edge(self)

        # シーンから削除
        scene = self.scene()
        if scene is not None:
            scene.removeItem(self)

        logger.info(f"Edge deleted: {self._uuid[:8]}...")

    def _reverse_direction(self) -> None:
        """接続方向を反転する。"""
        self._source, self._target = self._target, self._source
        self.update_path()
        logger.debug(f"Edge {self._uuid[:8]}... direction reversed")

    def set_color(self, color: QColor) -> None:
        """エッジの色を設定する。"""
        self._color = color
        self.update()

    def set_show_arrow(self, show: bool) -> None:
        """矢印の表示/非表示を設定する。"""
        self._show_arrow = show
        self.update()

    # ==========================================
    # Serialization
    # ==========================================

    def to_dict(self) -> dict:
        """エッジを辞書形式にシリアライズする。"""
        return {
            "uuid": self._uuid,
            "source_uuid": self._source.uuid,
            "target_uuid": self._target.uuid,
            "style": {
                "color": self._color.name(),
                "line_width": self._line_width,
                "show_arrow": self._show_arrow,
            },
        }
