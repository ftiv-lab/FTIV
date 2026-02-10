# -*- coding: utf-8 -*-
# ui/main_window.py

import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

# PySide6 Imports
from PySide6.QtCore import QPoint, Qt, QTimer, QUrl  # ← QUrl 追加
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QUndoStack,  # ← 追加
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from managers.animation_manager import AnimationManager
from managers.bulk_manager import BulkOperationManager
from managers.file_manager import FileManager
from managers.menu_manager import MenuManager
from managers.settings_manager import SettingsManager

# マネージャークラス
from managers.style_manager import StyleManager
from managers.window_manager import WindowManager
from ui.controllers.connector_actions import ConnectorActions
from ui.controllers.image_actions import ImageActions
from ui.controllers.info_actions import InfoActions
from ui.controllers.text_actions import TextActions
from ui.mixins.dnd_mixin import DnDMixin
from ui.mixins.shortcut_mixin import ShortcutMixin
from ui.property_panel import PropertyPanel
from ui.tabs.about_tab import AboutTab
from ui.tabs.animation_tab import AnimationTab
from ui.tabs.general_tab import GeneralTab
from ui.tabs.image_tab import ImageTab
from ui.tabs.info_tab import InfoTab
from ui.tabs.scene_tab import ConnectionsTab, SceneTab
from ui.tabs.text_tab import TextTab
from utils.app_settings import AppSettings
from utils.overlay_settings import OverlaySettings

# ユーティリティ・ダイアログ
from utils.translator import _translator, get_lang, set_lang, tr

# Logger Setup
logger = logging.getLogger(__name__)


