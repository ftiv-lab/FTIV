# ui/mindmap/mindmap_node.py
"""
マインドマップ用ノード。

QGraphicsItem ベースのノードで、ドラッグ移動、選択、
テキスト編集、スタイル変更をサポートする。
TextRenderer 統合により、高度なテキストスタイリング（縁取り、影、グラデーション）に対応。
"""

import logging
import uuid
from typing import TYPE_CHECKING, Any, List, Optional

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

from models.mindmap_node_config import MindMapNodeConfig
from ui.mindmap.renderers.node_renderer import SimpleNodeRenderer, TextNodeRenderer
from utils.translator import tr
from windows.text_renderer import TextRenderer

if TYPE_CHECKING:
    from ui.mindmap.mindmap_edge import MindMapEdge

from ui.mindmap.components.folding_manager import FoldingManager
from ui.mindmap.components.node_interaction_handler import NodeInteractionHandler

logger = logging.getLogger(__name__)


class MindMapNode(QObject, QGraphicsItem):
    """マインドマップ用ノード。

    Attributes:
        text: ノードのテキスト。
        uuid: ノードの一意識別子。
        edges: 接続されているエッジのリスト。
        sig_position_changed: 位置が変更されたときに発火するシグナル。
    """

    sig_position_changed = Signal(QPointF)
    sig_request_set_as_default = Signal(object)  # MindMapNodeConfig を送信

    def _set_as_default_style(self) -> None:
        """現在の設定をデフォルトスタイルとして適用する（Signal発行）。"""
        if self.config:
            self.sig_request_set_as_default.emit(self.config)

    # Node Style Defaults
    DEFAULT_WIDTH: int = 150
    DEFAULT_HEIGHT: int = 60
    MIN_WIDTH: int = 80
    MAX_WIDTH: int = 400
    PADDING: int = 8
    CORNER_RADIUS: int = 12

    # Integrated Fold Button Constants
    FOLD_BUTTON_SIZE = 14
    FOLD_BUTTON_MARGIN = 2

    # Colors (Dark Theme)
    DEFAULT_BG_COLOR: str = "#3c3c5c"
    DEFAULT_BORDER_COLOR: str = "#5c5c8c"
    DEFAULT_TEXT_COLOR: str = "#ffffff"
    SELECTED_BORDER_COLOR: str = "#6c9fff"
    HOVER_BG_COLOR: str = "#4c4c6c"

    def __init__(
        self,
        text: str = "",
        position: Optional[QPointF] = None,
        parent: Optional[QGraphicsItem] = None,
        use_text_renderer: bool = True,
    ) -> None:
        """MindMapNodeを初期化する。

        Args:
            text: ノードのテキスト。
            position: 初期位置（シーン座標）。
            parent: 親アイテム。
            use_text_renderer: TextRenderer を使用した高度なスタイリングを有効化。
        """
        super().__init__(parent)

        self._uuid: str = str(uuid.uuid4())
        self._text: str = text
        self._edges: List["MindMapEdge"] = []
        self._is_expanded: bool = True  # Internal fallback state

        # [REFACTORED] Integrated Fold Button - No explicit child item

        # リンクアイコンの領域
        self._link_icon_rect: Optional[QRectF] = None

        # QGraphicsItem init
        QGraphicsItem.__init__(self, parent)

        # フラグ設定: ItemSendsGeometryChanges を有効化して itemChange を受け取る
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Size (auto-calculated based on text)
        self._width: float = self.DEFAULT_WIDTH
        self._height: float = self.DEFAULT_HEIGHT

        # Style (シンプルモード用)
        self._bg_color: QColor = QColor(self.DEFAULT_BG_COLOR)
        self._border_color: QColor = QColor(self.DEFAULT_BORDER_COLOR)
        self._text_color: QColor = QColor(self.DEFAULT_TEXT_COLOR)
        self._font: QFont = QFont()
        self._font.setFamilies(["Segoe UI", "Segoe UI Emoji", "Apple Color Emoji", "Sans-Serif"])
        self._font.setPointSize(11)
        self._font.setWeight(QFont.Weight.Medium)

        # TextRenderer 統合
        self._use_text_renderer: bool = use_text_renderer
        self._text_renderer: Optional[TextRenderer] = None
        self._config: Optional[MindMapNodeConfig] = None
        self._rendered_pixmap: Optional[QPixmap] = None

        if self._use_text_renderer:
            self._text_renderer = TextRenderer()
            self._config = MindMapNodeConfig(
                uuid=self._uuid,
                text=text,
                font_family="Segoe UI",
                font_size=14,
                font_color="#ffffff",
                background_color=self.DEFAULT_BG_COLOR,
                border_color=self.DEFAULT_BORDER_COLOR,
            )
            self.renderer = TextNodeRenderer()
        else:
            self.renderer = SimpleNodeRenderer()

        # State
        self._is_hovered: bool = False
        self._inline_text_item: Optional[QGraphicsTextItem] = None

        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Set position
        if position is not None:
            self.setPos(position)

        # Calculate initial size
        self._update_size()

        # Helper Component
        self.interaction_handler = NodeInteractionHandler(self)
        self.folding_manager = FoldingManager(self)

        logger.debug(f"MindMapNode created: {self._uuid[:8]}... text='{text}'")

    # ==========================================
    # Properties
    # ==========================================

    @property
    def uuid(self) -> str:
        """ノードの一意識別子。"""
        return self._uuid

    @property
    def text(self) -> str:
        """ノードのテキスト。"""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """テキストを設定し、サイズを再計算する。"""
        self._text = value
        if self._config:
            self._config.text = value
        self._update_size()
        self._update_size()
        self._update_tooltip()
        self.update()

    @property
    def edges(self) -> List["MindMapEdge"]:
        """接続されているエッジのリスト。"""
        return self._edges

    def add_edge(self, edge: "MindMapEdge") -> None:
        """エッジを追加し、UI状態を更新する。"""
        if edge not in self._edges:
            self._edges.append(edge)
            logger.debug(f"Edge added to node {self._uuid[:8]}... Total edges: {len(self._edges)}")
            self.prepareGeometryChange()  # Button might appear now
            self.update()

    def remove_edge(self, edge: "MindMapEdge") -> None:
        """エッジを削除し、UI状態を更新する。"""
        if edge in self._edges:
            self._edges.remove(edge)
            logger.debug(f"Edge removed from node {self._uuid[:8]}... Total edges: {len(self._edges)}")
            self.prepareGeometryChange()
            self.update()

    @property
    def center(self) -> QPointF:
        """ノードの中心座標（シーン座標）。"""
        return self.scenePos() + QPointF(self._width / 2, self._height / 2)

    @property
    def config(self) -> Optional[MindMapNodeConfig]:
        """ノードの MindMapNodeConfig（TextRenderer モード時のみ）。"""
        return self._config

    @property
    def use_text_renderer(self) -> bool:
        """TextRenderer を使用しているかどうか。"""
        return self._use_text_renderer

    def _enable_text_renderer(self) -> None:
        """TextRenderer モードを有効化する（内部使用）。"""
        if not self._use_text_renderer:
            self._use_text_renderer = True
            self._text_renderer = TextRenderer()
            self._config = MindMapNodeConfig(
                uuid=self._uuid,
                text=self._text,
                font_family=self._font.family(),
                font_size=self._font.pointSize(),
                font_color=self._text_color.name(),
                background_color=self._bg_color.name(),
                border_color=self._border_color.name(),
            )
            self._update_tooltip()
            self.renderer = TextNodeRenderer()
            self.update()

    def _disable_text_renderer(self) -> None:
        """TextRenderer モードを無効化する（内部使用）。"""
        if self._use_text_renderer:
            self._use_text_renderer = False
            self._rendered_pixmap = None
            self._update_size()
            self.renderer = SimpleNodeRenderer()
            self.update()

    # ==========================================
    # Integrated Fold Button Methods
    # ==========================================

    def _get_fold_button_rect(self) -> QRectF:
        """ボタンの矩形を取得する（ノード座標系）。"""
        # Config logic: Horizontal or Vertical?
        is_vertical = False
        if self.config:
            is_vertical = self.config.is_vertical

        if is_vertical:
            # Bottom Center
            x = (self._width - self.FOLD_BUTTON_SIZE) / 2
            y = self._height + self.FOLD_BUTTON_MARGIN
        else:
            # Right Center
            x = self._width + self.FOLD_BUTTON_MARGIN
            y = (self._height - self.FOLD_BUTTON_SIZE) / 2

        return QRectF(x, y, self.FOLD_BUTTON_SIZE, self.FOLD_BUTTON_SIZE)

    def _draw_fold_button(self, painter: QPainter) -> None:
        """折りたたみボタンを描画する。"""
        rect = self._get_fold_button_rect()

        # Mouse Hover Check
        is_hovered = getattr(self, "_is_button_hovered", False)
        bg_color = QColor("#FFB040") if is_hovered else QColor("#FF9900")

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawEllipse(rect)

        # Symbol (+/-)
        center = rect.center()
        painter.setPen(QPen(QColor("#ffffff"), 2.0))

        # Horizontal line (-)
        painter.drawLine(QPointF(center.x() - 3, center.y()), QPointF(center.x() + 3, center.y()))

        # Vertical line (+) if folded
        if not self.is_expanded:
            painter.drawLine(QPointF(center.x(), center.y() - 3), QPointF(center.x(), center.y() + 3))

    # ==========================================
    # QGraphicsItem Override
    # ==========================================

    def boundingRect(self) -> QRectF:
        """バウンディングボックスを返す（ボタンを含む）。"""
        margin = 3
        base_rect = QRectF(-margin, -margin, self._width + margin * 2, self._height + margin * 2)

        if self.has_children():
            btn_rect = self._get_fold_button_rect()
            return base_rect.united(btn_rect)

        return base_rect

    def shape(self) -> QPainterPath:
        """衝突判定用のシェイプを返す（角丸長方形 + ボタン）。"""
        path = QPainterPath()
        # 本体
        path.addRoundedRect(0, 0, self._width, self._height, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # ボタン領域もヒットテストに含める
        if self.has_children():
            btn_rect = self._get_fold_button_rect()
            path.addEllipse(btn_rect)

        return path

    def raise_(self) -> None:
        """QWidget.raise_() の互換メソッド。Z値を上げて最前面に移動する。"""
        if self.scene():
            max_z = 0.0
            for item in self.scene().items():
                if item.zValue() > max_z:
                    max_z = item.zValue()
            self.setZValue(max_z + 1.0)
        self.update()

    def lower(self) -> None:
        """QWidget.lower() の互換メソッド。Z値を下げて最背面に移動する。"""
        if self.scene():
            min_z = 0.0
            for item in self.scene().items():
                if item.zValue() < min_z:
                    min_z = item.zValue()
            self.setZValue(min_z - 1.0)
        self.update()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """ノードを描画する。"""
        # 描画品質設定
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._use_text_renderer:
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 本体描画
        self.renderer.paint(painter, self)

        # 選択枠描画
        if self.isSelected():
            self._paint_selection_border(painter)

        # 折りたたみボタン描画 (Integrated)
        if self.has_children():
            self._draw_fold_button(painter)

        # 注釈（メモ・リンク）描画
        self._draw_annotations(painter)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """アイテム変更イベント。"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # 接続エッジを更新
            self._update_edges()
            # リアルタイム更新通知
            self.sig_position_changed.emit(value)

            # キャンバス拡張チェック
            scene = self.scene()
            if scene is not None:
                view = scene.views()[0] if scene.views() else None
                if view is not None and hasattr(view, "check_and_expand_canvas"):
                    view.check_and_expand_canvas(self.scenePos())

        return super().itemChange(change, value)

    # ==========================================
    # Event Handlers
    # ==========================================

    def hoverEnterEvent(self, event) -> None:
        """ホバー開始。"""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event) -> None:
        """ホバー移動（ボタンハイライト）。"""
        self.interaction_handler.handle_hover_move(event)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """ホバー終了。"""
        self._is_hovered = False
        self._is_button_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """ダブルクリックでインプレース編集を開始。"""
        if self.interaction_handler.handle_mouse_double_click(event):
            return

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウスリリースイベント。"""
        if self.interaction_handler.handle_mouse_release(event):
            return

        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウスクリックイベント。"""
        if self.interaction_handler.handle_mouse_press(event):
            return

        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """右クリックメニュー。"""
        self._show_context_menu(event.screenPos())
        event.accept()

    # ==========================================
    # Private Methods
    # ==========================================

    def _update_size(self) -> None:
        """テキストに基づいてサイズを再計算する。"""
        # 高機能モードの場合、TextRenderer 用の設定からサイズを計算する方が正確だが、
        # ここでは簡易的にフォントメトリクスを使用し、十分な余白を確保する。

        # フォントサイズに基づいてメトリクスを取得
        font = self._font
        if self._use_text_renderer and self._config:
            # 高機能モードの場合は config のフォントサイズを使用
            font = QFont(self._font)
            font.setPointSize(self._config.font_size)

        metrics = QFontMetricsF(font)
        text_rect = metrics.boundingRect(self._text)

        # パディングを追加
        # 高機能モードの場合、アウトラインや影の分だけ余白を広めに取る
        extra_padding = 0
        if self._use_text_renderer:
            extra_padding = 10  # アウトライン等のマージン
            if self._config:
                # 影やアウトラインの設定値に応じて調整も可能だが、一旦固定値で確保
                extra_padding += self._config.outline_width
                if self._config.second_outline_enabled:
                    extra_padding += self._config.second_outline_width

        padding = self.PADDING + extra_padding

        new_width = text_rect.width() + padding * 2
        new_height = text_rect.height() + padding * 2

        # 最小/最大制限
        self._width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))
        self._height = max(self.DEFAULT_HEIGHT, new_height)

        self.prepareGeometryChange()

    def _update_edges(self) -> None:
        """接続されているエッジを更新する。"""
        for edge in self.edges:
            if hasattr(edge, "update_path"):
                edge.update_path()

    def _start_inline_edit(self) -> None:
        """ネイティブインプレース編集を開始する（ノード内で直接編集）。"""
        if hasattr(self, "_inline_text_item") and self._inline_text_item is not None:
            return  # 既に編集中

        scene = self.scene()
        if scene is None:
            return

        # 再入防止フラグ
        self._is_finishing_edit = False

        # 高機能モードを一時的に無効化（編集中はシンプル表示）
        self._was_text_renderer_enabled = self._use_text_renderer
        if self._use_text_renderer:
            self._use_text_renderer = False  # 編集中はシンプルモード（一時的）

        # ノードを一時的に非表示（編集中は背景を透明に）
        self._editing_mode = True
        self.update()

        # QGraphicsTextItem を作成してノード位置に配置
        self._inline_text_item = QGraphicsTextItem(self._text)

        # フォント設定
        font = self._font
        if self._config:
            font = QFont(self._font)
            font.setPointSize(self._config.font_size)
            # 編集時は左揃えにするため、必要ならここで調整

        self._inline_text_item.setFont(font)

        # テキスト色（編集時は入力しやすさ重視で白など見やすい色固定でも良いが、一旦設定に従う）
        self._inline_text_item.setDefaultTextColor(self._text_color)

        # 編集可能にする
        self._inline_text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

        # 編集しやすいスタイル調整（ダイアログ風）
        # 左揃えで配置するため、オフセット計算を変更
        # rect = self._inline_text_item.boundingRect()  # 未使用のため削除

        # パディングを考慮して配置（左上に寄せる）
        # 高機能モード時の見た目と極端にずれないように調整
        padding = self.PADDING
        if self._config:
            padding += 10  # 簡易的な追加パディング（枠線分など）

        self._inline_text_item.setPos(self.scenePos().x() + padding, self.scenePos().y() + padding)
        self._inline_text_item.setZValue(self.zValue() + 1)

        # 編集枠の幅を制限して折り返しさせる（オプション）
        max_width = self.MAX_WIDTH - padding * 2
        self._inline_text_item.setTextWidth(max_width)

        # シーンに追加
        scene.addItem(self._inline_text_item)

        # フォーカスを設定してカーソルを表示
        self._inline_text_item.setFocus()

        # テキスト全選択
        cursor = self._inline_text_item.textCursor()
        cursor.select(cursor.SelectionType.Document)
        self._inline_text_item.setTextCursor(cursor)

        # キーイベントを監視（Enter/Escape で終了）
        self._inline_text_item.installSceneEventFilter(self)

        # テキスト変更を監視（ノードサイズを動的に更新）
        self._inline_text_item.document().contentsChanged.connect(self._on_inline_text_changed)
        self._on_inline_text_changed()  # 初期サイズ適用

    def _on_inline_text_changed(self) -> None:
        """インプレース編集中にノードサイズを更新する。"""
        if not hasattr(self, "_inline_text_item") or self._inline_text_item is None:
            return

        # テキストアイテムのバウンディングボックスを取得
        rect = self._inline_text_item.boundingRect()
        text_width = rect.width()

        # MAX_WIDTH を超えそうな場合は折り返し幅を設定
        max_text_width = self.MAX_WIDTH - self.PADDING * 2
        if text_width > max_text_width:
            self._inline_text_item.setTextWidth(max_text_width)
            rect = self._inline_text_item.boundingRect()  # 再計算

        # 新しいノードサイズを計算
        new_width = rect.width() + self.PADDING * 2
        new_height = rect.height() + self.PADDING * 2

        self.prepareGeometryChange()
        self._width = max(self.MIN_WIDTH, new_width)
        self._height = max(self.DEFAULT_HEIGHT, new_height)

        # テキストアイテムを中央に配置
        offset_x = (self._width - rect.width()) / 2
        offset_y = (self._height - rect.height()) / 2
        self._inline_text_item.setPos(self.scenePos().x() + offset_x, self.scenePos().y() + offset_y)

        # エッジと再描画を更新
        self._update_edges()
        self.update()

    # ==========================================
    # Serialization
    # ==========================================

    def to_dict(self) -> dict:
        """ノードの状態を辞書形式で返す。"""
        data = {
            "uuid": self._uuid,
            "text": self._text,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "use_text_renderer": self._use_text_renderer,
            "is_expanded": self.is_expanded,
        }
        if self._config:
            data["config"] = self._config.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict, parent: Optional[QGraphicsItem] = None) -> "MindMapNode":
        """辞書形式からノードを生成する。"""
        node = cls(
            text=data.get("text", ""),
            position=QPointF(data.get("x", 0), data.get("y", 0)),
            parent=parent,
            use_text_renderer=data.get("use_text_renderer", True),
        )
        if "uuid" in data:
            node._uuid = data["uuid"]

        if "config" in data and data["config"]:
            node._config = MindMapNodeConfig.from_dict(data["config"])
            node._enable_text_renderer()  # Apply config

        if "is_expanded" in data:
            node.is_expanded = data["is_expanded"]

        return node

    # ==========================================
    # Folding Logic
    # ==========================================

    def has_children(self) -> bool:
        """子ノード（自分からエッジが出ている先）が存在するか判定する。"""
        return any(edge.source_node == self and edge.target_node != self for edge in self.edges)

    def get_child_nodes(self) -> List["MindMapNode"]:
        """直下の子ノードのリストを取得する。"""
        return [edge.target_node for edge in self.edges if edge.source_node == self and edge.target_node != self]

    @property
    def is_expanded(self) -> bool:
        """展開状態を取得する（Managerへ委譲）。"""
        return self.folding_manager.is_expanded()

    @is_expanded.setter
    def is_expanded(self, value: bool) -> None:
        """展開状態を設定する（Managerへ委譲）。"""
        self.folding_manager.set_expanded(value)

    def toggle_fold(self) -> None:
        """折りたたみ状態を切り替える（Managerへ委譲）。"""
        self.folding_manager.toggle_fold()

    def update_children_visibility(self, visible: bool) -> None:
        """子ノードの表示状態を更新する。"""
        self.folding_manager.update_children_visibility(self, visible)

    def _draw_annotations(self, painter: QPainter) -> None:
        """注釈（メモ・リンク）アイコンを描画する。"""
        if not self.config:
            return

        has_memo = bool(self.config.memo)
        has_link = bool(self.config.hyperlink)

        if not has_memo and not has_link:
            self._link_icon_rect = None
            return

        rect = self.boundingRect()
        icon_size = 14
        margin = 2

        # 右上に配置
        # 位置調整は簡易的に
        x = rect.right() + margin
        y = rect.top()

        current_x = x
        current_y = y

        # メモアイコン
        if has_memo:
            # 📝
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QPointF(current_x, current_y + 10), "📝")
            current_x += icon_size + 2

        # リンクアイコン
        if has_link:
            # 🔗
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QPointF(current_x, current_y + 10), "🔗")

            # ヒットテスト用Rect
            self._link_icon_rect = QRectF(current_x, current_y, icon_size, icon_size)
            current_x += icon_size + 2
        else:
            self._link_icon_rect = None

        # ユーザー指定アイコン (Priority)
        if self.config.icon:
            # アイコンがある場合、ノードの左側（テキストの前）に描画するか、右上に並べるか？
            # ここでは「右上に並べる」方式で統一する（GitMind風のアノテーションとして）。
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QPointF(current_x, current_y + 10), self.config.icon)
            current_x += icon_size + 2

    def _update_tooltip(self) -> None:
        """ツールチップを更新する。"""
        if not self.config:
            self.setToolTip(self.text)
            return

        tooltip = f"<b>{self.text}</b>"

        if self.config.memo:
            memo_preview = self.config.memo[:100] + "..." if len(self.config.memo) > 100 else self.config.memo
            tooltip += f"<br><br>📝 {memo_preview}"

        if self.config.hyperlink:
            tooltip += f"<br>🔗 {self.config.hyperlink}"

        self.setToolTip(tooltip)

    def _paint_selection_border(self, painter: QPainter) -> None:
        """選択枠を描画する（メソッド切り出し）。"""
        rect = self.boundingRect()
        painter.setPen(QPen(QColor("#6c9fff"), 2.0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 4, 4)

    def sceneEventFilter(self, watched, event) -> bool:
        """テキストアイテムのキーイベントをフィルタ。"""
        if watched == getattr(self, "_inline_text_item", None):
            from PySide6.QtCore import QEvent

            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                modifiers = event.modifiers()

                # Enter（Shift なし）で確定
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if not (modifiers & Qt.KeyboardModifier.ShiftModifier):
                        self._finish_inline_edit(True)
                        return True

                # Escape でキャンセル
                if key == Qt.Key.Key_Escape:
                    self._finish_inline_edit(False)
                    return True

            # フォーカスアウトで確定
            if event.type() == QEvent.Type.FocusOut:
                if not getattr(self, "_is_finishing_edit", False):
                    from PySide6.QtCore import QTimer

                    QTimer.singleShot(0, lambda: self._finish_inline_edit(True))
                return False

        return False

    def _finish_inline_edit(self, accept: bool) -> None:
        """ネイティブインプレース編集を終了する。

        Args:
            accept: True なら変更を適用、False ならキャンセル。
        """
        # 再入防止
        if getattr(self, "_is_finishing_edit", False):
            return
        if not hasattr(self, "_inline_text_item") or self._inline_text_item is None:
            return

        self._is_finishing_edit = True

        # テキストを取得
        if accept:
            new_text = self._inline_text_item.toPlainText().strip()
            if new_text and new_text != self._text:
                self.text = new_text
                logger.info(f"Node {self._uuid[:8]}... text changed to '{new_text}'")

        # テキストアイテムを削除
        scene = self.scene()
        text_item = self._inline_text_item

        # Cleanup
        self._inline_text_item = None
        self._editing_mode = False

        if scene and text_item:
            scene.removeItem(text_item)

        # Restore state
        self._use_text_renderer = getattr(self, "_was_text_renderer_enabled", True)
        if self._use_text_renderer and self._config:
            self.renderer = TextNodeRenderer()
        else:
            self.renderer = SimpleNodeRenderer()

        self._update_size()
        self.update()

    def _show_context_menu(self, screen_pos) -> None:
        """コンテキストメニューを表示する。"""
        # Import moved inside to avoid circular deps if any, or just local focus

        menu = QMenu()

        # Actions
        # Actions
        menu.addAction(tr("Add Child Node"))
        menu.addAction(tr("Add Sibling Node"))
        menu.addSeparator()
        menu.addAction(tr("Delete Node"))
        menu.addSeparator()
        menu.addAction(tr("Set as Main Topic"))

        menu.exec(screen_pos)

        # Handled by Controller usually, but if we need local logic:
        # Actually MindMapController connects to scene signal or item signal?
        # Usually Controller handles context menu via scene.
        # This local menu is for fallback or specific actions.
        # For FTIV, the controller likely manages this.
        # But we show it here.

        # We need to emit signals to let Controller handle it
        # But MindMapNode doesn't have specific signals for these actions yet?
        # Assuming Controller intercepts the event or we just use this for visuals.
        pass
