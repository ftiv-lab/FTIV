from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class NodeRenderer(ABC):
    """ノード描画のための抽象基底クラス。"""

    @abstractmethod
    def paint(self, painter: QPainter, node: "MindMapNode") -> None:
        """ノード本体を描画する。

        Args:
            painter: QPainter インスタンス。
            node: 描画対象の MindMapNode。
        """
        pass


class SimpleNodeRenderer(NodeRenderer):
    """シンプルモード用レンダラー。"""

    def paint(self, painter: QPainter, node: "MindMapNode") -> None:
        """シンプルモードで描画する。"""
        # 背景色（ホバー/通常）
        # node は _is_hovered, _bg_color などの属性を持っている前提
        # インターフェース経由でのアクセスが望ましいが、リファクタリングの段階的適用のため直接アクセスを許容
        bg_color = QColor(node.HOVER_BG_COLOR) if getattr(node, "_is_hovered", False) else node._bg_color

        # ボーダー（選択時/通常）
        if node.isSelected():
            pen = QPen(QColor(node.SELECTED_BORDER_COLOR), 3)
        else:
            pen = QPen(node._border_color, 2)

        painter.setPen(pen)
        painter.setBrush(QBrush(bg_color))

        # 角丸長方形
        rect = QRectF(0, 0, node._width, node._height)
        painter.drawRoundedRect(rect, node.CORNER_RADIUS, node.CORNER_RADIUS)

        # テキスト（編集モード中は描画しない）
        if not getattr(node, "_editing_mode", False):
            painter.setPen(node._text_color)
            painter.setFont(node._font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, node._text)


class TextNodeRenderer(NodeRenderer):
    """TextRenderer を使用した高機能レンダラー。"""

    def paint(self, painter: QPainter, node: "MindMapNode") -> None:
        """TextRenderer を使用して描画する。"""
        # 編集モード中は背景のみ描画（QGraphicsTextItem と被らないように）
        if getattr(node, "_editing_mode", False):
            self._paint_background_only(painter, node)
            return

        if node.config is None or node._text_renderer is None:
            return

        # config のテキストを同期（念のため）
        if node.config.text != node._text:
            node.config.text = node._text

        # MindMapTextAdapter のインポートはメソッド内で行う（循環参照回避）
        from ui.mindmap.mindmap_text_adapter import MindMapTextAdapter

        adapter = MindMapTextAdapter(node.config)

        # 直接描画
        canvas_size = node._text_renderer.paint_direct(painter, adapter, None)

        # ノードサイズを更新 (描画中にサイズが変わるのは副作用として微妙だが、現状のロジックを踏襲)
        if canvas_size.width() > 0 and canvas_size.height() > 0:
            node._width = float(canvas_size.width())
            node._height = float(canvas_size.height())

        # 選択時のボーダー強調 (TextRendererモード特有の処理)
        if node.isSelected():
            pen = QPen(QColor(node.SELECTED_BORDER_COLOR), 3)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            rect = QRectF(0, 0, node._width, node._height)
            corner_radius = node.config.font_size * node.config.background_corner_ratio
            # TextRendererの角丸に合わせて描画
            painter.drawRoundedRect(rect, corner_radius, corner_radius)

    def _paint_background_only(self, painter: QPainter, node: "MindMapNode") -> None:
        """編集モード中に背景のみを描画する。"""
        if node.config is None:
            return

        from PySide6.QtGui import QBrush

        bg_color = QColor(node.config.background_color)
        border_color = QColor(node.config.border_color)
        corner_radius = node.config.font_size * node.config.background_corner_ratio

        rect = QRectF(0, 0, node._width, node._height)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, corner_radius, corner_radius)
