"""ui/tabs/layer_tab.py

LayerタブUI — MainWindow 内で親子ウィンドウ構造を可視化・操作するパネル。

QTreeWidget で親/子 Window をツリー表示し、
Attach / Detach / Move Up / Move Down 操作を提供する。

ショートカット契約: docs/RUNBOOK.md §11
 - Shift ショートカットは未割り当て（Connector/Layer の両方で使わない）。
 - Layer 操作の主導線は LayerタブUI / 右クリックメニュー。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)

# ウィンドウ種別テキストアイコン
_ICON_TEXT = "📝"
_ICON_IMAGE = "🖼"

# 状態バッジ（ラベル末尾に付与）
_BADGE_HIDDEN = " [H]"
_BADGE_LOCKED = " [L]"
_BADGE_FRONT = " [F]"


def _window_label(window: Any) -> str:
    """ツリー表示用のラベル文字列を生成する。"""
    try:
        from windows.image_window import ImageWindow
        from windows.text_window import TextWindow

        if isinstance(window, TextWindow):
            icon = _ICON_TEXT
            raw = getattr(window.config, "text", "") or ""
            name = raw.replace("\n", " ").strip()[:24] or "(空)"
        elif isinstance(window, ImageWindow):
            icon = _ICON_IMAGE
            path = getattr(window, "image_path", "") or ""
            basename = path.replace("\\", "/").split("/")[-1] if path else ""
            name = basename[:24] if basename else "(画像)"
        else:
            icon = "□"
            name = str(getattr(window, "uuid", "?"))[:8]

        badges = ""
        if getattr(window, "is_hidden", False):
            badges += _BADGE_HIDDEN
        if getattr(window, "is_locked", False):
            badges += _BADGE_LOCKED
        if getattr(window, "is_frontmost", False):
            badges += _BADGE_FRONT

        return f"{icon} {name}{badges}"
    except Exception:
        return "?"


class LayerTab(QWidget):
    """Layerタブ: 親子ウィンドウ構造を可視化・操作するパネル。

    双方向同期:
      - キャンバス選択変更 (sig_selection_changed) → ツリー選択ハイライト
      - ツリー選択変更 → キャンバスウィンドウを raise_()
      - Layer 構造変更 (sig_layer_structure_changed) → rebuild()
    """

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window
        self._rebuilding = False
        self._uuid_to_item: dict[str, QTreeWidgetItem] = {}
        self._attach_parent_candidate_uuid: Optional[str] = None
        self._setup_ui()
        self._connect_signals()

    # ==========================================
    # UI 構築
    # ==========================================

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- ツリー ---
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setAnimated(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree, 1)

        # --- ボタンバー ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self.btn_attach = QPushButton(tr("layer_btn_attach"))
        self.btn_attach.setObjectName("ActionBtn")
        self.btn_attach.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_attach.setToolTip(tr("layer_tooltip_attach"))
        self.btn_attach.clicked.connect(self._on_attach)

        self.btn_detach = QPushButton(tr("layer_btn_detach"))
        self.btn_detach.setObjectName("ActionBtn")
        self.btn_detach.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_detach.setToolTip(tr("layer_tooltip_detach"))
        self.btn_detach.clicked.connect(self._on_detach)

        self.btn_up = QPushButton("↑")
        self.btn_up.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_up.setToolTip(tr("layer_tooltip_move_up"))
        self.btn_up.setFixedWidth(32)
        self.btn_up.clicked.connect(self._on_move_up)

        self.btn_down = QPushButton("↓")
        self.btn_down.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_down.setToolTip(tr("layer_tooltip_move_down"))
        self.btn_down.setFixedWidth(32)
        self.btn_down.clicked.connect(self._on_move_down)

        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_refresh.setToolTip(tr("layer_tooltip_refresh"))
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.rebuild)

        btn_row.addWidget(self.btn_attach)
        btn_row.addWidget(self.btn_detach)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_up)
        btn_row.addWidget(self.btn_down)
        btn_row.addWidget(self.btn_refresh)

        layout.addLayout(btn_row)

        # --- ヒントテキスト ---
        hint = QLabel(tr("layer_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(hint)

    def showEvent(self, event: Any) -> None:
        """タブが表示されるたびにツリーを最新状態に更新する。"""
        super().showEvent(event)
        self.rebuild()

    def _connect_signals(self) -> None:
        """WindowManager シグナルを接続する。"""
        try:
            wm = self.mw.window_manager
            wm.sig_layer_structure_changed.connect(self.rebuild)
            wm.sig_selection_changed.connect(self._on_canvas_selection_changed)
        except AttributeError:
            logger.debug("LayerTab: WindowManager シグナル接続スキップ（テスト環境）")

    # ==========================================
    # Public: ツリー再構築
    # ==========================================

    def rebuild(self) -> None:
        """ツリーをゼロから再構築する。sig_layer_structure_changed で呼ばれる。"""
        if self._rebuilding:
            return
        self._rebuilding = True
        try:
            self.tree.blockSignals(True)
            self.tree.clear()
            self._uuid_to_item.clear()

            wm = self.mw.window_manager
            all_wins = list(wm.text_windows) + list(wm.image_windows)

            # 親なし（ルート）Window を先に追加
            for window in all_wins:
                if not getattr(window, "parent_window_uuid", None):
                    item = self._make_item(window)
                    self.tree.addTopLevelItem(item)
                    self._uuid_to_item[window.uuid] = item
                    # 子を再帰追加
                    self._add_children(item, window, all_wins)

            self.tree.expandAll()
        except Exception:
            logger.exception("LayerTab.rebuild() failed")
        finally:
            self.tree.blockSignals(False)
            self._rebuilding = False

    def _add_children(
        self,
        parent_item: QTreeWidgetItem,
        parent_win: Any,
        all_wins: list,
    ) -> None:
        """parent_win の子を layer_order 順にツリーへ追加（再帰）。"""
        children = [w for w in all_wins if getattr(w, "parent_window_uuid", None) == parent_win.uuid]
        children.sort(key=lambda c: c.config.layer_order if c.config.layer_order is not None else 0)
        for child in children:
            item = self._make_item(child)
            parent_item.addChild(item)
            self._uuid_to_item[child.uuid] = item
            self._add_children(item, child, all_wins)

    def _make_item(self, window: Any) -> QTreeWidgetItem:
        """QTreeWidgetItem を生成する。"""
        item = QTreeWidgetItem([_window_label(window)])
        item.setData(0, Qt.ItemDataRole.UserRole, window.uuid)
        return item

    # ==========================================
    # 双方向同期
    # ==========================================

    def _on_canvas_selection_changed(self, selected_window: Any) -> None:
        """キャンバスで選択が変わったとき、ツリーの対応アイテムをハイライトする。"""
        if self._rebuilding:
            return
        if selected_window is None:
            self.tree.blockSignals(True)
            self.tree.clearSelection()
            self.tree.blockSignals(False)
            return

        uuid = getattr(selected_window, "uuid", None)
        if uuid and uuid in self._uuid_to_item:
            self._attach_parent_candidate_uuid = uuid
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(self._uuid_to_item[uuid])
            self.tree.blockSignals(False)

    def _on_tree_selection_changed(self) -> None:
        """ツリーで選択が変わったとき、対応するキャンバスウィンドウを raise_() する。

        Note:
            activateWindow() はフォーカス奪取を引き起こすため使わない。
            raise_() のみ使い、キャンバスの自然なフォーカスを保つ（Antigravity ガイドライン）。
        """
        items = self.tree.selectedItems()
        if not items:
            return
        uuid = items[0].data(0, Qt.ItemDataRole.UserRole)
        if not uuid:
            return
        wm = self.mw.window_manager
        window = wm.find_window_by_uuid(uuid)
        if window:
            try:
                prev_selected = getattr(wm, "last_selected_window", None)
                if hasattr(wm, "set_selected_window"):
                    wm.set_selected_window(window)
                else:
                    wm.last_selected_window = window
                prev_uuid = getattr(prev_selected, "uuid", None)
                if prev_uuid and prev_uuid != uuid:
                    self._attach_parent_candidate_uuid = prev_uuid
                elif self._attach_parent_candidate_uuid is None:
                    self._attach_parent_candidate_uuid = uuid
                window.raise_()
            except Exception:
                pass

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """ダブルクリックで対応 Window を最前面に出してアクティベートする。"""
        uuid = item.data(0, Qt.ItemDataRole.UserRole)
        if not uuid:
            return
        window = self.mw.window_manager.find_window_by_uuid(uuid)
        if window:
            try:
                window.raise_()
                window.activateWindow()
            except Exception:
                pass

    # ==========================================
    # ボタンアクション
    # ==========================================

    def _selected_uuid(self) -> Optional[str]:
        """ツリーで選択中のアイテムの UUID を返す。なければ None。"""
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    def _on_attach(self) -> None:
        """ツリーで選択中の Window を、キャンバスの最後選択 Window の子にアタッチする。

        操作手順:
          1. キャンバス上で「親にしたい Window」を左クリックして選択
          2. LayerタブのツリーでChild にしたい Window を選択
          3. [アタッチ] を押す
        """
        child_uuid = self._selected_uuid()
        if not child_uuid:
            return

        wm = self.mw.window_manager
        child = wm.find_window_by_uuid(child_uuid)
        if child is None:
            return

        # 親候補は「直前の選択」を優先し、直近が child 自身なら候補UUIDをフォールバックする
        parent = wm.last_selected_window
        if parent is child:
            candidate_uuid = self._attach_parent_candidate_uuid
            if candidate_uuid:
                parent = wm.find_window_by_uuid(candidate_uuid)
        if parent is None or parent is child:
            wm.sig_status_message.emit(tr("layer_msg_select_parent_first"))
            return

        try:
            wm.attach_layer(parent, child)
            parent_uuid = getattr(parent, "uuid", None)
            if parent_uuid:
                self._attach_parent_candidate_uuid = parent_uuid
        except Exception as e:
            logger.warning("attach_layer failed: %s", e)
            wm.sig_status_message.emit(str(e))

    def _on_detach(self) -> None:
        """ツリーで選択中の Window の親子関係を解除する。"""
        child_uuid = self._selected_uuid()
        if not child_uuid:
            return

        wm = self.mw.window_manager
        child = wm.find_window_by_uuid(child_uuid)
        if child is None:
            return

        if not getattr(child, "parent_window_uuid", None):
            wm.sig_status_message.emit(tr("layer_msg_no_parent"))
            return

        wm.detach_layer(child)

    def _on_move_up(self) -> None:
        """同階層内で1つ上（layer_order -1）に移動する。"""
        self._reorder_selected(delta=-1)

    def _on_move_down(self) -> None:
        """同階層内で1つ下（layer_order +1）に移動する。"""
        self._reorder_selected(delta=+1)

    def _reorder_selected(self, delta: int) -> None:
        """選択中の Window の layer_order を delta だけ変更し、兄弟の順序を整える。"""
        child_uuid = self._selected_uuid()
        if not child_uuid:
            return

        wm = self.mw.window_manager
        child = wm.find_window_by_uuid(child_uuid)
        if child is None:
            return

        parent_uuid = getattr(child, "parent_window_uuid", None)
        if not parent_uuid:
            wm.sig_status_message.emit(tr("layer_msg_no_parent"))
            return

        parent = wm.find_window_by_uuid(parent_uuid)
        if parent is None:
            return

        # 兄弟リストを layer_order でソート
        siblings = sorted(
            parent.child_windows,
            key=lambda c: c.config.layer_order if c.config.layer_order is not None else 0,
        )

        idx = next((i for i, s in enumerate(siblings) if s.uuid == child_uuid), None)
        if idx is None:
            return

        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(siblings):
            return

        # 隣と入れ替え
        siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
        for order, sibling in enumerate(siblings):
            sibling.config.layer_order = order
        try:
            parent.child_windows.sort(key=lambda c: c.config.layer_order if c.config.layer_order is not None else 0)
        except Exception:
            pass

        # Z-order 更新 + ツリー再構築
        wm.raise_group_stack(parent)
        wm.sig_layer_structure_changed.emit()
