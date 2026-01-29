import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QCursor, QDesktopServices
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode

logger = logging.getLogger(__name__)


class NodeInteractionHandler:
    """MindMapNode のインタラクション（マウスイベント）を処理するハンドラ。

    MindMapNode (View/Data) からイベント処理ロジックを分離し、
    State Pattern 等の導入を容易にするために独立化。
    """

    def __init__(self, node: "MindMapNode"):
        """初期化。

        Args:
            node: 操作対象のノード。
        """
        self.node = node
        self._is_handling = False  # イベント処理中フラグ
        self._drag_start_pos: Optional[QPointF] = None

    def handle_mouse_press(self, event: QGraphicsSceneMouseEvent) -> bool:
        """マウスプレスイベントを処理する。

        Returns:
            bool: イベントを消費したか (True=消費, False=無視)
        """
        pos = event.pos()

        # 1. Fold Button Check
        if self.node.has_children():
            # MindMapNode に _get_fold_button_rect がある前提 (リファクタリング過渡期)
            # 将来的には FoldingManager に委譲すべきだが、まずはイベント分離から。
            btn_rect = self.node._get_fold_button_rect()
            if btn_rect.contains(pos):
                self.node.toggle_fold()
                event.accept()
                return True

        # 2. Link Icon Check
        # _link_icon_rect は描画時に更新される
        link_rect = getattr(self.node, "_link_icon_rect", None)
        if link_rect and link_rect.contains(pos):
            if self.node.config and self.node.config.hyperlink:
                url = QUrl(self.node.config.hyperlink)
                QDesktopServices.openUrl(url)
                event.accept()
                return True

        # 3. Default (Selection / Move)
        # 記録開始
        self._drag_start_pos = event.scenePos()

        # Superへ委譲
        return False

    def handle_mouse_move(self, event: QGraphicsSceneMouseEvent) -> bool:
        """マウス移動イベントを処理する。"""
        # 現状、MindMapNode の mouseMoveEvent は super への委譲のみなので、
        # 特殊な処理は不要。
        return False

    def handle_mouse_double_click(self, event: QGraphicsSceneMouseEvent) -> bool:
        """ダブルクリックイベントを処理する。"""
        pos = event.pos()

        # ボタン上でのダブルクリックは無視（連打で開閉と編集が暴発するのを防ぐ）
        if self.node.has_children():
            btn_rect = self.node._get_fold_button_rect()
            if btn_rect.contains(pos):
                event.ignore()
                return True

        # インプレース編集開始
        # _start_inline_edit はまだ Node にある
        self.node._start_inline_edit()
        event.accept()
        return True

    def handle_mouse_release(self, event: QGraphicsSceneMouseEvent) -> bool:
        """マウスリリースイベントを処理する。"""
        # ドラッグ終了判定
        if self._drag_start_pos is not None:
            # ドラッグ処理は完了
            # (is_manual_positionフラグは廃止 - モード管理に移行)
            self._drag_start_pos = None

        return False

    def handle_hover_move(self, event) -> None:
        """ホバー移動イベントを処理する（カーソル変更など）。"""
        pos = event.pos()

        # 折りたたみボタンのホバー処理
        if self.node.has_children():
            btn_rect = self.node._get_fold_button_rect()
            is_over = btn_rect.contains(pos)

            # _is_button_hovered 属性を操作（Viewの状態）
            current_hover = getattr(self.node, "_is_button_hovered", False)
            if current_hover != is_over:
                self.node._is_button_hovered = is_over
                self.node.update()  # View更新

                if is_over:
                    self.node.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                else:
                    self.node.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # リンクアイコンのホバー処理（必要なら追加）
