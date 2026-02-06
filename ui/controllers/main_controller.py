# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from managers.window_manager import WindowManager
    from ui.main_window import MainWindow


class MainController:
    """
    アプリケーションのメインコントローラー。
    MainWindow (View) と WindowManager (Model) の間のイベントハンドリング、
    およびアプリ全体のステート変更時のUI制御を担当する。
    """

    def __init__(self, main_window: "MainWindow", window_manager: "WindowManager"):
        self.view = main_window
        self.model = window_manager

    def setup_connections(self) -> None:
        """シグナル接続をセットアップする。"""
        # Model -> View/Controller (選択変更など)
        self.model.sig_selection_changed.connect(self._on_selection_changed)

    # --- Actions Accessors (Dependency Decoupling) ---
    @property
    def layout_actions(self) -> Any:
        return getattr(self.view, "layout_actions", None)

    @property
    def scene_actions(self) -> Any:
        return getattr(self.view, "scene_actions", None)

    @property
    def image_actions(self) -> Any:
        return getattr(self.view, "img_actions", None)

    @property
    def connector_actions(self) -> Any:
        return getattr(self.view, "conn_actions", None)

    @property
    def txt_actions(self) -> Any:
        return getattr(self.view, "txt_actions", None)

    @property
    def bulk_manager(self) -> Any:
        return getattr(self.view, "bulk_manager", None)

    def _on_selection_changed(self, window: Optional[Any]) -> None:
        """WindowManagerからの選択変更通知を処理する。"""
        # 1. PropertyPanel の更新
        if hasattr(self.view, "property_panel"):
            if window:
                self.view.property_panel.set_target(window)
                if self.view.is_property_panel_active:
                    self.view.property_panel.show()
                    self.view.property_panel.raise_()
            else:
                self.view.property_panel.set_target(None)
                if not self.view.is_property_panel_active:
                    self.view.property_panel.hide()

        # 2. 各タブの更新 (View上のコンポーネントへ通知)
        self._update_tab_state("animation_tab", window)
        self._update_tab_state("image_tab", window)
        self._update_tab_state("text_tab", window)
        self._update_tab_state("connections_tab", window)

    def _update_tab_state(self, tab_attr: str, window: Optional[Any]) -> None:
        """タブが選択変更メソッドを持っていれば呼ぶヘルパー。"""
        tab = getattr(self.view, tab_attr, None)
        if tab and hasattr(tab, "on_selection_changed"):
            tab.on_selection_changed(window)

    def handle_app_state_change(self, state: Qt.ApplicationState) -> None:
        """アプリケーションのアクティブ状態変化を処理する。"""
        if state == Qt.ApplicationInactive:
            # 非アクティブ時は選択解除 (従来ロジックの踏襲)
            if self.model.last_selected_window:
                self.model.set_selected_window(None)

    def request_property_panel(self, window: Any) -> None:
        """ウィンドウからのプロパティパネル表示要求時の処理。"""
        if not self.view.is_property_panel_active:
            self.view.is_property_panel_active = True

            # 全タブのボタン状態更新 (PropertyボタンをONにする)
            for tab_name in ["general_tab", "text_tab", "image_tab"]:
                tab = getattr(self.view, tab_name, None)
                if tab and hasattr(tab, "update_prop_button_state"):
                    tab.update_prop_button_state(True)

        self.view.update_prop_button_style()

        # モデルの選択状態を更新 (パネルが開いたらそのウィンドウを選択)
        self.model.set_selected_window(window)

        # パネル表示・前面化
        if hasattr(self.view, "property_panel"):
            self.view.property_panel.show()
            self.view.property_panel.raise_()
            self.view.property_panel.activateWindow()
            if hasattr(window, "raise_"):
                window.raise_()
