import json
import logging
import os
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox

from utils.app_settings import AppSettings, load_app_settings, save_app_settings
from utils.overlay_settings import OverlaySettings, load_overlay_settings, save_overlay_settings
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class SettingsManager:
    """アプリケーション設定とオーバーレイ設定を一元管理するクラス。"""

    def __init__(self, main_window: "MainWindow"):
        self.mw = main_window
        self.app_settings: Optional[AppSettings] = None
        self.overlay_settings: Optional[OverlaySettings] = None
        self.base_directory = getattr(self.mw, "base_directory", os.getcwd())

    def load_settings(self) -> None:
        """設定をロードする。MainWindowの初期化時に呼ぶこと。"""
        self.app_settings = load_app_settings(self.mw, self.base_directory)
        self.overlay_settings = load_overlay_settings(self.mw, self.base_directory)

    def save_app_settings(self) -> None:
        if self.app_settings:
            save_app_settings(self.mw, self.base_directory, self.app_settings)

    def save_overlay_settings(self) -> None:
        if self.overlay_settings:
            save_overlay_settings(self.mw, self.base_directory, self.overlay_settings)

    def load_text_archetype(self) -> dict:
        """TextWindowの初期スタイル（Archetype）を取得する。"""
        path = os.path.join(self.base_directory, "json", "text_archetype.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load text archetype: {e}")
            return {}

    def save_text_archetype(self, data: dict) -> bool:
        """TextWindowのデフォルトスタイルを保存する。"""
        path = os.path.join(self.base_directory, "json", "text_archetype.json")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save text archetype: {e}")
            return False

    def init_window_settings(self) -> None:
        """初回のウィンドウ設定（タイトル、アイコン、最前面フラグ等）を適用する。"""
        # アイコンなどは MainWindow 側でパス解決済みと想定
        if hasattr(self.mw, "icon_path") and os.path.exists(self.mw.icon_path):
            self.mw.setWindowIcon(QIcon(self.mw.icon_path))

        self.mw.setWindowTitle(tr("app_title"))
        self.mw.resize(320, 600)

        # 追加：設定に応じて最前面を適用
        is_top: bool = True
        try:
            if self.app_settings:
                is_top = bool(getattr(self.app_settings, "main_window_frontmost", True))
        except Exception:
            logger.debug("Failed to read main_window_frontmost setting", exc_info=True)
            is_top = True

        self._apply_frontmost_flag(is_top)

    def set_main_frontmost(self, enable: bool) -> None:
        """メインウィンドウの最前面表示を設定する。"""
        try:
            self._apply_frontmost_flag(enable)

            # 保存
            if self.app_settings:
                try:
                    self.app_settings.main_window_frontmost = enable
                    self.save_app_settings()
                except Exception:
                    logger.warning("Failed to save frontmost setting", exc_info=True)
        except Exception as e:
            QMessageBox.critical(self.mw, tr("msg_error"), f"Failed to set frontmost: {e}")

    def _apply_frontmost_flag(self, is_top: bool) -> None:
        """ウィンドウフラグを操作して最前面状態を変更するヘルパー。"""
        flags = self.mw.windowFlags()
        if is_top:
            self.mw.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.mw.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        self.mw.show()  # フラグ変更後は再表示が必要

    def apply_performance_settings(self, debounce_ms: int, wheel_debounce_ms: int, cache_size: int) -> None:
        """パフォーマンス設定を全ウィンドウへ適用・保存する。"""
        try:
            # 1. 設定保存
            if self.app_settings:
                self.app_settings.render_debounce_ms = int(debounce_ms)
                self.app_settings.wheel_debounce_ms = int(wheel_debounce_ms)
                self.app_settings.glyph_cache_size = int(cache_size)
                self.save_app_settings()

            # 2. TextWindow への適用
            if hasattr(self.mw, "text_windows"):
                for w in self.mw.text_windows:
                    if hasattr(w, "_render_debounce_ms"):
                        w._render_debounce_ms = int(debounce_ms)
                    if hasattr(w, "_wheel_debounce_setting"):
                        w._wheel_debounce_setting = int(wheel_debounce_ms)
                    if hasattr(w, "renderer") and hasattr(w.renderer, "_glyph_cache_size"):
                        w.renderer._glyph_cache_size = int(cache_size)

            # 3. ConnectorLabel への適用
            if hasattr(self.mw, "connectors"):
                for conn in self.mw.connectors:
                    try:
                        label = getattr(conn, "label_window", None)
                        if label:
                            if hasattr(label, "_render_debounce_ms"):
                                label._render_debounce_ms = int(debounce_ms)
                            if hasattr(label, "_wheel_debounce_setting"):
                                label._wheel_debounce_setting = int(wheel_debounce_ms)
                            if hasattr(label, "renderer") and hasattr(label.renderer, "_glyph_cache_size"):
                                label.renderer._glyph_cache_size = int(cache_size)
                    except Exception:
                        logger.warning(f"Failed to apply settings to connector {conn}", exc_info=True)

            if hasattr(self.mw, "show_status_message"):
                self.mw.show_status_message(tr("title_success"))

        except Exception as e:
            QMessageBox.critical(self.mw, tr("msg_error"), f"Failed to apply settings: {e}")

    def apply_overlay_settings_to_all_windows(self) -> None:
        """現在の overlay_settings を、既存の全オーバーレイウィンドウへ反映する。"""
        if not self.overlay_settings:
            return

        all_windows = []
        if hasattr(self.mw, "text_windows"):
            all_windows.extend(self.mw.text_windows)
        if hasattr(self.mw, "image_windows"):
            all_windows.extend(self.mw.image_windows)

        for w in all_windows:
            if w is None:
                continue

            # --- Common Settings ---
            # Title Bar
            if hasattr(w, "set_title_bar_visible"):
                if hasattr(self.overlay_settings, "show_title_bar"):
                    w.set_title_bar_visible(bool(self.overlay_settings.show_title_bar))

            # Border
            if hasattr(self.overlay_settings, "show_border") and hasattr(w, "set_border_visible"):
                w.set_border_visible(bool(self.overlay_settings.show_border))

            if hasattr(self.overlay_settings, "border_color") and hasattr(w, "border_color"):
                w.border_color = self.overlay_settings.border_color

            if hasattr(self.overlay_settings, "border_width") and hasattr(w, "border_width"):
                w.border_width = int(self.overlay_settings.border_width)

            # Background
            if hasattr(self.overlay_settings, "bg_color") and hasattr(w, "bg_color"):
                w.bg_color = self.overlay_settings.bg_color

            # Handle Size
            if hasattr(self.overlay_settings, "handle_size") and hasattr(w, "handle_size"):
                w.handle_size = int(self.overlay_settings.handle_size)

            # Update
            if hasattr(w, "update"):
                w.update()
