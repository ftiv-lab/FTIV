# ui/mindmap/mindmap_widget.py
"""
マインドマップモードのメインウィジェット。

キャンバスとツールバーを包含するコンテナウィジェット。
全画面モードや背景色変更などの操作を提供する。
"""

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.controllers.mindmap_controller import MindMapController
from ui.mindmap.mindmap_canvas import MindMapCanvas
from ui.mindmap.mindmap_node import MindMapNode
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class MindMapWidget(QWidget):
    """マインドマップモードのメインウィジェット。

    キャンバス、ツールバー、全画面モードを統合する。
    """

    sig_fullscreen_toggled = Signal(bool)

    def __init__(self, main_window: "MainWindow", parent: Optional[QWidget] = None) -> None:
        """MindMapWidgetを初期化する。

        Args:
            main_window: MainWindowのインスタンス。
            parent: 親ウィジェット。
        """
        super().__init__(parent)
        self.mw = main_window
        self._is_fullscreen: bool = False

        # 1. Canvas作成
        self.canvas = MindMapCanvas(self)

        # 2. Controller作成
        self.controller = MindMapController(self)
        self.canvas.controller = self.controller

        # 3. UI構築 (Toolbar作成などでControllerを使用するため最後)
        self._setup_ui()

        self._setup_shortcuts()
        self._connect_signals()

        logger.info("MindMapWidget initialized")

    def _setup_ui(self) -> None:
        """UIをセットアップする。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.setSpacing(0)

        # ツールバー
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)
        layout.addWidget(self.canvas, stretch=1)

        # スタイルシート
        self.setStyleSheet("""
            MindMapWidget {
                background-color: #1e1e2e;
            }
        """)

    def _create_toolbar(self) -> QWidget:
        """ツールバーを作成する。"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #2a2a3e;
                border-bottom: 1px solid #3a3a4e;
            }
            QPushButton {
                background-color: #3c3c5c;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4c4c6c;
            }
            QPushButton:pressed {
                background-color: #5c5c7c;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                background: #3c3c5c;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #6c9fff;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # ノード追加ボタン
        btn_add_node = QPushButton("➕ " + tr("mm_toolbar_add_node"))
        btn_add_node.clicked.connect(self._add_node_at_center)
        layout.addWidget(btn_add_node)

        layout.addSpacing(10)

        # ビュー操作
        btn_center = QPushButton("🎯 " + tr("mm_toolbar_center"))
        btn_center.clicked.connect(self.canvas.center_view)
        layout.addWidget(btn_center)

        btn_fit = QPushButton("📐 " + tr("mm_toolbar_fit_all"))
        btn_fit.clicked.connect(self.canvas.fit_all_nodes)
        layout.addWidget(btn_fit)

        layout.addSpacing(10)

        # ズームスライダー
        zoom_label = QLabel(tr("mm_toolbar_zoom"))
        layout.addWidget(zoom_label)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(10, 300)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        layout.addWidget(self._zoom_slider)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(40)
        layout.addWidget(self._zoom_label)

        layout.addSpacing(10)

        # Layout Mode Toggle
        mode_label = QLabel(tr("mm_mode_label"))
        layout.addWidget(mode_label)

        self._btn_mode_auto = QPushButton("⚡ " + tr("mm_mode_auto"))
        self._btn_mode_auto.setCheckable(True)
        self._btn_mode_auto.setChecked(False)  # デフォルトはManual
        self._btn_mode_auto.clicked.connect(lambda: self._set_layout_mode("auto"))
        layout.addWidget(self._btn_mode_auto)

        self._btn_mode_manual = QPushButton("✋ " + tr("mm_mode_manual"))
        self._btn_mode_manual.setCheckable(True)
        self._btn_mode_manual.setChecked(True)  # デフォルトはManual
        self._btn_mode_manual.clicked.connect(lambda: self._set_layout_mode("manual"))
        layout.addWidget(self._btn_mode_manual)

        layout.addSpacing(10)

        # Auto Layout
        # Auto Layout (Menu)
        self._btn_layout = QToolButton()
        self._btn_layout.setText("☷")
        self._btn_layout.setToolTip("Auto Layout (Ctrl+L)")
        self._btn_layout.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self._btn_layout.clicked.connect(self.controller.auto_layout_all)

        layout_menu = QMenu(self._btn_layout)
        # Menu Style (Ensure visibility)
        layout_menu.setStyleSheet("""
            QMenu { background-color: #f0f0f0; color: #333333; border: 1px solid #999; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #d0d0d0; color: #000000; }
        """)

        action_right = layout_menu.addAction(tr("mm_layout_right_logical"))
        action_right.triggered.connect(lambda: self.controller.set_layout_strategy("right_logical"))
        action_balanced = layout_menu.addAction(tr("mm_layout_balanced_map"))
        action_balanced.triggered.connect(lambda: self.controller.set_layout_strategy("balanced_map"))

        action_org = layout_menu.addAction(tr("mm_layout_org_chart"))
        action_org.triggered.connect(lambda: self.controller.set_layout_strategy("org_chart"))

        self._btn_layout.setMenu(layout_menu)
        # スタイル修正: 背景が暗い場合に見えにくくなるのを防ぐため、文字色や背景を明示
        self._btn_layout.setStyleSheet(
            "QToolButton { font-weight: bold; color: #444444; background-color: #eeeeee; border-radius: 4px; padding: 2px; }"
        )
        layout.addWidget(self._btn_layout)

        layout.addStretch()

        # 背景色ボタン
        btn_bg_color = QPushButton("🎨 " + tr("mm_toolbar_background"))
        btn_bg_color.clicked.connect(self._change_background_color)
        layout.addWidget(btn_bg_color)

        # グリッド表示切り替えボタン
        self._btn_grid = QPushButton("▦ " + tr("mm_toolbar_grid"))
        self._btn_grid.setCheckable(True)
        self._btn_grid.setChecked(True)  # デフォルトで有効
        self._btn_grid.clicked.connect(self._toggle_grid)
        layout.addWidget(self._btn_grid)

        # 全画面ボタン
        self._btn_fullscreen = QPushButton("⛶ " + tr("mm_toolbar_fullscreen"))
        self._btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self._btn_fullscreen)

        # プロパティパネルボタン
        self._btn_property = QPushButton("⚙ " + tr("mm_toolbar_property"))
        self._btn_property.setCheckable(True)
        if hasattr(self.mw, "is_property_panel_active"):
            self._btn_property.setChecked(self.mw.is_property_panel_active)
        self._btn_property.clicked.connect(self.mw.toggle_property_panel)
        layout.addWidget(self._btn_property)

        # デフォルトスタイル設定ボタン
        self._btn_style_settings = QPushButton("🎨")
        self._btn_style_settings.setToolTip(tr("mm_btn_default_style"))
        self._btn_style_settings.clicked.connect(self._open_style_settings)
        layout.addWidget(self._btn_style_settings)

        layout.addSpacing(10)

        # エクスポートボタン
        self._btn_export = QPushButton("📷")
        self._btn_export.setToolTip(tr("mm_toolbar_export"))
        self._btn_export.clicked.connect(self._export_image)
        layout.addWidget(self._btn_export)

        return toolbar

    def _setup_shortcuts(self) -> None:
        """キーボードショートカットを設定する。"""
        # Esc: 全画面解除
        self._add_shortcut(Qt.Key.Key_Escape, self._on_escape)

        # F11: 全画面切替
        self._add_shortcut(Qt.Key.Key_F11, self.toggle_fullscreen)

        # Ctrl+0: ズームリセット
        self._add_shortcut("Ctrl+0", self.canvas.reset_zoom)

        # Tab: 子ノード追加
        self._add_shortcut(Qt.Key.Key_Tab, self.controller.add_child_node)

        # Enter / Return: 兄弟ノード追加
        self._add_shortcut(Qt.Key.Key_Return, self.controller.add_sibling_node)
        self._add_shortcut(Qt.Key.Key_Enter, self.controller.add_sibling_node)

        # Delete / Backspace: 削除
        self._add_shortcut(Qt.Key.Key_Delete, self.controller.delete_selected_items)
        self._add_shortcut(Qt.Key.Key_Backspace, self.controller.delete_selected_items)

        # Ctrl+E: Export
        self._add_shortcut("Ctrl+E", self._export_image)

        # Ctrl+K: Annotate (Focus Property Panel)
        self._add_shortcut("Ctrl+K", self._focus_annotation_panel)

        # Ctrl+V: Paste as Markdown
        self._add_shortcut("Ctrl+V", self._handle_paste)

        # Ctrl+L: Auto Layout
        self._add_shortcut("Ctrl+L", self.controller.auto_layout_all)

    def _add_shortcut(self, key, slot) -> None:
        """ショートカットを追加するヘルパー。"""
        shortcut = QShortcut(QKeySequence(key), self)
        # Widgetにフォーカスがある時（子ウィジェット含む）のみ有効
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(slot)

    def _focus_annotation_panel(self) -> None:
        """プロパティパネルのアノテーション入力にフォーカスを移動する。"""
        if not self.mw or not hasattr(self.mw, "toggle_property_panel"):
            return

        # パネルを開く
        if not self._btn_property.isChecked():
            self.mw.toggle_property_panel()

        # TODO: Annotation入力フィールドへのフォーカス移動などを実装
        # とりあえずパネルを開くだけでも便利

    def _connect_signals(self) -> None:
        """シグナルを接続する。"""
        self.canvas.sig_canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.sig_add_node_requested.connect(self._on_add_node_request)
        if self.canvas.scene():
            self.canvas.scene().selectionChanged.connect(self._on_selection_changed)
        self.canvas.sig_zoom_changed.connect(self._update_zoom_ui)

    # ==========================================
    # Public API
    # ==========================================

    def update_prop_button_state(self, active: bool) -> None:
        """プロパティパネルボタンの状態を更新する。"""
        self._btn_property.setChecked(active)

    @property
    def is_fullscreen(self) -> bool:
        """全画面モードかどうか。"""
        return self._is_fullscreen

    def toggle_fullscreen(self) -> None:
        """全画面モードを切り替える。"""
        self._is_fullscreen = not self._is_fullscreen

        if self._is_fullscreen:
            self._original_parent = self.parent()
            self.setParent(None)
            self.showFullScreen()
            self._btn_fullscreen.setText("✕ " + tr("mm_toolbar_exit_fullscreen"))
        else:
            self.showNormal()
            if hasattr(self, "_original_parent") and self._original_parent:
                self.setParent(self._original_parent)
            self._btn_fullscreen.setText("⛶ " + tr("mm_toolbar_fullscreen"))

        self.sig_fullscreen_toggled.emit(self._is_fullscreen)
        logger.info(f"Fullscreen mode: {self._is_fullscreen}")

    def exit_fullscreen(self) -> None:
        """全画面モードを終了する。"""
        if self._is_fullscreen:
            self.toggle_fullscreen()

    def add_node(self, text: str = "New Node", position: Optional[tuple] = None) -> MindMapNode:
        """ノードを追加する。

        Args:
            text: ノードのテキスト。
            position: (x, y) 座標。None の場合は中央に配置。

        Returns:
            追加されたノード。
        """
        from PySide6.QtCore import QPointF

        pos = QPointF(position[0], position[1]) if position else None
        return self.controller.add_node(text=text, position=pos)

        node = MindMapNode(text=text, position=pos)

        # デフォルトスタイルを適用 (DRY: apply_to_config 使用)
        if self.mw and hasattr(self.mw, "default_node_style") and node.config:
            self.mw.default_node_style.apply_to_config(node.config)

        # Signal 接続 (疎結合)
        node.sig_request_set_as_default.connect(self._handle_set_as_default)

        self.canvas.scene().addItem(node)

        logger.info(f"Node added: '{text}' at ({pos.x():.0f}, {pos.y():.0f})")
        return node

    def _handle_set_as_default(self, config) -> None:
        """ノードからのデフォルトスタイル設定リクエストを処理する。

        Args:
            config: ノードの MindMapNodeConfig。

        Note:
            MindMapNode.sig_request_set_as_default シグナルに接続される。
            ノード側のフォールバックコードを代替する。
        """
        if not self.mw or not hasattr(self.mw, "default_node_style"):
            return

        # スタイルをコピー
        self.mw.default_node_style.copy_from_config(config)

        # 保存
        self.mw.file_manager.save_default_node_style()

        # 通知
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(self, tr("mm_dialog_default_style"), tr("msg_default_style_updated"))

        logger.info("Default node style updated via signal handler")

    def _open_style_settings(self) -> None:
        """デフォルトスタイル設定ダイアログを開く。"""
        if not self.mw or not hasattr(self.mw, "default_node_style"):
            return

        from ui.style_dialogs.default_style_dialog import DefaultStyleDialog

        dialog = DefaultStyleDialog(self.mw.default_node_style, self)
        if dialog.exec():
            # 設定更新
            new_style = dialog.get_style()
            # MainWindow の設定を更新 (参照渡しになっているが念のため代入)
            self.mw.default_node_style = new_style
            # 保存
            self.mw.file_manager.save_default_node_style()
            logger.info("Default node style updated via dialog")

    def clear_all(self) -> None:
        """全ノード・エッジを削除する。"""
        scene = self.canvas.scene()
        if scene:
            scene.clear()
            logger.info("All nodes and edges cleared")

    def _handle_paste(self) -> None:
        """クリップボードのテキストを貼り付ける（Markdownとして処理、プレビュー付き）。"""
        from PySide6.QtGui import QGuiApplication

        from ui.dialogs import MarkdownPastePreviewDialog

        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()

        if not text:
            return

        # プレビューダイアログを表示
        dialog = MarkdownPastePreviewDialog(text, self)
        if dialog.exec() != MarkdownPastePreviewDialog.Accepted:
            return

        parse_result = dialog.get_parse_result()
        if not parse_result or not parse_result.get("nodes"):
            return

        # 選択中のノードがあればそれを親とする
        selected = None
        scene = self.canvas.scene()
        if scene:
            items = scene.selectedItems()
            nodes = [i for i in items if isinstance(i, MindMapNode)]
            if nodes:
                selected = nodes[0]

        # コントローラーへ委譲（パース済みのノードデータを使用）
        self.controller.paste_nodes_from_parsed_data(parse_result["nodes"], selected)

    # ==========================================
    # Event Handlers
    # ==========================================

    def _on_escape(self) -> None:
        """Escキー押下時。"""
        if self._is_fullscreen:
            self.exit_fullscreen()

    def _on_canvas_clicked(self, pos) -> None:
        """キャンバスダブルクリック時。"""
        self.add_node("New Node", (pos.x(), pos.y()))

    def _on_add_node_request(self, pos) -> None:
        """キャンバス右クリックメニューからのノード追加リクエスト。"""
        node = self.add_node("New Node", (pos.x(), pos.y()))
        node.setSelected(True)

    def _on_selection_changed(self) -> None:
        """シーンの選択状態が変更された際の処理。"""
        scene = self.canvas.scene()
        if not scene:
            return

        items = scene.selectedItems()
        target = None
        if items:
            # 先頭の MindMapNode を選択対象とする（複数選択時は先頭優先）
            for item in items:
                if isinstance(item, MindMapNode):
                    target = item
                    break

        # WindowManager に通知して PropertyPanel を更新させる
        if self.mw and hasattr(self.mw, "window_manager"):
            self.mw.window_manager.set_selected_window(target)

    def _on_zoom_changed(self, value: int) -> None:
        """ズームスライダー変更時。"""
        self._zoom_label.setText(f"{value}%")
        factor = value / 100.0
        # Canvas側のzoom_factorも同期するためset_zoomを使用
        # ただしsig_zoom_changedが発火するのでループ防止が必要
        self.canvas.blockSignals(True)
        self.canvas.set_zoom(factor)
        self.canvas.blockSignals(False)

    def _update_zoom_ui(self, zoom_factor: float) -> None:
        """ズームUI（スライダー・ラベル）を更新する。"""
        percentage = int(zoom_factor * 100)
        self._zoom_label.setText(f"{percentage}%")

        # スライダー更新（シグナルループ防止）
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(percentage)
        self._zoom_slider.blockSignals(False)

    def _add_node_at_center(self) -> None:
        """中央にノードを追加する。"""
        self.add_node("New Node")

    def _change_background_color(self) -> None:
        """背景色変更ダイアログを表示する。"""
        current_color = self.canvas._bg_color
        new_color = QColorDialog.getColor(current_color, self, tr("mm_title_select_bg_color"))

        if new_color.isValid():
            self.canvas.set_background_color(new_color)
            logger.info(f"Background color changed to {new_color.name()}")

    def _toggle_grid(self) -> None:
        """グリッド表示を切り替える。"""
        enabled = self._btn_grid.isChecked()
        self.canvas.set_grid_enabled(enabled)
        logger.info(f"Grid {'enabled' if enabled else 'disabled'}")
        enabled = self._btn_grid.isChecked()
        self.canvas.set_grid_enabled(enabled)
        logger.info(f"Grid {'enabled' if enabled else 'disabled'}")

    def _set_layout_mode(self, mode: str) -> None:
        """レイアウトモードを切り替える。

        Args:
            mode: "auto" または "manual"
        """
        # ボタンの状態を更新 (排他的トグル)
        self._btn_mode_auto.setChecked(mode == "auto")
        self._btn_mode_manual.setChecked(mode == "manual")

        # Controllerに反映
        self.controller.set_layout_mode(mode)

    def _export_image(self) -> None:
        """画像をエクスポートする。"""
        from PySide6.QtCore import QDateTime
        from PySide6.QtWidgets import QFileDialog

        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        default_name = f"mindmap_{timestamp}.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("mm_dialog_export_image"),
            default_name,
            "Images (*.png *.jpg);;All Files (*)",
        )

        if file_path:
            success = self.canvas.export_to_image(file_path)

            from PySide6.QtWidgets import QMessageBox

            if success:
                QMessageBox.information(self, tr("mm_title_export_success"), tr("msg_export_success"))
            else:
                QMessageBox.warning(self, tr("mm_title_export_failed"), tr("msg_export_failed"))
