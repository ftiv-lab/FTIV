# ui/mindmap/mindmap_canvas.py
"""
マインドマップ専用キャンバス。

QGraphicsView + QGraphicsScene ベースのキャンバスで、
ズーム、パン、ノード/エッジの配置を提供する。
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode

from utils.translator import tr

logger = logging.getLogger(__name__)


class MindMapCanvas(QGraphicsView):
    """マインドマップ専用キャンバス。

    Features:
        - 初期サイズ 3000x3000、動的拡張（最大 10000x10000）
        - マウスホイールでズーム
        - ドラッグでパン
        - 背景色カスタマイズ
        - 初期表示は中央

    Signals:
        sig_node_added: ノードが追加された際に発火。
        sig_canvas_clicked: キャンバスがクリックされた際に発火（座標含む）。
    """

    # Constants
    INITIAL_SIZE: int = 3000
    MAX_SIZE: int = 10000
    EXPAND_THRESHOLD: int = 200
    EXPAND_AMOUNT: int = 1000
    DEFAULT_BG_COLOR: str = "#1e1e2e"  # Dark background
    GRID_SIZE: int = 50
    GRID_COLOR: str = "#2a2a3a"

    # Signals
    sig_add_node_requested = Signal(QPointF)
    sig_canvas_clicked = Signal(QPointF)
    sig_zoom_changed = Signal(float)
    sig_node_added = Signal(object)  # MindMapNode

    def __init__(self, parent=None) -> None:
        """MindMapCanvasを初期化する。

        Args:
            parent: 親ウィジェット。
        """
        super().__init__(parent)

        # Scene 初期化（中心が 0,0 になるように設定）
        self._scene = QGraphicsScene(self)
        half = self.INITIAL_SIZE / 2
        self._scene.setSceneRect(-half, -half, self.INITIAL_SIZE, self.INITIAL_SIZE)
        self.setScene(self._scene)

        # ズーム設定
        self._zoom_factor: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 3.0

        # 背景色
        self._bg_color: QColor = QColor(self.DEFAULT_BG_COLOR)
        self._grid_enabled: bool = True
        self._grid_color: QColor = QColor(self.GRID_COLOR)

        # 表示設定
        self._setup_view()

        # 初期表示は中央
        self.center_view()

        logger.info(f"MindMapCanvas initialized with size {self.INITIAL_SIZE}x{self.INITIAL_SIZE}")

    def _setup_view(self) -> None:
        """ビューの初期設定を行う。"""
        # レンダリング設定
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # ドラッグモード（パン操作）
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # スクロールバー非表示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 背景色
        self.setBackgroundBrush(self._bg_color)

        # フレームなし
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    # ==========================================
    # Public API
    # ==========================================

    def center_view(self) -> None:
        """ビューを中央（0, 0）にリセットする。"""
        self.centerOn(0, 0)
        logger.debug("View centered at (0, 0)")

    def reset_zoom(self) -> None:
        """ズームをリセットする（100%）。"""
        self.set_zoom(1.0)

    def set_zoom(self, zoom_factor: float) -> None:
        """ズームを指定値に設定する。

        Args:
            zoom_factor: ズーム倍率 (1.0 = 100%)
        """
        clamped = max(self._min_zoom, min(zoom_factor, self._max_zoom))
        self.resetTransform()
        self.scale(clamped, clamped)
        self._zoom_factor = clamped
        self.sig_zoom_changed.emit(self._zoom_factor)
        logger.debug(f"Zoom set to {self._zoom_factor:.2f}x")

    def fit_all_nodes(self) -> None:
        """全ノードが表示されるようにビューを調整する。"""
        items = self._scene.items()
        if not items:
            self.center_view()
            return

        # 全アイテムのバウンディングボックスを計算
        rect = self._scene.itemsBoundingRect()
        # マージンを追加
        margin = 100
        rect.adjust(-margin, -margin, margin, margin)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

        # ズームファクターを更新
        # ズームファクターを更新
        self._zoom_factor = self.transform().m11()
        self.sig_zoom_changed.emit(self._zoom_factor)
        logger.debug(f"Fitted to all nodes, zoom: {self._zoom_factor:.2f}")

    def set_background_color(self, color: QColor) -> None:
        """背景色を設定する。

        Args:
            color: 新しい背景色。
        """
        self._bg_color = color
        self.setBackgroundBrush(color)
        logger.debug(f"Background color set to {color.name()}")

    def set_grid_enabled(self, enabled: bool) -> None:
        """グリッド表示を切り替える。

        Args:
            enabled: True でグリッド表示。
        """
        self._grid_enabled = enabled
        self.viewport().update()

    def get_scene_pos_at_center(self) -> QPointF:
        """現在のビュー中央のシーン座標を取得する。"""
        return self.mapToScene(self.viewport().rect().center())

    # ==========================================
    # Event Handlers
    # ==========================================

    def wheelEvent(self, event: QWheelEvent) -> None:
        """マウスホイールでズームする。"""
        zoom_in = event.angleDelta().y() > 0
        factor = 1.15 if zoom_in else 1 / 1.15

        new_zoom = self._zoom_factor * factor
        # 範囲内にクランプ（300% に到達可能に）
        new_zoom = max(self._min_zoom, min(new_zoom, self._max_zoom))

        if new_zoom != self._zoom_factor:
            # 実際のスケール比率を計算
            actual_factor = new_zoom / self._zoom_factor
            # マウス位置を中心にズーム
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            self.scale(actual_factor, actual_factor)
            self._zoom_factor = new_zoom
            self.sig_zoom_changed.emit(self._zoom_factor)
            logger.debug(f"Zoom: {self._zoom_factor:.2f}x")

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """背景を描画する（グリッド付き）。"""
        # ベース背景
        painter.fillRect(rect, self._bg_color)

        # グリッド描画
        if self._grid_enabled:
            self._draw_grid(painter, rect)

    def _draw_grid(self, painter: QPainter, rect: QRectF) -> None:
        """グリッド線を描画する。"""
        pen = QPen(self._grid_color, 1)
        painter.setPen(pen)

        # グリッド間隔
        grid = self.GRID_SIZE

        # 開始位置（グリッドに揃える）
        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)

        # 縦線
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid

        # 横線
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid

    def mousePressEvent(self, event) -> None:
        """マウス押下イベント。"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # 中クリックでパンモード
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """ダブルクリックでノード追加。"""
        scene_pos = self.mapToScene(event.pos())

        # アイテム上でなければキャンバスクリック
        item = self.itemAt(event.pos())
        if item is None:
            self.sig_canvas_clicked.emit(scene_pos)
            logger.debug(f"Canvas double-clicked at {scene_pos}")
        else:
            super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        """右クリックメニュー。"""
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())

        if item is None:
            # キャンバス上の右クリック
            self._show_canvas_context_menu(event.globalPos(), scene_pos)
        else:
            # アイテム上の右クリック（アイテムに委譲）
            super().contextMenuEvent(event)

    def _show_canvas_context_menu(self, global_pos, scene_pos: QPointF) -> None:
        """キャンバス右クリックメニューを表示する。"""
        from PySide6.QtWidgets import QMenu

        from utils.translator import tr

        menu = QMenu(self)

        # ノード追加
        add_node_action = menu.addAction(tr("mm_add_node"))
        add_node_action.triggered.connect(lambda: self._add_node_at(scene_pos))

        # Paste (Markdown)
        paste_action = menu.addAction("Paste Node Tree (Markdown)")
        # Widget経由でPaste呼び出し
        if self.parent() and hasattr(self.parent(), "_handle_paste"):
            paste_action.triggered.connect(self.parent()._handle_paste)

        menu.addSeparator()

        # ビュー操作
        center_action = menu.addAction(tr("mm_canvas_center_view"))
        center_action.triggered.connect(self.center_view)

        fit_action = menu.addAction(tr("mm_canvas_fit_all"))
        fit_action.triggered.connect(self.fit_all_nodes)

        reset_zoom_action = menu.addAction(tr("mm_canvas_reset_zoom"))
        reset_zoom_action.triggered.connect(self.reset_zoom)

        # Copy Entire Map (Markdown)
        menu.addSeparator()
        copy_all_action = menu.addAction("Copy Entire Map as Markdown")
        copy_all_action.triggered.connect(self._copy_all_as_markdown)

        menu.exec(global_pos)

    def _copy_all_as_markdown(self):
        """マップ全体をMarkdownとしてクリップボードにコピーする。"""
        if hasattr(self, "controller") and self.controller:
            self.controller.copy_all_as_markdown()

    def _add_node_at(self, pos: QPointF) -> None:
        """指定位置にノードを追加する。"""
        # Widget経由で追加するためにシグナル発行
        self.sig_add_node_requested.emit(pos)

    # ==========================================
    # Structural Editing
    # ==========================================

    def add_child_node(self, parent_node: "MindMapNode" = None) -> "MindMapNode":
        """子ノードを追加する。"""
        from ui.mindmap.mindmap_edge import MindMapEdge
        from ui.mindmap.mindmap_node import MindMapNode

        if parent_node is None:
            # 選択中のノードを使用
            items = self._scene.selectedItems()
            nodes = [i for i in items if isinstance(i, MindMapNode)]
            if not nodes:
                return None
            parent_node = nodes[0]  # 複数選択時は先頭のみ

        # 位置計算 (親の右側)
        # 既存の子ノードがあればその下に追加するなどのインテリジェンスは後で
        offset_x = 200
        offset_y = 0

        # 既存の子ノードの数に応じて少しずらす（簡易的）
        child_count = len(parent_node.get_child_nodes())
        offset_y = child_count * 50

        new_pos = QPointF(parent_node.x() + offset_x, parent_node.y() + offset_y)

        # ノード作成
        new_node = MindMapNode(tr("mm_new_node"), position=new_pos)

        # スタイル適用 (Widget経由ではないのでデフォルトスタイル適用はWidget側で監視するか、ここでやるか)
        # ここでは最低限の作成のみ。Widget側で canvas.add_node を呼ぶほうが一貫性があるが、
        # 親子関係構築が必要なのでここでやる。

        self._scene.addItem(new_node)

        # エッジ作成
        edge = MindMapEdge(parent_node, new_node)
        self._scene.addItem(edge)

        # 選択切り替え
        self._scene.clearSelection()
        new_node.setSelected(True)

        # シグナル発行
        self.sig_node_added.emit(new_node)

        return new_node

    def add_sibling_node(self, node: "MindMapNode" = None) -> "MindMapNode":
        """兄弟ノードを追加する。"""
        from ui.mindmap.mindmap_node import MindMapNode

        if node is None:
            items = self._scene.selectedItems()
            nodes = [i for i in items if isinstance(i, MindMapNode)]
            if not nodes:
                return None
            node = nodes[0]

        # 親を探す
        parent_node = None
        for edge in node.edges:
            if edge.target_node == node:
                parent_node = edge.source_node
                break

        if parent_node:
            # 親がいる場合 -> 親に子を追加するのと同じだが、位置は「兄」の下
            return self.add_child_node(parent_node)
        else:
            # 親がいない（ルート） -> 別のルートノードを近くに作成
            new_pos = QPointF(node.x(), node.y() + 100)
            new_node = MindMapNode(tr("mm_new_root"), position=new_pos)
            self._scene.addItem(new_node)

            self._scene.clearSelection()
            new_node.setSelected(True)
            self.sig_node_added.emit(new_node)
            return new_node

    def delete_selected_items(self) -> None:
        """選択中のノード・エッジを削除する。"""
        from ui.mindmap.mindmap_edge import MindMapEdge
        from ui.mindmap.mindmap_node import MindMapNode

        items = self._scene.selectedItems()
        if not items:
            return

        # ノードとエッジを分離
        nodes_to_delete = []
        edges_to_delete = []

        for item in items:
            if isinstance(item, MindMapNode):
                nodes_to_delete.append(item)
            elif isinstance(item, MindMapEdge):
                edges_to_delete.append(item)

        # ノード削除時、接続されているエッジも削除リストに追加
        for node in nodes_to_delete:
            # コピーして走査（削除によりリストが変わるのを防ぐため）
            connected_edges = list(node.edges)
            for edge in connected_edges:
                if edge not in edges_to_delete:
                    edges_to_delete.append(edge)

        # 削除実行
        for edge in edges_to_delete:
            # ノード側の参照から削除
            if edge.source_node and edge in edge.source_node.edges:
                edge.source_node.edges.remove(edge)
            if edge.target_node and edge in edge.target_node.edges:
                edge.target_node.edges.remove(edge)
            self._scene.removeItem(edge)

        for node in nodes_to_delete:
            self._scene.removeItem(node)

        logger.info(f"Deleted {len(nodes_to_delete)} nodes and {len(edges_to_delete)} edges")

    # ==========================================
    # Canvas Expansion
    # ==========================================

    def check_and_expand_canvas(self, item_pos: QPointF) -> bool:
        """ノード位置に応じてキャンバスを拡張する。

        Args:
            item_pos: アイテムのシーン座標。

        Returns:
            bool: 拡張が行われた場合 True。
        """
        rect = self._scene.sceneRect()
        expanded = False
        max_half = self.MAX_SIZE / 2

        # 各辺のチェック
        if item_pos.x() > rect.right() - self.EXPAND_THRESHOLD:
            new_right = min(rect.right() + self.EXPAND_AMOUNT, max_half)
            if new_right > rect.right():
                rect.setRight(new_right)
                expanded = True

        if item_pos.x() < rect.left() + self.EXPAND_THRESHOLD:
            new_left = max(rect.left() - self.EXPAND_AMOUNT, -max_half)
            if new_left < rect.left():
                rect.setLeft(new_left)
                expanded = True

        if item_pos.y() > rect.bottom() - self.EXPAND_THRESHOLD:
            new_bottom = min(rect.bottom() + self.EXPAND_AMOUNT, max_half)
            if new_bottom > rect.bottom():
                rect.setBottom(new_bottom)
                expanded = True

        if item_pos.y() < rect.top() + self.EXPAND_THRESHOLD:
            new_top = max(rect.top() - self.EXPAND_AMOUNT, -max_half)
            if new_top < rect.top():
                rect.setTop(new_top)
                expanded = True

        if expanded:
            self._scene.setSceneRect(rect)
            logger.info(f"Canvas expanded to {rect.width()}x{rect.height()}")

        return expanded

    def export_to_image(self, file_path: str, format: str = "PNG") -> bool:
        """マインドマップ全体を画像としてエクスポートする。

        Args:
            file_path: 保存先のファイルパス。
            format: 画像フォーマット ("PNG", "JPG" など)。

        Returns:
            bool: 成功したかどうか。
        """
        try:
            # 選択を一時解除（選択枠を描画しないため）
            selected_items = self._scene.selectedItems()
            for item in selected_items:
                item.setSelected(False)

            # 全アイテムのバウンディングボックスを取得
            rect = self._scene.itemsBoundingRect()
            if rect.isEmpty():
                logger.warning("No items to export")
                return False

            # マージンを追加
            margin = 50
            rect.adjust(-margin, -margin, margin, margin)

            # 画像を作成
            image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)

            # 描画
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # 背景色で塗りつぶし
            painter.fillRect(image.rect(), self._bg_color)

            # グリッド描画（オプション: エクスポート時はグリッドを含めるかどうか？一旦含める）
            if self._grid_enabled:
                # グリッドの原点を調整して描画する必要があるが、
                # 簡易的に drawBackground のロジックを再利用するのは難しい（座標系が違う）。
                # シーンの render を使うので、シーン背景として設定されていれば描画されるはずだが、
                # ここでは QImage 上に直接描画している。
                # MindMapCanvas.drawBackground は View 依存なので再利用しにくい。
                # 今回はグリッドはエクスポートしない仕様とする（きれいなマップを出力するため）。
                pass

            # シーンを描画
            # target rect (image), source rect (scene)
            self._scene.render(painter, target=QRectF(image.rect()), source=rect)
            painter.end()

            # 保存
            success = image.save(file_path, format)

            # 選択を復元
            for item in selected_items:
                item.setSelected(True)

            if success:
                logger.info(f"MindMap exported to {file_path}")
            else:
                logger.error(f"Failed to save image to {file_path}")

            return success

        except Exception as e:
            logger.error(f"Error during export: {e}")
            return False

    def keyPressEvent(self, event) -> None:
        """キー入力イベント。

        矢印キーによるナビゲーションを処理する。
        """
        # ナビゲーション処理
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            if hasattr(self, "controller") and self.controller:
                if self.controller.navigate(event.key()):
                    event.accept()
                    return

        super().keyPressEvent(event)
