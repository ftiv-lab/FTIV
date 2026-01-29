# managers/app_mode_manager.py
"""
アプリケーションモードの管理。

デスクトップモードとマインドマップモードの切り替え、
各モードのUI表示/非表示制御を担当する。
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from models.app_mode import AppMode
from models.window_layer import WindowLayer

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class AppModeManager(QObject):
    """アプリケーションモードの管理クラス。

    Attributes:
        sig_mode_changed: モードが変更された際に発火するシグナル。
    """

    sig_mode_changed = Signal(AppMode)

    def __init__(self, main_window: "MainWindow") -> None:
        """AppModeManagerを初期化する。

        Args:
            main_window: MainWindowのインスタンス。
        """
        super().__init__()
        self.mw = main_window
        self._current_mode: AppMode = AppMode.DESKTOP
        self._is_fullscreen: bool = False

    @property
    def current_mode(self) -> AppMode:
        """現在のアプリケーションモードを取得する。"""
        return self._current_mode

    @property
    def is_fullscreen(self) -> bool:
        """全画面モードかどうかを取得する。"""
        return self._is_fullscreen

    def switch_to_desktop(self) -> None:
        """デスクトップモードに切り替える。"""
        self._switch_mode(AppMode.DESKTOP)

    def switch_to_mindmap(self) -> None:
        """マインドマップモードに切り替える。"""
        self._switch_mode(AppMode.MIND_MAP)

    def toggle_mode(self) -> None:
        """現在のモードを切り替える。"""
        if self._current_mode == AppMode.DESKTOP:
            self.switch_to_mindmap()
        else:
            self.switch_to_desktop()

    def toggle_fullscreen(self) -> None:
        """全画面モードを切り替える（マインドマップモード専用）。"""
        if self._current_mode != AppMode.MIND_MAP:
            logger.warning("Fullscreen toggle is only available in Mind Map mode.")
            return

        self._is_fullscreen = not self._is_fullscreen

        if hasattr(self.mw, "mindmap_widget"):
            widget = self.mw.mindmap_widget
            if self._is_fullscreen:
                widget.showFullScreen()
            else:
                widget.showNormal()

        logger.info(f"Fullscreen mode: {self._is_fullscreen}")

    def _switch_mode(self, new_mode: AppMode) -> None:
        """内部モード切替処理。

        Args:
            new_mode: 切り替え先のモード。
        """
        if new_mode == self._current_mode:
            return

        old_mode = self._current_mode
        self._current_mode = new_mode

        logger.info(f"Switching mode: {old_mode.name} -> {new_mode.name}")

        # 全画面解除（モード切替時）
        if self._is_fullscreen:
            self._is_fullscreen = False
            if hasattr(self.mw, "mindmap_widget"):
                self.mw.mindmap_widget.showNormal()

        # UI切替
        if new_mode == AppMode.DESKTOP:
            self._activate_desktop_mode()
        else:
            self._activate_mindmap_mode()

        self.sig_mode_changed.emit(new_mode)

    def _activate_desktop_mode(self) -> None:
        """デスクトップモードのUIをアクティブ化する。"""
        # デスクトップ用タブを有効化
        self._set_desktop_tabs_enabled(True)

        # デスクトップレイヤーのウィンドウを表示
        self._set_layer_visibility(WindowLayer.DESKTOP, visible=True)

        # マインドマップウィジェットを非表示
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.hide()

        logger.debug("Desktop mode activated.")

    def _activate_mindmap_mode(self) -> None:
        """マインドマップモードのUIをアクティブ化する。"""
        # デスクトップ用タブを無効化
        self._set_desktop_tabs_enabled(False)

        # デスクトップレイヤーのウィンドウを非表示
        self._set_layer_visibility(WindowLayer.DESKTOP, visible=False)

        # マインドマップウィジェットを表示
        if hasattr(self.mw, "mindmap_widget"):
            self.mw.mindmap_widget.show()
            # キャンバスを中央にリセット
            if hasattr(self.mw.mindmap_widget, "canvas"):
                self.mw.mindmap_widget.canvas.center_view()

        logger.debug("Mind Map mode activated.")

    def _set_desktop_tabs_enabled(self, enabled: bool) -> None:
        """デスクトップモード用タブの有効/無効を設定する。"""
        tabs = [
            getattr(self.mw, "text_tab", None),
            getattr(self.mw, "image_tab", None),
            getattr(self.mw, "animation_tab", None),
        ]
        for tab in tabs:
            if tab is not None:
                tab.setEnabled(enabled)

    def _set_layer_visibility(self, layer: WindowLayer, visible: bool) -> None:
        """指定レイヤーに属するウィンドウの表示/非表示を設定する。"""
        if not hasattr(self.mw, "window_manager"):
            return

        for window in self.mw.window_manager.all_windows:
            window_layer = getattr(window, "layer", WindowLayer.DESKTOP)
            if window_layer == layer:
                if visible:
                    window.show()
                else:
                    window.hide()