class MainWindow(DnDMixin, ShortcutMixin, QWidget):
    """アプリケーションのメインウィンドウクラス。

    各マネージャーの管理、UIの構築、グローバルなイベントハンドリングを担当します。
    """

    def __init__(self) -> None:
        """MainWindowの初期化。"""
        super().__init__()

        # --- 1. 状態変数の初期化 ---
        self.last_directory: str = ""
        self.is_dragging: bool = False
        self.drag_start_position: QPoint = QPoint()
        self.undo_stack: QUndoStack = QUndoStack(self)
        self.default_line_color: QColor = QColor(100, 200, 255, 180)
        self.default_line_width: int = 4
        self.is_property_panel_active: bool = False
        self.scenes: Dict[str, Any] = {}
        self.manual_dialog: Optional[Any] = None  # Lazy-init in show_manual_dialog()

        # 初期設定 (SettingsManagerに移譲)
        self.settings_manager = SettingsManager(self)
        self._init_paths()

        # 設定ロード
        self.settings_manager.load_settings()

        self.scene_db_path: str = os.path.join(self.json_directory, "scenes_db.json")

        # --- 2. マネージャーの初期化 ---
        self.window_manager: WindowManager = WindowManager(self)
        self.file_manager: FileManager = FileManager(self)
        self.style_manager: StyleManager = StyleManager(self)

        # Global Style System (Design Tokens)
        from managers.theme_manager import ThemeManager

        self.theme_manager = ThemeManager(self)
        self.theme_manager.apply_theme()

        self.menu_manager: MenuManager = MenuManager(self)
        self.animation_manager: AnimationManager = AnimationManager(self)
        self.bulk_manager: BulkOperationManager = BulkOperationManager(self)
        self.conn_actions = ConnectorActions(self)
        self.txt_actions = TextActions(self)
        self.img_actions = ImageActions(self)
        self.info_actions = InfoActions(self)

        from ui.controllers.layout_actions import LayoutActions
        from ui.controllers.scene_actions import SceneActions

        self.scene_actions = SceneActions(self)
        self.layout_actions = LayoutActions(self)

        # 11. コントローラーの初期化（ウィンドウ管理とUIの接着）
        # NOTE: Tabs生成時にControllerへの参照が必要なため、setup_uiの前に初期化する
        from ui.controllers.main_controller import MainController

        self.main_controller = MainController(self, self.window_manager)
        self.main_controller.setup_connections()

        # --- 3. UI構築と信号接続 ---
        self.setup_ui()

        # ウィンドウ設定適用 (UI構築後にサイズ等を確定させる)
        self.settings_manager.init_window_settings()

        self.create_undo_redo_actions()
        self.file_manager.load_scenes_db()

        self._register_emergency_shortcuts()

        # イベント・シグナル設定
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAcceptDrops(True)

        QApplication.instance().applicationStateChanged.connect(self.handle_app_state_change)
        _translator.languageChanged.connect(self.refresh_ui_text)

        # 13. 最後に選択されたウィンドウ (Propertyではなく初期値が必要ならここでNone代入だが、Property化されているため不要ならSkip。
        # Phase 9 リファクタリングで last_selected_window は property (delegated to window_manager) になった。
        # したがって self.last_selected_window = None は setter を呼ぶことになる。
        # WindowManager 側で None 初期化されているので、明示的な None セットは不要だが、やっても無害。
        # ただし、setter が wm.set_selected_window(None) を呼ぶ。

        # self.window_manager.sig_selection_changed.connect(self.on_manager_selection_changed) -> Moved to MainController
        # self.window_manager.sig_selection_changed.connect(self.on_manager_selection_changed) -> Moved to MainController
        self.window_manager.sig_undo_command_requested.connect(self.add_undo_command)

        self.show()

    # ==========================================
    # Properties (Compatibility Layer)
    # ==========================================
    @property
    def app_settings(self) -> Optional[AppSettings]:
        return self.settings_manager.app_settings

    @property
    def overlay_settings(self) -> Optional[OverlaySettings]:
        return self.settings_manager.overlay_settings

    @property
    def text_windows(self) -> List[Any]:
        """WindowManagerが保持するテキストウィンドウのリスト。"""
        return self.window_manager.text_windows

    @text_windows.setter
    def text_windows(self, value: List[Any]) -> None:
        self.window_manager.text_windows = value

    @property
    def image_windows(self) -> List[Any]:
        """WindowManagerが保持する画像ウィンドウのリスト。"""
        return self.window_manager.image_windows

    @image_windows.setter
    def image_windows(self, value: List[Any]) -> None:
        self.window_manager.image_windows = value

    @property
    def connectors(self) -> List[Any]:
        """WindowManagerが保持するコネクタのリスト。"""
        return self.window_manager.connectors

    @connectors.setter
    def connectors(self, value: List[Any]) -> None:
        self.window_manager.connectors = value

    @property
    def last_selected_window(self) -> Optional[Any]:
        """最後に選択されたウィンドウ。"""
        return self.window_manager.last_selected_window

    # ==========================================
    # Initialization Helpers
    # ==========================================

    def _init_paths(self) -> None:
        """実行環境に応じたパスの解決（utils.paths 利用版）。"""
        from utils.paths import get_base_dir, resolve_path

        # 書き込み用（設定・ログ・シーンDBなど）
        # Nuitka/PyInstallerのexe化時でも「exeのあるフォルダ」になります
        self.base_directory = get_base_dir()
        self.json_directory = os.path.join(self.base_directory, "json")
        os.makedirs(self.json_directory, exist_ok=True)

        # 読み込み用（アイコンなど）
        # exe化時は同梱リソースを探しに行きます
        self.icon_path = resolve_path("icon.ico")

        # 万が一見つからない場合のフォールバック
        if not os.path.exists(self.icon_path):
            self.icon_path = "icon.ico"

    def _init_window_settings(self) -> None:
        """メインウィンドウの基本外観設定 (SettingsManagerに移譲)。"""
        # 既に SettingsManager.init_window_settings() で実行済みだが
        # メソッド自体は残しておき、必要なら再呼び出しに応じる
        # ただし二重実行を避けるなら空にするか、Manager呼出にする
        if hasattr(self, "settings_manager"):
            self.settings_manager.init_window_settings()

    def handle_app_state_change(self, state: Qt.ApplicationState) -> None:
        """アプリケーションのアクティブ状態が変化した際の処理。"""
        if hasattr(self, "main_controller"):
            self.main_controller.handle_app_state_change(state)

    # ==========================================
    # Signal Handlers & Connection Helpers
    # ==========================================

    def add_undo_command(self, command: Any) -> None:
        """Undoスタックにコマンドを追加。"""
        self.undo_stack.push(command)

    def _legacy_connect_window_signals(self, window: Any) -> None:
        """互換用：旧シグナル接続API（強制 no-op 版）。

        方針:
            - 現在の正規ルートは WindowManager.add_text_window / add_image_window 内で
              _setup_window_connections を呼ぶ方式。
            - この legacy API が呼ばれるのは設計崩れ（管理外window混入・二重接続の温床）なので、
              何もせず return する。
            - ただし販売後のトラブルシュートのため、スタックトレース付きで error ログを残す。

        Args:
            window (Any): 旧コードから渡されるウィンドウ（未使用）。
        """
        _ = window

        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                "DEPRECATED: connect_window_signals/_legacy_connect_window_signals was called. "
                "This is a no-op. Please migrate all creation routes to WindowManager.add_*.",
                exc_info=True,
            )
        except Exception:
            pass

        # ★絶対に接続しない（no-op）
        return

    def connect_window_signals(self, window: Any) -> None:
        """互換エイリアス（強制 no-op）。

        Args:
            window (Any): 旧コードから渡されるウィンドウ（未使用）。
        """
        self._legacy_connect_window_signals(window)

    def on_properties_changed(self, window: Any) -> None:
        """プロパティ変更時にパネルを更新。"""
        if self.is_property_panel_active and self.last_selected_window == window:
            if hasattr(self.property_panel, "update_property_values"):
                self.property_panel.update_property_values()
        if hasattr(self, "info_tab") and hasattr(self.info_tab, "refresh_data"):
            self.info_tab.refresh_data()

    def on_request_property_panel(self, window: Any) -> None:
        """ウィンドウからの要求に応じてプロパティパネルを表示。"""
        if hasattr(self, "main_controller"):
            self.main_controller.request_property_panel(window)
        else:
            # フォールバック (初期化前等)
            self.window_manager.set_selected_window(window)

    def on_manager_selection_changed(self, window: Optional[Any]) -> None:
        """Deprecated: WindowManagerでの選択変更処理は MainController が担当します。"""
        pass

    def on_window_selected(self, window: Any) -> None:
        """ウィンドウ選択時の処理。"""
        self.window_manager.set_selected_window(window)

    def set_last_selected_window(self, window: Optional[Any]) -> None:
        """選択ウィンドウの外部設定。"""
        self.window_manager.set_selected_window(window)

    def on_window_moved(self, window: Any) -> None:
        """移動中のパネル座標同期。"""
        if self.is_property_panel_active and self.last_selected_window == window:
            if hasattr(self, "property_panel"):
                if hasattr(self.property_panel, "update_coordinates"):
                    self.property_panel.update_coordinates()
                else:
                    self.property_panel.refresh_ui()

    def on_window_closed(self, window: Any) -> None:
        """ウィンドウが閉じられた際のクリーンアップ。"""
        self.window_manager.remove_window(window)

    # ==========================================
    # UI Setup Methods
    # ==========================================

    def setup_ui(self) -> None:
        """メインUIコンポーネントの構築。"""
        main_layout = QVBoxLayout(self)
        # self.setStyleSheet(self._get_stylesheet())  # Removed for Global Style System

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self._build_main_tabs()

        self.footer_label = QLabel(tr("footer_msg"))
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setProperty("class", "footer-text")
        main_layout.addWidget(self.footer_label)

        self._init_property_panel()

    def _build_main_tabs(self) -> None:
        """メインのタブ構成を追加する（順序の集中管理）。"""
        # 1. 一般タブ (クラス化済み)
        self.general_tab = GeneralTab(self)
        self.tabs.addTab(self.general_tab, tr("tab_general"))
        # 2. テキストタブ (クラス化済み)
        self.text_tab = TextTab(self)
        self.tabs.addTab(self.text_tab, tr("tab_text"))
        # 3. 画像タブ (クラス化済み)
        self.image_tab = ImageTab(self)
        self.tabs.addTab(self.image_tab, tr("tab_image"))
        # 4. シーンタブ (クラス化済み)
        self.scene_tab = SceneTab(self)
        self.tabs.addTab(self.scene_tab, tr("tab_scene"))
        # 5. 接続タブ (クラス化済み)
        self.connections_tab = ConnectionsTab(self)
        self.tabs.addTab(self.connections_tab, tr("tab_connections"))
        # 6. 情報管理タブ (クラス化済み)
        self.info_tab = InfoTab(self)
        self.tabs.addTab(self.info_tab, tr("tab_info"))
        # 7. アニメーションタブ (クラス化済み)
        self.animation_tab = AnimationTab(self)
        self.tabs.addTab(self.animation_tab, tr("tab_animation"))
        # 8. 情報タブ (クラス化済み)
        self.about_tab = AboutTab(self)
        self.tabs.addTab(self.about_tab, tr("tab_about"))

    def _init_property_panel(self) -> None:
        """プロパティパネルの初期化（Undo/Redo action の取り込み含む）。"""
        # 独立ウィンドウとして扱うため Qt親は None にする。
        # MainWindow側トグル同期に必要な参照は main_window 引数で渡す。
        self.property_panel = PropertyPanel(parent=None, main_window=self)

        if hasattr(self, "undo_action"):
            self.property_panel.addAction(self.undo_action)
        if hasattr(self, "redo_action"):
            self.property_panel.addAction(self.redo_action)

        self.property_panel.hide()

        screen_geo = self.screen().availableGeometry()
        self.property_panel.move(screen_geo.right() - 320, screen_geo.top() + 100)

    def _get_stylesheet(self) -> str:
        """UIの基本スタイルシート定義（スリム化版）。"""
        return """
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Arial'; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #444; background: #323232; border-radius: 5px; }
            QTabBar::tab { background: #444; color: #bbb; padding: 6px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #323232; color: white; border-bottom: 2px solid #007acc; }

            /* ボタンの padding を少し減らしてスリム化 (10px -> 6px) */
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #005f9e; }
            QPushButton:pressed { background-color: #004a80; }

            QPushButton#ActionBtn { background-color: #444; border: 1px solid #555; }
            QPushButton#ActionBtn:hover { background-color: #555; }

            QPushButton#DangerBtn { background-color: #d32f2f; }
            QPushButton#DangerBtn:hover { background-color: #b71c1c; }

            /* GroupBoxのマージンを削減 (15px -> 8px) */
            QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 8px; font-weight: bold; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; bottom: 0px; }
            QListWidget { background-color: #333; border: 1px solid #555; }
        """

    # ==========================================
    # Language & UI Updates
    # ==========================================

    def change_language(self, button_id: int) -> None:
        """言語の切り替え。"""
        lang_code = "en" if button_id == 0 else "jp"
        set_lang(lang_code)
        self.setWindowTitle(tr("app_title"))
        self.refresh_ui_text()

    def _refresh_tab_titles(self) -> None:
        """メインタブ/サブタブのタブ名を現在言語で更新する。"""
        # メインタブ
        if hasattr(self, "tabs"):
            if self.tabs.count() >= 1:
                self.tabs.setTabText(0, tr("tab_general"))
            if self.tabs.count() >= 2:
                self.tabs.setTabText(1, tr("tab_text"))
            if self.tabs.count() >= 3:
                self.tabs.setTabText(2, tr("tab_image"))
            if self.tabs.count() >= 4:
                self.tabs.setTabText(3, tr("tab_scene"))
            if self.tabs.count() >= 5:
                self.tabs.setTabText(4, tr("tab_connections"))
            if self.tabs.count() >= 6:
                self.tabs.setTabText(5, tr("tab_info"))
            if self.tabs.count() >= 7:
                self.tabs.setTabText(6, tr("tab_animation"))
            if self.tabs.count() >= 8:
                self.tabs.setTabText(7, tr("tab_about"))

    def _refresh_selected_labels(self) -> None:
        """
        言語切替時などに、Selected 表示・チェック状態を現在の選択対象から再同期する。
        - Text/Image/Connections/Animation の Selected 表示を同時に更新
        - 例外が出ても refresh 全体を落とさない
        """
        try:
            if hasattr(self, "animation_tab"):
                self.animation_tab.on_selection_changed(self.last_selected_window)
        except Exception:
            logger.error("Failed to refresh AnimationTab selection", exc_info=True)

        try:
            if hasattr(self, "image_tab"):
                self.image_tab.on_selection_changed(self.last_selected_window)
            elif hasattr(self, "_img_on_selection_changed"):
                self._img_on_selection_changed(self.last_selected_window)
        except Exception:
            logger.error("Failed to refresh ImageTab selection", exc_info=True)

        try:
            if hasattr(self, "text_tab"):
                self.text_tab.on_selection_changed(self.last_selected_window)
            elif hasattr(self, "_txt_on_selection_changed"):
                self._txt_on_selection_changed(self.last_selected_window)
        except Exception:
            logger.error("Failed to refresh TextTab selection", exc_info=True)

        try:
            if hasattr(self, "connections_tab"):
                self.connections_tab.on_selection_changed(self.last_selected_window)
            elif hasattr(self, "_conn_on_selection_changed"):
                self._conn_on_selection_changed(self.last_selected_window)
        except Exception:
            logger.error("Failed to refresh ConnectionsTab selection", exc_info=True)

        try:
            if hasattr(self, "info_tab"):
                self.info_tab.on_selection_changed(self.last_selected_window)
        except Exception:
            logger.error("Failed to refresh InfoTab selection", exc_info=True)

    def _refresh_text_tab_text(self) -> None:
        """Textタブ内のラベル/ボタン/GroupBox/サブタブ名を現在言語で更新する。"""
        # ヘッダ
        if hasattr(self, "btn_add_text_main"):
            self.btn_add_text_main.setText("+ " + tr("menu_add_text"))
        if hasattr(self, "btn_toggle_prop_text"):
            self.btn_toggle_prop_text.setText(tr("btn_toggle_prop_panel"))

        # サブタブ名
        if hasattr(self, "txt_subtabs"):
            try:
                if self.txt_subtabs.count() >= 1:
                    self.txt_subtabs.setTabText(0, tr("tab_img_manage"))
                if self.txt_subtabs.count() >= 2:
                    self.txt_subtabs.setTabText(1, tr("tab_img_visibility"))
                if self.txt_subtabs.count() >= 3:
                    self.txt_subtabs.setTabText(2, tr("grp_orientation_spacing"))
                if self.txt_subtabs.count() >= 4:
                    self.txt_subtabs.setTabText(3, tr("grp_bulk_actions"))
            except Exception:
                pass

        # GroupBoxタイトル
        if hasattr(self, "txt_manage_grp_create"):
            self.txt_manage_grp_create.setTitle(tr("grp_img_manage_create"))
        if hasattr(self, "txt_manage_grp_selected"):
            self.txt_manage_grp_selected.setTitle(tr("grp_img_manage_selected"))

        if hasattr(self, "txt_vis_grp_selected"):
            self.txt_vis_grp_selected.setTitle(tr("anim_target_selected"))
        if hasattr(self, "txt_vis_grp_all"):
            self.txt_vis_grp_all.setTitle(tr("anim_target_all_text"))

        if hasattr(self, "txt_layout_grp_selected"):
            self.txt_layout_grp_selected.setTitle(tr("anim_target_selected"))
        if hasattr(self, "txt_layout_grp_all"):
            self.txt_layout_grp_all.setTitle(tr("anim_target_all_text"))

        # --- Text Tab ---
        if hasattr(self, "text_tab"):
            self.text_tab.refresh_ui()
        if hasattr(self, "btn_def_spacing_h"):
            self.btn_def_spacing_h.setText(tr("btn_set_def_spacing_h"))
        if hasattr(self, "btn_def_spacing_v"):
            self.btn_def_spacing_v.setText(tr("btn_set_def_spacing_v"))

        # --- Bulk (Style) ---
        if hasattr(self, "style_group"):
            self.style_group.setTitle(tr("grp_bulk_style"))
        if hasattr(self, "btn_font"):
            self.btn_font.setText(tr("btn_change_all_fonts"))
        if hasattr(self, "btn_apply_preset_all"):
            self.btn_apply_preset_all.setText(tr("btn_apply_preset_all"))
        if hasattr(self, "btn_front"):
            self.btn_front.setText(tr("btn_toggle_front"))

    def _refresh_image_tab_text(self) -> None:
        """画像タブ内のラベル/ボタン/GroupBox/サブタブ名を現在言語で更新する。"""
        if hasattr(self, "btn_add_image_main"):
            self.btn_add_image_main.setText("+ " + tr("menu_add_image"))
        if hasattr(self, "btn_toggle_prop_image"):
            self.btn_toggle_prop_image.setText(tr("btn_toggle_prop_panel"))

        # サブタブ名
        if hasattr(self, "image_subtabs"):
            try:
                if hasattr(self, "image_manage_page"):
                    i = self.image_subtabs.indexOf(self.image_manage_page)
                    if i != -1:
                        self.image_subtabs.setTabText(i, tr("tab_img_manage"))

                if hasattr(self, "transform_page"):
                    i = self.image_subtabs.indexOf(self.transform_page)
                    if i != -1:
                        self.image_subtabs.setTabText(i, tr("tab_img_transform"))

                if hasattr(self, "playback_page"):
                    i = self.image_subtabs.indexOf(self.playback_page)
                    if i != -1:
                        self.image_subtabs.setTabText(i, tr("tab_img_playback"))

                if hasattr(self, "arrange_page"):
                    i = self.image_subtabs.indexOf(self.arrange_page)
                    if i != -1:
                        self.image_subtabs.setTabText(i, tr("tab_img_arrange"))

                if hasattr(self, "visibility_page"):
                    i = self.image_subtabs.indexOf(self.visibility_page)
                    if i != -1:
                        self.image_subtabs.setTabText(i, tr("tab_img_visibility"))

            except Exception:
                logger.error("Failed to refresh Image subtab texts", exc_info=True)

        # Arrange 内サブタブ名（All / Selected）
        if hasattr(self, "arrange_subtabs"):
            try:
                if hasattr(self, "arrange_all_page"):
                    i = self.arrange_subtabs.indexOf(self.arrange_all_page)
                    if i != -1:
                        self.arrange_subtabs.setTabText(i, tr("tab_img_arrange_all"))
                if hasattr(self, "arrange_selected_page"):
                    i = self.arrange_subtabs.indexOf(self.arrange_selected_page)
                    if i != -1:
                        self.arrange_subtabs.setTabText(i, tr("tab_img_arrange_selected"))
            except Exception:
                logger.error("Failed to refresh Arrange subtab texts", exc_info=True)

        # --- Image Tab ---
        if hasattr(self, "image_tab"):
            self.image_tab.refresh_ui()

    def _refresh_scene_tab_text(self) -> None:
        """Sceneタブ内のラベル/ボタン/タブ名(未分類)を現在言語で更新する。"""
        if hasattr(self, "scene_group"):
            self.scene_group.setTitle(tr("grp_scene_list"))
        if hasattr(self, "scene_hint_label"):
            self.scene_hint_label.setText(tr("hint_scene_tab_usage"))

        # Sceneタブのボタン（言語切替時に未更新になりがちなのでここで更新）
        if hasattr(self, "btn_add_category"):
            self.btn_add_category.setText(tr("btn_add_category"))
        if hasattr(self, "btn_add_scene"):
            self.btn_add_scene.setText(tr("btn_add_scene"))
        if hasattr(self, "btn_load_scene_manual"):
            self.btn_load_scene_manual.setText(tr("btn_load_scene"))
        if hasattr(self, "btn_update_scene"):
            self.btn_update_scene.setText(tr("btn_update_scene"))
        if hasattr(self, "btn_close_scene"):
            self.btn_close_scene.setText(tr("btn_close_scene"))
        if hasattr(self, "btn_delete_scene"):
            self.btn_delete_scene.setText(tr("btn_delete_scene"))

        # Sceneカテゴリタブ名：defaultカテゴリだけ表示を翻訳に寄せる
        if hasattr(self, "scene_tab") and hasattr(self.scene_tab, "scene_category_tabs"):
            try:
                tabs = self.scene_tab.scene_category_tabs
                tab_bar = tabs.tabBar()
                for i in range(tabs.count()):
                    tab_data = tab_bar.tabData(i)
                    key = str(tab_data) if tab_data is not None else tabs.tabText(i)
                    if self._is_default_scene_category(key):
                        tabs.setTabText(i, tr("default_category"))
            except Exception:
                logger.debug("Failed to update scene category tab text", exc_info=True)

    def refresh_ui_text(self) -> None:
        """多言語対応のためのUIテキスト再読み込み。

        方針:
            - 各タブ/領域は _refresh_xxx_tab_text() に分割済みなので、それだけ呼ぶ
            - 旧来の重複更新ブロックは削除し、保守性を上げる
            - 例外が起きても全体が落ちないようにする
        """
        try:
            # 分割済みの更新関数だけ呼ぶ
            self._refresh_tab_titles()
            if hasattr(self, "general_tab"):
                self.general_tab.refresh_ui()
            if hasattr(self, "text_tab"):
                self.text_tab.refresh_ui()
            if hasattr(self, "image_tab"):
                self.image_tab.refresh_ui()
            if hasattr(self, "scene_tab"):
                self.scene_tab.refresh_ui()
            if hasattr(self, "connections_tab"):
                self.connections_tab.refresh_ui()
            if hasattr(self, "info_tab"):
                self.info_tab.refresh_ui()
            if hasattr(self, "animation_tab"):
                self.animation_tab.refresh_ui()
            if hasattr(self, "about_tab"):
                self.about_tab.refresh_ui()

            # MainWindow自体
            self.setWindowTitle(tr("app_title"))
            if hasattr(self, "footer_label"):
                self.footer_label.setText(tr("footer_msg"))

            # Sceneカテゴリ表示を現在言語へ同期（defaultカテゴリ表記を含む）
            if hasattr(self, "scenes"):
                self.refresh_scene_tabs()

            # Selected表示/チェック状態の再同期
            self._refresh_selected_labels()

            # PropertyPanel（表示中なら）
            try:
                if hasattr(self, "property_panel") and self.property_panel.isVisible():
                    self.property_panel.setWindowTitle(tr("prop_panel_title"))
                    self.property_panel.refresh_ui()
            except Exception:
                logger.error("Failed to refresh PropertyPanel", exc_info=True)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"UI Refresh Error: {e}")

    # ==========================================
    # Delegate Methods to WindowManager
    # ==========================================

    def update_image_window_list(self) -> None:
        """
        互換用メソッド。

        過去コード互換のために ImageWindow 側から呼ばれることがあるが、
        現在のUIには「画像一覧ウィジェット」が無いので、基本は no-op。

        ただし実害（リストに無効なウィンドウ参照が残り続ける等）を避けるため、
        WindowManager の image_windows を軽くクリーンアップする。
        """
        try:
            import shiboken6

            if hasattr(self, "window_manager") and hasattr(self.window_manager, "image_windows"):
                self.window_manager.image_windows = [
                    w for w in self.window_manager.image_windows if w is not None and shiboken6.isValid(w)
                ]
        except Exception:
            # ここで落ちると互換目的自体が崩れるが、重大なエラーではない
            logger.debug("Failed to clean up image_windows list", exc_info=True)

    def add_image_from_path(self, image_path: str) -> None:
        """画像追加の一元入口。

        - last_directory を更新
        - WindowManager 経由でウィンドウ生成（信号接続や管理リストを統一）
        - 互換のため update_image_window_list も呼ぶ

        Args:
            image_path (str): 追加する画像ファイルパス
        """
        self.last_directory = os.path.dirname(image_path)

        try:
            if hasattr(self, "window_manager"):
                self.window_manager.add_image_window(image_path)
            else:
                # ここは通常到達しない想定：到達したら設計崩れなので通知
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            self.update_image_window_list()

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to add image: {e}")
            traceback.print_exc()

    def close_all_images(self) -> None:
        self.window_manager.close_all_image_windows()

    def show_all_image_windows(self) -> None:
        self.window_manager.show_all_image_windows()

    def hide_all_image_windows(self) -> None:
        self.window_manager.hide_all_image_windows()

    def toggle_all_frontmost_image_windows(self) -> None:
        self.window_manager.toggle_all_frontmost_image_windows()

    def toggle_image_click_through(self) -> None:
        self.window_manager.toggle_image_click_through()

    def show_image_window_context_menu(self, image_window: Any) -> None:
        image_window.show_context_menu(QPoint(0, 0))

    # ==========================================
    # Image Batch Operations
    # ==========================================

    def set_all_gif_apng_playback_speed(self) -> None:
        self.img_actions.set_all_gif_apng_playback_speed()

    def set_all_image_opacity(self) -> None:
        self.img_actions.set_all_image_opacity()

    def set_all_image_opacity_realtime(self, val: int) -> None:
        self.img_actions.set_all_image_opacity_realtime(val)

    def set_all_image_size_percentage(self) -> None:
        self.img_actions.set_all_image_size_percentage()

    def set_all_image_size_realtime(self, val: int) -> None:
        self.img_actions.set_all_image_size_realtime(val)

    def set_all_image_rotation(self) -> None:
        self.img_actions.set_all_image_rotation()

    def set_all_image_rotation_realtime(self, val: int) -> None:
        self.img_actions.set_all_image_rotation_realtime(val)

    def reset_all_flips(self) -> None:
        self.img_actions.reset_all_flips()

    def reset_all_animation_speeds(self) -> None:
        self.img_actions.reset_all_animation_speeds()

    def toggle_all_image_animation_speed(self) -> None:
        self.img_actions.toggle_all_image_animation_speed()

    def stop_all_image_animations(self) -> None:
        self.img_actions.stop_all_image_animations()

        # def open_align_dialog(self) -> None:
        #     """(Deprecated) Duplicate removed."""
        #     pass
        if not self.image_windows:
            QMessageBox.information(self, tr("msg_info"), tr("msg_no_image_windows"))
            return

        # 生存しているウィンドウだけに絞る（保険）
        wins: list[Any] = []
        try:
            import shiboken6

            for w in list(self.image_windows):
                if w is None:
                    continue
                if not shiboken6.isValid(w):
                    continue
                wins.append(w)
        except Exception:
            logger.debug("Failed to filter valid windows for align dialog", exc_info=True)
            wins = [w for w in self.image_windows if w is not None]

        if not wins:
            QMessageBox.information(self, tr("msg_info"), tr("msg_no_image_windows"))
            return

        # 初期値（適当でOK：最後にUI側で調整する）
        initial_columns: int = 3
        initial_space: int = 0
        initial_screen: int = 0

        # 開始時の位置をスナップショット（Cancelで戻す）
        start_positions: dict[int, QPoint] = {id(w): w.pos() for w in wins}

        # プレビュー関数（Undoなし）
        def preview(columns: int, space: int, screen_index: int) -> None:
            try:
                self.align_images_on_multiple_displays(int(columns), int(space), int(screen_index))
            except Exception:
                logger.error("Preview failed in AlignDialog", exc_info=True)

            # 追加：プレビューで画像が前面を奪う環境があるため、操作盤を前に戻す保険
            try:
                self.raise_()
                self.activateWindow()
            except Exception:
                pass  # UI復帰の軽微なエラーは無視（再帰防止）

        try:
            from ui.dialogs import AlignImagesRealtimeDialog

            dialog: Optional[AlignImagesRealtimeDialog] = None

            def _run_dialog() -> int:
                nonlocal dialog
                dialog = AlignImagesRealtimeDialog(
                    initial_columns=initial_columns,
                    initial_space=initial_space,
                    screen_index=initial_screen,
                    on_preview=preview,
                    parent=self,
                )
                try:
                    dialog.raise_()
                    dialog.activateWindow()
                except Exception:
                    logger.warning("Failed to raise AlignDialog", exc_info=True)
                return int(dialog.exec())

            result: int = int(self._with_temporary_frontmost(_run_dialog))

            # dialog が作れなかった場合（極めて稀）
            if dialog is None:
                return

            if result != QDialog.Accepted:
                # Cancel：開始時の位置に戻す（Undoなし）
                for w in wins:
                    try:
                        p = start_positions.get(id(w))
                        if p is not None:
                            w.move(p)
                            if hasattr(w, "config"):
                                w.config.position = {"x": int(w.x()), "y": int(w.y())}
                    except Exception:
                        logger.error("Failed to restore window position on cancel", exc_info=True)
                return

            # OK：確定（Undoをまとめて積む）
            columns, space, screen_index = dialog.get_values()

            # 念のため最終値で整列をもう一度当てる（UI値とズレないように）
            self.align_images_on_multiple_displays(int(columns), int(space), int(screen_index))

            if hasattr(self, "undo_stack"):
                try:
                    self.undo_stack.beginMacro("Align Images (Realtime)")
                except Exception:
                    logger.error("Failed to begin Undo macro", exc_info=True)

            try:
                from utils.commands import MoveWindowCommand

                for w in wins:
                    old_pos = start_positions.get(id(w), w.pos())
                    new_pos = w.pos()
                    if old_pos == new_pos:
                        continue
                    if hasattr(self, "add_undo_command"):
                        self.add_undo_command(MoveWindowCommand(w, old_pos, new_pos))

            finally:
                if hasattr(self, "undo_stack"):
                    try:
                        self.undo_stack.endMacro()
                    except Exception:
                        logger.error("Failed to end Undo macro", exc_info=True)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open align dialog: {e}")
            traceback.print_exc()

            # 失敗したら位置を戻す
            for w in wins:
                try:
                    p = start_positions.get(id(w))
                    if p is not None:
                        w.move(p)
                except Exception:
                    logger.error("Failed to restore window position on error", exc_info=True)

    def open_align_dialog(self) -> None:
        # LayoutActions は Dialog を持っていないため、ここだけは MainWindow が Dialog を開き、
        # コールバックで layout_actions を呼ぶ形にするか、あるいは一旦ここから委譲する
        # 今回は Dialog ロジックごと移設すると import 循環などが面倒なので、
        # ここで Dialog を開き、処理実体を layout_actions.align_images_grid に流す

        # ...と思ったが、open_align_dialog もかなり長いので、
        # 理想は LayoutActions に移したいが、Dialog import がある。
        # ui/dialogs/align_dialog.py から MainWindow を参照している可能性があるので注意。
        # 確認: AlignImagesRealtimeDialog は parent=self を取るが、型は QWidget でOK。

        # v1: ここに残すが、実計算は layout_actions に逃がす
        # v2: LayoutActions に open_dialog メソッドを作り、mw を親として渡す (推奨)

        # ここでは v2 案を採用し、LayoutActions に open_align_dialog はまだないので、
        # 一旦「整列計算部分」だけ委譲する形に修正します。
        # -> align_images_on_multiple_displays を layout_actions に委譲

        # しかしコードを見ると open_align_dialog はロジックの塊なので、
        # 将来的にはこれも移動すべきですが、今回は安全策で
        # 「align_images_on_multiple_displays」のみを委譲します。
        self._legacy_open_align_dialog()

    def _legacy_open_align_dialog(self):
        """(Legacy) 画像整列ダイアログを表示する。内部で LayoutActions を利用。"""
        if not self.image_windows:
            QMessageBox.information(self, tr("msg_info"), tr("msg_no_image_windows"))
            return

        # 生存しているウィンドウだけに絞る（保険）
        wins: list[Any] = []
        try:
            import shiboken6

            for w in list(self.image_windows):
                if w is None:
                    continue
                if not shiboken6.isValid(w):
                    continue
                wins.append(w)
        except Exception:
            wins = [w for w in self.image_windows if w is not None]

        if not wins:
            QMessageBox.information(self, tr("msg_info"), tr("msg_no_image_windows"))
            return

        # 初期値（適当でOK：最後にUI側で調整する）
        initial_columns: int = 3
        initial_space: int = 0
        initial_screen: int = 0

        # 開始時の位置をスナップショット（Cancelで戻す）
        start_positions: dict[int, QPoint] = {id(w): w.pos() for w in wins}

        # プレビュー関数（Undoなし）
        def preview(columns: int, space: int, screen_index: int) -> None:
            try:
                self.align_images_on_multiple_displays(int(columns), int(space), int(screen_index))
            except Exception:
                # プレビューで落とさない
                pass

            # 追加：プレビューで画像が前面を奪う環境があるため、操作盤を前に戻す保険
            try:
                self.raise_()
                self.activateWindow()
            except Exception:
                pass

        try:
            from ui.dialogs import AlignImagesRealtimeDialog

            dialog: Optional[AlignImagesRealtimeDialog] = None

            def _run_dialog() -> int:
                nonlocal dialog
                dialog = AlignImagesRealtimeDialog(
                    initial_columns=initial_columns,
                    initial_space=initial_space,
                    screen_index=initial_screen,
                    on_preview=preview,
                    parent=self,
                )
                try:
                    dialog.raise_()
                    dialog.activateWindow()
                except Exception:
                    pass
                return int(dialog.exec())

            result: int = int(self._with_temporary_frontmost(_run_dialog))

            # dialog が作れなかった場合（極めて稀）
            if dialog is None:
                return

            if result != QDialog.Accepted:
                # Cancel：開始時の位置に戻す（Undoなし）
                for w in wins:
                    try:
                        p = start_positions.get(id(w))
                        if p is not None:
                            w.move(p)
                            if hasattr(w, "config"):
                                w.config.position = {"x": int(w.x()), "y": int(w.y())}
                    except Exception:
                        pass
                return

            # OK：確定（Undoをまとめて積む）
            columns, space, screen_index = dialog.get_values()

            # 念のため最終値で整列をもう一度当てる（UI値とズレないように）
            self.align_images_on_multiple_displays(int(columns), int(space), int(screen_index))

            if hasattr(self, "undo_stack"):
                try:
                    self.undo_stack.beginMacro("Align Images (Realtime)")
                except Exception:
                    pass

            try:
                from utils.commands import MoveWindowCommand

                for w in wins:
                    old_pos = start_positions.get(id(w), w.pos())
                    new_pos = w.pos()
                    if old_pos == new_pos:
                        continue
                    if hasattr(self, "add_undo_command"):
                        self.add_undo_command(MoveWindowCommand(w, old_pos, new_pos))

            finally:
                if hasattr(self, "undo_stack"):
                    try:
                        self.undo_stack.endMacro()
                    except Exception:
                        pass

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open align dialog: {e}")
            traceback.print_exc()

            # 失敗したら位置を戻す
            for w in wins:
                try:
                    p = start_positions.get(id(w))
                    if p is not None:
                        w.move(p)
                except Exception:
                    pass

    def align_images_on_multiple_displays(self, columns: int, space: int, screen_index: int) -> None:
        self.layout_actions.align_images_grid(columns, space, screen_index)

    # ==========================================
    # Connector & Manager Proxies (Deleted in Phase 11)
    # ==========================================

    def toggle_property_panel(self) -> None:
        """プロパティパネルの表示切り替え。

        複数のタブにある切替ボタンの状態を同期させつつ、パネルの表示/非表示を制御します。
        """
        # 送信元ボタンの状態を取得（クリックされたボタンのチェック状態を全体に反映）
        sender = self.sender()
        if isinstance(sender, QPushButton):
            self.is_property_panel_active = sender.isChecked()
            # Style update is handled by .toggle class now but we ensure state sync
        else:
            # メニュー等から直接呼ばれた場合のトグル
            self.is_property_panel_active = not self.is_property_panel_active

        if hasattr(self, "general_tab"):
            self.general_tab.update_prop_button_state(self.is_property_panel_active)
        if hasattr(self, "text_tab"):
            self.text_tab.update_prop_button_state(self.is_property_panel_active)
        if hasattr(self, "image_tab"):
            self.image_tab.update_prop_button_state(self.is_property_panel_active)

        # self.update_prop_button_style() # Deprecated/Removed as CSS handles it via :checked state

        if hasattr(self, "property_panel"):
            if self.is_property_panel_active:
                self.property_panel.show()
                self.property_panel.raise_()
                if self.last_selected_window:
                    self.property_panel.set_target(self.last_selected_window)
                    self.last_selected_window.raise_()
            else:
                self.property_panel.hide()

    def update_prop_button_style(self) -> None:
        """プロパティパネルボタンのトグル状態に応じたスタイル更新。"""
        if self.is_property_panel_active:
            # 活性化時のスタイル（画像タブなどの既存スタイルと合わせる）
            # style = "QPushButton { background-color: #3a6ea5; border: 2px solid #55aaff; }"
            pass

    # ==========================================
    # Scene Database & Tab Management
    # ==========================================

    @staticmethod
    def _is_default_scene_category(category: str) -> bool:
        """defaultカテゴリの内部キー/旧表示名を判定する。"""
        return str(category) in {"__default__", "未分類", "Uncategorized"}

    def _scene_category_display_title(self, category: str) -> str:
        """カテゴリキーから表示名を決定する。"""
        if self._is_default_scene_category(category):
            return tr("default_category")
        return str(category)

    def refresh_scene_tabs(self) -> None:
        """シーンDBの内容に基づいてタブを再構築。"""
        if not hasattr(self, "scene_tab") or not hasattr(self.scene_tab, "scene_category_tabs"):
            return

        tabs = self.scene_tab.scene_category_tabs
        tab_bar = tabs.tabBar()
        cur_idx = tabs.currentIndex()
        cur_key = ""
        if cur_idx >= 0:
            cur_data = tab_bar.tabData(cur_idx)
            cur_key = str(cur_data) if cur_data is not None else tabs.tabText(cur_idx)
        tabs.clear()

        for category, scene_dict in self.scenes.items():
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            list_widget.itemDoubleClicked.connect(self.load_selected_scene)
            for name in scene_dict.keys():
                list_widget.addItem(name)
            tabs.addTab(list_widget, self._scene_category_display_title(category))
            tab_bar.setTabData(tabs.count() - 1, str(category))

        for i in range(tabs.count()):
            tab_data = tab_bar.tabData(i)
            key = str(tab_data) if tab_data is not None else tabs.tabText(i)
            if key == cur_key:
                tabs.setCurrentIndex(i)
                break

    def add_new_category(self) -> None:
        """新しいカテゴリを追加する（SceneActionsへ委譲）。"""
        self.scene_actions.add_new_category()

    def add_new_scene(self) -> None:
        """新しいシーンを追加する（SceneActionsへ委譲）。"""
        self.scene_actions.add_new_scene()

    def load_selected_scene(self) -> None:
        """選択されたシーンをロードする（SceneActionsへ委譲）。"""
        self.scene_actions.load_selected_scene()

    def update_selected_scene(self) -> None:
        """選択されたシーンを更新する（SceneActionsへ委譲）。"""
        self.scene_actions.update_selected_scene()

    def delete_selected_item(self) -> None:
        """選択されたカテゴリまたはシーンを削除する（SceneActionsへ委譲）。"""
        self.scene_actions.delete_selected_item()

    def apply_preset_to_all_text_windows(self) -> None:
        if not self.text_windows:
            return QMessageBox.information(self, tr("msg_info"), tr("msg_no_text_windows"))
        from ui.dialogs import StyleGalleryDialog

        dialog = StyleGalleryDialog(self.style_manager, self)
        if dialog.exec() == QDialog.Accepted:
            path = dialog.get_selected_style_path()
            if path:
                self.style_manager.apply_style_to_text_windows(self.text_windows, path)

    def navigate_selection(self, current_window: Any, key: Qt.Key) -> None:
        self.window_manager.navigate_selection(current_window, key)

    # ==========================================
    # Events & Context Menu
    # ==========================================

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging, self.drag_start_position = (
                True,
                event.globalPosition().toPoint() - self.frameGeometry().topLeft(),
            )
            self.raise_()
            self.activateWindow()
            if self.last_selected_window:
                self.window_manager.set_selected_window(None)
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()

    def closeEvent(self, event) -> None:
        if hasattr(self, "property_panel"):
            self.property_panel.close()

        # Sticky Note Mode (Orphan Windows) Cleanup
        # 親子関係を切ったウィンドウ達は道連れにならないので、手動で閉じる
        if hasattr(self, "window_manager"):
            self.window_manager.close_all_windows()

    def show_context_menu(self, pos: QPoint) -> None:
        """メインウィンドウの背景右クリックメニュー構築（MenuManagerに委譲）。"""
        self.menu_manager.show_context_menu(pos)

    def open_log_folder(self) -> None:
        """ログファイルが保存されているフォルダを OS のエクスプローラー等で開きます。"""
        # self.base_directory は _init_paths で設定済み
        log_path = os.path.join(self.base_directory, "logs")

        # フォルダが存在しない場合は作成しておく
        if not os.path.exists(log_path):
            try:
                os.makedirs(log_path)
            except Exception as e:
                QMessageBox.critical(self, tr("msg_error"), f"Failed to create log directory: {e}")
                return

        try:
            if sys.platform == "win32":
                os.startfile(log_path)
            elif sys.platform == "darwin":
                import subprocess

                subprocess.Popen(["open", log_path])
            else:
                import subprocess

                subprocess.Popen(["xdg-open", log_path])
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open log folder: {e}")

    def show_status_message(self, text: str, timeout_ms: int = 2000) -> None:
        """
        フッターに一時メッセージを表示し、timeout後に footer_msg に戻す。
        """
        try:
            self.footer_label.setText(text)

            def _restore():
                try:
                    self.footer_label.setText(tr("footer_msg"))
                except Exception:
                    logger.debug("Failed to restore footer status message", exc_info=True)

            QTimer.singleShot(int(timeout_ms), _restore)
        except Exception:
            logger.warning("Failed to show status message", exc_info=True)

    def toggle_main_frontmost(self) -> None:
        """メインウィンドウの最前面表示（WindowStaysOnTopHint）を切り替えます。"""
        # 送信元（ボタン）から状態を取得
        is_checked = False
        sender = self.sender()
        if isinstance(sender, QPushButton):
            is_checked = sender.isChecked()
        elif hasattr(self, "general_tab"):
            # Fallback
            is_checked = self.general_tab.btn_main_frontmost.isChecked()

        self.settings_manager.set_main_frontmost(is_checked)

        # UI更新
        if hasattr(self, "general_tab"):
            self.general_tab.update_frontmost_button_state(is_checked)

    def apply_performance_settings(self, debounce_ms: int, wheel_debounce_ms: int, cache_size: int) -> None:
        """パフォーマンス設定を保存し、既存の全ウィンドウに即時適用する。"""
        self.settings_manager.apply_performance_settings(debounce_ms, wheel_debounce_ms, cache_size)

    def _txt_open_style_gallery_selected(self) -> None:
        """
        スタイルギャラリーを開き、選択中（TextWindow / ConnectorLabel）に適用する。
        """
        w = getattr(self, "last_selected_window", None)
        if w is None:
            return

        is_text_like = False
        try:
            from windows.connector import ConnectorLabel
            from windows.text_window import TextWindow

            is_text_like = isinstance(w, (TextWindow, ConnectorLabel))
        except Exception:
            is_text_like = type(w).__name__ in ("TextWindow", "ConnectorLabel")

        if not is_text_like:
            return

        style_mgr = getattr(self, "style_manager", None)
        if style_mgr is None:
            return

        try:
            from PySide6.QtWidgets import QDialog

            from ui.dialogs import StyleGalleryDialog

            dialog = StyleGalleryDialog(style_mgr, self)
            if dialog.exec() != QDialog.Accepted:
                return

            json_path = dialog.get_selected_style_path()
            if not json_path:
                return

            style_mgr.load_text_style(w, json_path)
        except Exception:
            pass

    def create_connections_tab(self) -> QWidget:
        """
        Connections をメインタブとして表示する。
        現状は ui/tabs/scene_tab.py の build_connections_subtab を再利用する（仕様合意済みの案C）。
        """
        # ここは循環import回避のためローカルimportにしておく（安全策）
        from ui.tabs.scene_tab import build_connections_subtab

        return build_connections_subtab(self)

    def apply_overlay_settings_to_all_windows(self) -> None:
        """現在の overlay_settings を、既存の全オーバーレイウィンドウへ反映する。"""
        self.settings_manager.apply_overlay_settings_to_all_windows()

    def img_pack_all_left_top(self, screen_index: int, space: int = 0) -> None:
        """全 ImageWindow を指定ディスプレイの左上へ詰めて配置する（ImageActionsへ委譲）。"""
        self.img_actions.pack_all_left_top(screen_index, space)

    def img_pack_all_center(self, screen_index: int, space: int = 0) -> None:
        """全 ImageWindow を指定ディスプレイの中央へ詰めて配置する（ImageActionsへ委譲）。"""
        self.img_actions.pack_all_center(screen_index, space)

    def _with_temporary_frontmost(self, fn: Any) -> Any:
        """処理中だけ MainWindow を一時的に最前面にする。

        整列プレビュー等でオーバーレイが前面に居座り、操作盤が押せなくなる問題の対策。

        Args:
            fn (Any): 実行する関数（戻り値はそのまま返す）。

        Returns:
            Any: fn の戻り値。
        """
        original_top: bool = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)

        try:
            # 一時的に最前面化
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
            self.raise_()
            self.activateWindow()

            return fn()

        finally:
            # 元に戻す（設定の永続化はしない）
            try:
                flags = self.windowFlags()
                if original_top:
                    self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
                else:
                    self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
                self.show()
                self.raise_()
                self.activateWindow()
            except Exception:
                logger.warning("Failed to restore window flags in _with_temporary_frontmost", exc_info=True)

    def show_about_dialog(self) -> None:
        """About（バージョン情報）を表示する（リッチ表示版）。"""
        try:
            from ui.dialogs import TextBrowserDialog
            from utils.docs import ABOUT_TEXT_TEMPLATE
            from utils.edition import get_edition
            from utils.version import APP_VERSION

            # 現在の情報を取得
            edition = get_edition(self, getattr(self, "base_directory", None))

            # テンプレートに値を埋め込む
            html_content = ABOUT_TEXT_TEMPLATE.format(
                version=APP_VERSION.version,
                edition=edition.value.upper(),
                data_format=str(APP_VERSION.data_format_version),
            )

            # 説明書表示用のダイアログを再利用（タイトルだけ About に）
            # リサイズして少し小さめにする
            dialog = TextBrowserDialog(tr("title_about"), html_content, self)
            dialog.resize(400, 350)
            dialog.exec()

        except Exception as e:
            # 万が一のフォールバック
            QMessageBox.critical(self, tr("msg_error"), f"Failed to show about: {e}")

    def show_manual_dialog(self) -> None:
        """説明書ダイアログを表示する。"""
        # 既に表示中なら最前面へ
        dialog = self.manual_dialog
        if dialog is not None:
            if dialog.isVisible():
                dialog.activateWindow()
                dialog.raise_()
                return

        from ui.dialogs import TextBrowserDialog
        from utils.docs import MANUAL_TEXT_EN, MANUAL_TEXT_JP

        # 言語判定
        lang = get_lang()
        text = MANUAL_TEXT_EN if lang == "en" else MANUAL_TEXT_JP

        self.manual_dialog = TextBrowserDialog(tr("btn_manual"), text, parent=None, allow_independence=True)
        # 独立ウィンドウにもメインと同じスタイルを適用
        # self.manual_dialog.setStyleSheet(self._get_stylesheet())  # Removed for Global Style System
        self.manual_dialog.show()

    def show_license_dialog(self) -> None:
        """ライセンスダイアログを表示する。"""
        from ui.dialogs import TextBrowserDialog
        from utils.docs import LICENSE_TEXT

        dialog = TextBrowserDialog(tr("btn_license"), LICENSE_TEXT, self)
        dialog.exec()

    def open_shop_page(self) -> None:
        """販売ページをブラウザで開く。"""
        from utils.edition import SHOP_URL

        try:
            QDesktopServices.openUrl(QUrl(SHOP_URL))
        except Exception as e:
            QMessageBox.warning(self, tr("msg_error"), f"Failed to open URL: {e}")

    def copy_shop_url(self) -> None:
        """販売ページのURLをクリップボードにコピーする。"""
        from utils.edition import SHOP_URL

        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(SHOP_URL)
            self.show_status_message(tr("msg_url_copied"))
        except Exception:
            pass
