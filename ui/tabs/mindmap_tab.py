# ui/tabs/mindmap_tab.py
"""
マインドマップモード用のタブコンテンツ。

MainWindowのタブウィジェットに追加される、
マインドマップモードの設定・操作を提供するタブ。
"""

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class MindMapTab(QScrollArea):
    """マインドマップモード用のタブ。

    キャンバス設定、ノードスタイル、エクスポート設定などを提供する。
    """

    def __init__(self, main_window: "MainWindow", parent: Optional[QWidget] = None) -> None:
        """MindMapTabを初期化する。

        Args:
            main_window: MainWindowのインスタンス。
            parent: 親ウィジェット。
        """
        super().__init__(parent)
        self.mw = main_window

        self._setup_ui()
        logger.info("MindMapTab initialized")

    def _setup_ui(self) -> None:
        """UIをセットアップする。"""
        # スクロール可能なコンテナ
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # モード切替セクション
        layout.addWidget(self._create_mode_section())

        # マップ管理セクション (New)
        layout.addWidget(self._create_map_management_section())

        # キャンバス設定セクション
        layout.addWidget(self._create_canvas_section())

        # ノード設定セクション
        layout.addWidget(self._create_node_section())

        # 操作セクション
        layout.addWidget(self._create_actions_section())

        layout.addStretch()

    def _create_mode_section(self) -> QGroupBox:
        """モード切替セクションを作成する。"""
        group = QGroupBox(tr("mm_grp_mode"))
        layout = QVBoxLayout(group)

        # モード切替ボタン
        self._btn_toggle_mode = QPushButton("🗺️ " + tr("mm_btn_switch_to_mindmap"))
        self._btn_toggle_mode.setMinimumHeight(40)
        self._btn_toggle_mode.clicked.connect(self._toggle_mode)
        layout.addWidget(self._btn_toggle_mode)

        # 全画面ボタン
        self._btn_fullscreen = QPushButton("⛶ " + tr("mm_btn_enter_fullscreen"))
        self._btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(self._btn_fullscreen)

        return group

    def _create_map_management_section(self) -> QGroupBox:
        """マップ管理セクションを作成する。"""
        group = QGroupBox(tr("mm_grp_map_management"))
        layout = QVBoxLayout(group)

        # カテゴリ選択
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel(tr("mm_label_category")))
        self._cmb_category = QComboBox()
        self._cmb_category.setEditable(True)  # 新規作成可能に
        self._cmb_category.currentTextChanged.connect(self._on_category_changed)
        cat_layout.addWidget(self._cmb_category, stretch=1)
        layout.addLayout(cat_layout)

        # マップ選択
        map_layout = QHBoxLayout()
        map_layout.addWidget(QLabel(tr("mm_label_map")))
        self._cmb_map = QComboBox()
        self._cmb_map.setEditable(True)  # 新規作成可能に
        self._cmb_map.currentTextChanged.connect(self._on_map_changed)
        map_layout.addWidget(self._cmb_map, stretch=1)
        layout.addLayout(map_layout)

        # 操作ボタン
        btn_layout = QHBoxLayout()

        btn_load = QPushButton("📂 " + tr("mm_btn_load"))
        btn_load.clicked.connect(self._load_selected_map)
        btn_layout.addWidget(btn_load)

        btn_save = QPushButton("💾 " + tr("mm_btn_save"))
        btn_save.clicked.connect(self._save_current_map)
        btn_layout.addWidget(btn_save)

        btn_delete = QPushButton("🗑️ " + tr("mm_btn_delete"))
        btn_delete.setStyleSheet("background-color: #d32f2f;")
        btn_delete.clicked.connect(self._delete_selected_map)
        btn_layout.addWidget(btn_delete)

        layout.addLayout(btn_layout)

        return group

    def _create_canvas_section(self) -> QGroupBox:
        """キャンバス設定セクションを作成する。"""
        group = QGroupBox(tr("mm_grp_canvas_settings"))
        layout = QVBoxLayout(group)

        # 背景色
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel(tr("mm_label_background")))
        self._btn_bg_color = QPushButton("🎨 " + tr("mm_btn_select_color"))
        self._btn_bg_color.clicked.connect(self._select_bg_color)
        bg_layout.addWidget(self._btn_bg_color)
        bg_layout.addStretch()
        layout.addLayout(bg_layout)

        # グリッド表示
        self._chk_grid = QCheckBox(tr("mm_chk_show_grid"))
        self._chk_grid.setChecked(True)
        self._chk_grid.toggled.connect(self._toggle_grid)
        layout.addWidget(self._chk_grid)

        # グリッドサイズ
        grid_size_layout = QHBoxLayout()
        grid_size_layout.addWidget(QLabel(tr("mm_label_grid_size")))
        self._spin_grid_size = QSpinBox()
        self._spin_grid_size.setRange(20, 100)
        self._spin_grid_size.setValue(50)
        self._spin_grid_size.setSuffix(" px")
        self._spin_grid_size.valueChanged.connect(self._change_grid_size)
        grid_size_layout.addWidget(self._spin_grid_size)
        grid_size_layout.addStretch()
        layout.addLayout(grid_size_layout)

        return group

    def _create_node_section(self) -> QGroupBox:
        """ノード設定セクションを作成する。"""
        group = QGroupBox(tr("mm_grp_node_defaults"))
        layout = QVBoxLayout(group)

        # ノードスタイル
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel(tr("mm_label_style")))
        self._cmb_node_style = QComboBox()
        self._cmb_node_style.addItems([tr("mm_style_rounded_rect"), tr("mm_style_rectangle"), tr("mm_style_ellipse")])
        style_layout.addWidget(self._cmb_node_style)
        style_layout.addStretch()
        layout.addLayout(style_layout)

        # エッジタイプ
        edge_layout = QHBoxLayout()
        edge_layout.addWidget(QLabel(tr("mm_label_edge_type")))
        self._cmb_edge_type = QComboBox()
        self._cmb_edge_type.addItems([tr("mm_edge_bezier"), tr("mm_edge_straight"), tr("mm_edge_orthogonal")])
        edge_layout.addWidget(self._cmb_edge_type)
        edge_layout.addStretch()
        layout.addLayout(edge_layout)

        # 矢印表示
        self._chk_show_arrows = QCheckBox(tr("mm_chk_show_arrows"))
        self._chk_show_arrows.setChecked(True)
        layout.addWidget(self._chk_show_arrows)

        return group

    def _create_actions_section(self) -> QGroupBox:
        """操作セクションを作成する。"""
        group = QGroupBox(tr("mm_grp_actions"))
        layout = QVBoxLayout(group)

        # ビュー操作
        view_layout = QHBoxLayout()
        btn_center = QPushButton("🎯 " + tr("mm_btn_center_view"))
        btn_center.clicked.connect(self._center_view)
        view_layout.addWidget(btn_center)

        btn_fit = QPushButton("📐 " + tr("mm_btn_fit_all"))
        btn_fit.clicked.connect(self._fit_all)
        view_layout.addWidget(btn_fit)
        layout.addLayout(view_layout)

        # クリア
        btn_clear = QPushButton("🗑️ " + tr("mm_btn_clear_all"))
        btn_clear.clicked.connect(self._clear_all)
        layout.addWidget(btn_clear)

        return group

    # ==========================================
    # Event Handlers
    # ==========================================

    def _toggle_mode(self) -> None:
        """モードを切り替える。"""
        if hasattr(self.mw, "app_mode_manager"):
            self.mw.app_mode_manager.toggle_mode()
            self._update_mode_button()

    def _toggle_fullscreen(self) -> None:
        """全画面モードを切り替える。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.toggle_fullscreen()
            self._update_fullscreen_button()

    def _select_bg_color(self) -> None:
        """背景色を選択する。"""
        if not hasattr(self.mw, "mindmap_widget"):
            return

        current = self.mw.mindmap_widget.canvas._bg_color
        color = QColorDialog.getColor(current, self, "Select Background Color")
        if color.isValid():
            self.mw.mindmap_widget.canvas.set_background_color(color)

    def _toggle_grid(self, enabled: bool) -> None:
        """グリッド表示を切り替える。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.canvas.set_grid_enabled(enabled)

    def _change_grid_size(self, size: int) -> None:
        """グリッドサイズを変更する。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.canvas.GRID_SIZE = size
            self.mw.mindmap_widget.canvas.viewport().update()

    def _center_view(self) -> None:
        """ビューを中央にリセットする。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.canvas.center_view()

    def _fit_all(self) -> None:
        """全ノードが見えるようにフィットする。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.canvas.fit_all_nodes()

    def _clear_all(self) -> None:
        """全ノードをクリアする。"""
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.clear_all()

    def _update_mode_button(self) -> None:
        """モードボタンのテキストを更新する。"""
        if hasattr(self.mw, "app_mode_manager"):
            from models.app_mode import AppMode

            mode = self.mw.app_mode_manager.current_mode
            if mode == AppMode.MIND_MAP:
                self._btn_toggle_mode.setText("🖥️ Switch to Desktop Mode")
            else:
                self._btn_toggle_mode.setText("🗺️ Switch to Mind Map Mode")

    def _update_fullscreen_button(self) -> None:
        """全画面ボタンのテキストを更新する。"""
        if hasattr(self.mw, "mindmap_widget"):
            if self.mw.mindmap_widget.is_fullscreen:
                self._btn_fullscreen.setText("✕ Exit Fullscreen")
            else:
                self._btn_fullscreen.setText("⛶ Enter Fullscreen")

    # ==========================================
    # Map Management Handlers
    # ==========================================

    def _on_category_changed(self, category: str) -> None:
        """カテゴリ変更時の処理。マップリストを更新する。"""
        if not category:
            return

        self._cmb_map.blockSignals(True)
        self._cmb_map.clear()

        if hasattr(self.mw, "mindmaps") and category in self.mw.mindmaps:
            maps = self.mw.mindmaps[category].keys()
            self._cmb_map.addItems(sorted(list(maps)))

        self._cmb_map.blockSignals(False)

    def _on_map_changed(self, map_name: str) -> None:
        """マップ選択変更時の処理。"""
        # 自動ロードはしない（意図しない上書き防止のため明示的なボタン操作を要求）
        pass

    def _load_selected_map(self) -> None:
        """選択されたマップをロードする。"""
        category = self._cmb_category.currentText()
        map_name = self._cmb_map.currentText()

        if not category or not map_name:
            return

        mindmaps = getattr(self.mw, "mindmaps", {})
        if category in mindmaps and map_name in mindmaps[category]:
            data = mindmaps[category][map_name]
            self.mw.file_manager.deserialize_mindmap(data)
            self.mw.show_status_message(f"Loaded mind map: {category}/{map_name}")
        else:
            # 新規マップとして扱う場合（何もしないか、クリアするか）
            # ここでは何もしない
            pass

    def _save_current_map(self) -> None:
        """現在のマップを保存する。"""
        category = self._cmb_category.currentText()
        map_name = self._cmb_map.currentText()

        if not category or not map_name:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Warning", "Please specify Category and Map Name.")
            return

        # データを取得
        data = self.mw.file_manager.serialize_mindmap()

        # メモリ内DB更新
        if not hasattr(self.mw, "mindmaps"):
            self.mw.mindmaps = {}

        if category not in self.mw.mindmaps:
            self.mw.mindmaps[category] = {}

        self.mw.mindmaps[category][map_name] = data

        # ファイルへ永続化
        self.mw.file_manager.save_mindmaps_db(self.mw.mindmaps)

        self.mw.show_status_message(f"Saved mind map: {category}/{map_name}")

        # リスト更新 (新規作成時など)
        if self._cmb_category.findText(category) == -1:
            self._cmb_category.addItem(category)

        # マップリスト更新は _on_category_changed に任せるが、
        # 現在の選択を維持する必要がある
        current_map = self._cmb_map.currentText()
        if self._cmb_map.findText(current_map) == -1:
            self._cmb_map.addItem(current_map)

    def _delete_selected_map(self) -> None:
        """選択されたマップを削除する。"""
        category = self._cmb_category.currentText()
        map_name = self._cmb_map.currentText()

        if not category or not map_name:
            return

        from PySide6.QtWidgets import QMessageBox

        ret = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{category}/{map_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if ret != QMessageBox.Yes:
            return

        if hasattr(self.mw, "mindmaps"):
            if category in self.mw.mindmaps and map_name in self.mw.mindmaps[category]:
                del self.mw.mindmaps[category][map_name]

                # カテゴリが空になったらカテゴリも消す？ (今回は残す方針)

                self.mw.file_manager.save_mindmaps_db(self.mw.mindmaps)
                self.mw.show_status_message(f"Deleted mind map: {category}/{map_name}")

                # UI更新
                self._on_category_changed(category)
                self.mw.mindmap_widget.clear_all()

    def refresh_ui(self) -> None:
        """UI表示を更新する。"""
        # カテゴリリストの初期化など
        if hasattr(self.mw, "mindmaps"):
            current_cat = self._cmb_category.currentText()
            self._cmb_category.blockSignals(True)
            self._cmb_category.clear()
            self._cmb_category.addItems(sorted(self.mw.mindmaps.keys()))

            if current_cat:
                self._cmb_category.setCurrentText(current_cat)

            self._cmb_category.blockSignals(False)

            # マップリストも同期
            if self._cmb_category.currentText():
                self._on_category_changed(self._cmb_category.currentText())
