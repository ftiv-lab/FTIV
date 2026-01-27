import json
import logging
import os
import traceback
from typing import Any, Dict, Optional, Union

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QColorDialog, QDialog, QFileDialog, QFontDialog, QMessageBox

from models.enums import OffsetMode
from models.window_config import TextWindowConfig
from ui.context_menu import ContextMenuBuilder
from ui.dialogs import (
    GradientEditorDialog,
    MarginRatioDialog,
    ShadowOffsetDialog,
    StyleGalleryDialog,
    TextInputDialog,
    TextSpacingDialog,
)
from utils.translator import tr

from .base_window import BaseOverlayWindow
from .text_renderer import TextRenderer

# ロガーの取得
logger = logging.getLogger(__name__)


class TextWindow(BaseOverlayWindow):
    """テキストを表示・制御するためのオーバーレイウィンドウクラス。

    テキストの描画、スタイル設定、およびマインドマップ風のノード操作を管理します。
    """

    def __init__(self, main_window: Any, text: str, pos: QPoint):
        """TextWindowの初期化を行い、ログに記録します。

        Args:
            main_window (Any): メインウィンドウのインスタンス。
            text (str): 初期表示テキスト。
            pos (QPoint): 表示位置。
        """
        super().__init__(main_window, config_class=TextWindowConfig)

        try:
            self.renderer: TextRenderer = TextRenderer()

            # --- パフォーマンス設定（キャッシュサイズ）の反映 ---
            try:
                self.renderer._glyph_cache_size = int(getattr(main_window.app_settings, "glyph_cache_size", 512))
            except Exception:
                pass

            self.config.text = text
            self.config.position = {"x": pos.x(), "y": pos.y()}
            self.canvas_size: QSize = QSize(10, 10)
            self.setGeometry(QRect(pos, self.canvas_size))

            defaults = self.load_text_defaults()
            self.config.horizontal_margin_ratio = defaults.get("h_margin", 0.0)
            self.config.vertical_margin_ratio = defaults.get("v_margin", 0.2)
            self.config.margin_top = defaults.get("margin_top", 0.0)
            self.config.margin_bottom = defaults.get("margin_bottom", 0.0)
            self.config.margin_left = defaults.get("margin_left", 0.3)
            self.config.margin_right = defaults.get("margin_right", 0.0)

            self._previous_text_opacity: int = 100
            self._previous_background_opacity: int = 100

            self.auto_detect_offset_mode(QFont(self.font_family, int(self.font_size)))

            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)

            # デバウンス用タイマー
            self._render_timer: QTimer = QTimer(self)
            self._render_timer.setSingleShot(True)
            self._render_timer.timeout.connect(self._update_text_immediate)

            # ホイール操作後のデバウンス復帰用タイマー
            self._wheel_render_relax_timer: QTimer = QTimer(self)
            self._wheel_render_relax_timer.setSingleShot(True)
            self._wheel_render_relax_timer.timeout.connect(self._restore_render_debounce_ms_after_wheel)

            # --- パフォーマンス設定（デバウンス時間）の反映 ---
            try:
                self._render_debounce_ms: int = int(getattr(main_window.app_settings, "render_debounce_ms", 50))
                # ★追加: ホイール用設定も読み込む
                self._wheel_debounce_setting: int = int(getattr(main_window.app_settings, "wheel_debounce_ms", 80))
            except Exception:
                self._render_debounce_ms = 25
                self._wheel_debounce_setting = 50

            self.update_text()
            logger.info(f"TextWindow initialized: UUID={self.uuid}")

        except Exception as e:
            logger.error(f"Failed to initialize TextWindow: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(None, tr("msg_error"), f"Initialization error: {e}")

    # --- Properties ---

    @property
    def text(self) -> str:
        return self.config.text

    @text.setter
    def text(self, value: str):
        self.config.text = value

    @property
    def font_family(self) -> str:
        return self.config.font

    @font_family.setter
    def font_family(self, value: str):
        self.config.font = value

    @property
    def font_size(self) -> int:
        return int(self.config.font_size)

    @font_size.setter
    def font_size(self, value: Union[int, float]):
        self.config.font_size = int(value)

    def _get_color(self, hex_str: str) -> QColor:
        return QColor(hex_str)

    def _set_color(self, target_attr: str, value: Union[QColor, str]) -> None:
        if isinstance(value, QColor):
            setattr(self.config, target_attr, value.name(QColor.HexArgb))
        else:
            setattr(self.config, target_attr, value)

    @property
    def font_color(self) -> QColor:
        return self._get_color(self.config.font_color)

    @font_color.setter
    def font_color(self, v: Union[QColor, str]):
        self._set_color("font_color", v)

    @property
    def background_color(self) -> QColor:
        return self._get_color(self.config.background_color)

    @background_color.setter
    def background_color(self, v: Union[QColor, str]):
        self._set_color("background_color", v)

    @property
    def text_visible(self) -> bool:
        return self.config.text_visible

    @text_visible.setter
    def text_visible(self, v: bool):
        self.config.text_visible = v

    @property
    def background_visible(self) -> bool:
        return self.config.background_visible

    @background_visible.setter
    def background_visible(self, v: bool):
        self.config.background_visible = v

    @property
    def text_opacity(self) -> int:
        return self.config.text_opacity

    @text_opacity.setter
    def text_opacity(self, v: int):
        self.config.text_opacity = int(v)

    @property
    def background_opacity(self) -> int:
        return self.config.background_opacity

    @background_opacity.setter
    def background_opacity(self, v: int):
        self.config.background_opacity = int(v)

    @property
    def shadow_enabled(self) -> bool:
        return self.config.shadow_enabled

    @shadow_enabled.setter
    def shadow_enabled(self, v: bool):
        self.config.shadow_enabled = v

    @property
    def shadow_color(self) -> QColor:
        return self._get_color(self.config.shadow_color)

    @shadow_color.setter
    def shadow_color(self, v: Union[QColor, str]):
        self._set_color("shadow_color", v)

    @property
    def shadow_opacity(self) -> int:
        return self.config.shadow_opacity

    @shadow_opacity.setter
    def shadow_opacity(self, v: int):
        self.config.shadow_opacity = int(v)

    @property
    def shadow_blur(self) -> int:
        return self.config.shadow_blur

    @shadow_blur.setter
    def shadow_blur(self, v: int):
        self.config.shadow_blur = int(v)

    @property
    def shadow_scale(self) -> float:
        return self.config.shadow_scale

    @shadow_scale.setter
    def shadow_scale(self, v: float):
        self.config.shadow_scale = float(v)

    @property
    def shadow_offset_x(self) -> float:
        return self.config.shadow_offset_x

    @shadow_offset_x.setter
    def shadow_offset_x(self, v: float):
        self.config.shadow_offset_x = float(v)

    @property
    def shadow_offset_y(self) -> float:
        return self.config.shadow_offset_y

    @shadow_offset_y.setter
    def shadow_offset_y(self, v: float):
        self.config.shadow_offset_y = float(v)

    @property
    def outline_enabled(self) -> bool:
        return self.config.outline_enabled

    @outline_enabled.setter
    def outline_enabled(self, v: bool):
        self.config.outline_enabled = v

    @property
    def outline_color(self) -> QColor:
        return self._get_color(self.config.outline_color)

    @outline_color.setter
    def outline_color(self, v: Union[QColor, str]):
        self._set_color("outline_color", v)

    @property
    def outline_opacity(self) -> int:
        return self.config.outline_opacity

    @outline_opacity.setter
    def outline_opacity(self, v: int):
        self.config.outline_opacity = int(v)

    @property
    def outline_width(self) -> float:
        return self.config.outline_width

    @outline_width.setter
    def outline_width(self, v: float):
        self.config.outline_width = float(v)

    @property
    def outline_blur(self) -> int:
        return self.config.outline_blur

    @outline_blur.setter
    def outline_blur(self, v: int):
        self.config.outline_blur = int(v)

    @property
    def second_outline_enabled(self) -> bool:
        return self.config.second_outline_enabled

    @second_outline_enabled.setter
    def second_outline_enabled(self, v: bool):
        self.config.second_outline_enabled = v

    @property
    def second_outline_color(self) -> QColor:
        return self._get_color(self.config.second_outline_color)

    @second_outline_color.setter
    def second_outline_color(self, v: Union[QColor, str]):
        self._set_color("second_outline_color", v)

    @property
    def second_outline_opacity(self) -> int:
        return self.config.second_outline_opacity

    @second_outline_opacity.setter
    def second_outline_opacity(self, v: int):
        self.config.second_outline_opacity = int(v)

    @property
    def second_outline_width(self) -> float:
        return self.config.second_outline_width

    @second_outline_width.setter
    def second_outline_width(self, v: float):
        self.config.second_outline_width = float(v)

    @property
    def second_outline_blur(self) -> int:
        return self.config.second_outline_blur

    @second_outline_blur.setter
    def second_outline_blur(self, v: int):
        self.config.second_outline_blur = int(v)

    @property
    def third_outline_enabled(self) -> bool:
        return self.config.third_outline_enabled

    @third_outline_enabled.setter
    def third_outline_enabled(self, v: bool):
        self.config.third_outline_enabled = v

    @property
    def third_outline_color(self) -> QColor:
        return self._get_color(self.config.third_outline_color)

    @third_outline_color.setter
    def third_outline_color(self, v: Union[QColor, str]):
        self._set_color("third_outline_color", v)

    @property
    def third_outline_opacity(self) -> int:
        return self.config.third_outline_opacity

    @third_outline_opacity.setter
    def third_outline_opacity(self, v: int):
        self.config.third_outline_opacity = int(v)

    @property
    def third_outline_width(self) -> float:
        return self.config.third_outline_width

    @third_outline_width.setter
    def third_outline_width(self, v: float):
        self.config.third_outline_width = float(v)

    @property
    def third_outline_blur(self) -> int:
        return self.config.third_outline_blur

    @third_outline_blur.setter
    def third_outline_blur(self, v: int):
        self.config.third_outline_blur = int(v)

    @property
    def background_outline_enabled(self) -> bool:
        return self.config.background_outline_enabled

    @background_outline_enabled.setter
    def background_outline_enabled(self, v: bool):
        self.config.background_outline_enabled = v

    @property
    def background_outline_color(self) -> QColor:
        return self._get_color(self.config.background_outline_color)

    @background_outline_color.setter
    def background_outline_color(self, v: Union[QColor, str]):
        self._set_color("background_outline_color", v)

    @property
    def background_outline_opacity(self) -> int:
        return self.config.background_outline_opacity

    @background_outline_opacity.setter
    def background_outline_opacity(self, v: int):
        self.config.background_outline_opacity = int(v)

    @property
    def background_outline_width_ratio(self) -> float:
        return self.config.background_outline_width_ratio

    @background_outline_width_ratio.setter
    def background_outline_width_ratio(self, v: float):
        self.config.background_outline_width_ratio = float(v)

    @property
    def text_gradient_enabled(self) -> bool:
        return self.config.text_gradient_enabled

    @text_gradient_enabled.setter
    def text_gradient_enabled(self, v: bool):
        self.config.text_gradient_enabled = v

    @property
    def text_gradient(self) -> Any:
        return self.config.text_gradient

    @text_gradient.setter
    def text_gradient(self, v: Any):
        self.config.text_gradient = v

    @property
    def text_gradient_angle(self) -> int:
        return self.config.text_gradient_angle

    @text_gradient_angle.setter
    def text_gradient_angle(self, v: int):
        self.config.text_gradient_angle = int(v)

    @property
    def text_gradient_opacity(self) -> int:
        return self.config.text_gradient_opacity

    @text_gradient_opacity.setter
    def text_gradient_opacity(self, v: int):
        self.config.text_gradient_opacity = int(v)

    @property
    def background_gradient_enabled(self) -> bool:
        return self.config.background_gradient_enabled

    @background_gradient_enabled.setter
    def background_gradient_enabled(self, v: bool):
        self.config.background_gradient_enabled = v

    @property
    def background_gradient(self) -> Any:
        return self.config.background_gradient

    @background_gradient.setter
    def background_gradient(self, v: Any):
        self.config.background_gradient = v

    @property
    def background_gradient_angle(self) -> int:
        return self.config.background_gradient_angle

    @background_gradient_angle.setter
    def background_gradient_angle(self, v: int):
        self.config.background_gradient_angle = int(v)

    @property
    def background_gradient_opacity(self) -> int:
        return self.config.background_gradient_opacity

    @background_gradient_opacity.setter
    def background_gradient_opacity(self, v: int):
        self.config.background_gradient_opacity = int(v)

    @property
    def is_vertical(self) -> bool:
        return self.config.is_vertical

    @is_vertical.setter
    def is_vertical(self, v: bool):
        self.config.is_vertical = v

    @property
    def offset_mode(self) -> OffsetMode:
        return self.config.offset_mode

    @offset_mode.setter
    def offset_mode(self, v: OffsetMode):
        self.config.offset_mode = v

    @property
    def horizontal_margin_ratio(self) -> float:
        return self.config.horizontal_margin_ratio

    @horizontal_margin_ratio.setter
    def horizontal_margin_ratio(self, v: float):
        self.config.horizontal_margin_ratio = float(v)

    @property
    def vertical_margin_ratio(self) -> float:
        return self.config.vertical_margin_ratio

    @vertical_margin_ratio.setter
    def vertical_margin_ratio(self, v: float):
        self.config.vertical_margin_ratio = float(v)

    @property
    def margin_top_ratio(self) -> float:
        return self.config.margin_top

    @margin_top_ratio.setter
    def margin_top_ratio(self, v: float):
        self.config.margin_top = float(v)

    @property
    def margin_bottom_ratio(self) -> float:
        return self.config.margin_bottom

    @margin_bottom_ratio.setter
    def margin_bottom_ratio(self, v: float):
        self.config.margin_bottom = float(v)

    @property
    def margin_left_ratio(self) -> float:
        return self.config.margin_left

    @margin_left_ratio.setter
    def margin_left_ratio(self, v: float):
        self.config.margin_left = float(v)

    @property
    def margin_right_ratio(self) -> float:
        return self.config.margin_right

    @margin_right_ratio.setter
    def margin_right_ratio(self, v: float):
        self.config.margin_right = float(v)

    @property
    def background_corner_ratio(self) -> float:
        return self.config.background_corner_ratio

    @background_corner_ratio.setter
    def background_corner_ratio(self, v: float):
        self.config.background_corner_ratio = float(v)

    # --- Core Logic ---

    def paintEvent(self, event: Any) -> None:
        """ペイントイベントのオーバーライド。

        Args:
            event: QPaintEventオブジェクト。
        """
        super().paintEvent(event)
        painter = QPainter(self)
        self.draw_selection_frame(painter)
        painter.end()

    def update_text(self) -> None:
        """TextRendererの描画をデバウンスして実行する。

        Notes:
            高負荷なTextRenderer.render()を、連続操作中に毎回走らせないための対策。
            見た目（最終結果）は同じで、操作中の“無駄な中間レンダ”だけを減らす。
        """
        try:
            if hasattr(self, "_render_timer"):
                # 連打されても最後の1回だけ描画する
                self._render_timer.start(int(getattr(self, "_render_debounce_ms", 25)))
                return
        except Exception:
            pass

        # フォールバック：タイマーが使えない場合は即時
        self._update_text_immediate()

    def update_text_debounced(self) -> None:
        """描画更新をデバウンス予約する（外部から呼ぶ用）。

        Notes:
            ホイール等で連打される操作は、Undoは積みつつ描画は最後の1回に寄せる。
            最終結果（表示）は同じで、無駄な中間レンダを削減する。
        """
        try:
            if hasattr(self, "_render_timer"):
                self._render_timer.start(int(getattr(self, "_render_debounce_ms", 25)))
                return
        except Exception:
            pass

        self._update_text_immediate()

    def _update_text_immediate(self) -> None:
        """TextRendererを使用して即時描画する（内部用）。"""
        try:
            pixmap = self.renderer.render(self)
            if pixmap:
                self.setPixmap(pixmap)
                try:
                    self.sig_properties_changed.emit(self)
                except Exception:
                    pass
            else:
                logger.error(f"Renderer returned empty pixmap for window {self.uuid}")
        except Exception as e:
            logger.error(f"Render error in TextWindow {self.uuid}: {e}\n{traceback.format_exc()}")

    def set_undoable_property(
        self,
        property_name: str,
        new_value: Any,
        update_method_name: Optional[str] = None,
    ) -> None:
        """Undo可能な形式でプロパティを変更する（TextWindow用の最適化）。

        Notes:
            font_size はホイール操作で連打されやすく、update_text が重い。
            そのため font_size 変更時は update_text を即時実行せず、デバウンス予約に寄せる。

        Args:
            property_name (str): 変更プロパティ名。
            new_value (Any): 新しい値。
            update_method_name (Optional[str]): 通常の更新メソッド名。
        """
        # font_size は常に「即時update_text」にならないようにする
        if property_name == "font_size":
            super().set_undoable_property(property_name, new_value, None)
            self.update_text_debounced()
            return

        super().set_undoable_property(property_name, new_value, update_method_name)

    def set_offset_mode_a(self) -> None:
        self.set_undoable_property("offset_mode", OffsetMode.MONO, "update_text")

    def set_offset_mode_b(self) -> None:
        self.set_undoable_property("offset_mode", OffsetMode.PROP, "update_text")

    def toggle_outline(self) -> None:
        self.set_undoable_property("outline_enabled", not self.outline_enabled, "update_text")

    def change_outline_color(self) -> None:
        color = QColorDialog.getColor(self.outline_color, self)
        if color.isValid():
            self.set_undoable_property("outline_color", color, "update_text")

    def toggle_second_outline(self) -> None:
        self.set_undoable_property("second_outline_enabled", not self.second_outline_enabled, "update_text")

    def change_second_outline_color(self) -> None:
        color = QColorDialog.getColor(self.second_outline_color, self)
        if color.isValid():
            self.set_undoable_property("second_outline_color", color, "update_text")

    def toggle_third_outline(self) -> None:
        self.set_undoable_property("third_outline_enabled", not self.third_outline_enabled, "update_text")

    def change_third_outline_color(self) -> None:
        color = QColorDialog.getColor(self.third_outline_color, self)
        if color.isValid():
            self.set_undoable_property("third_outline_color", color, "update_text")

    def toggle_vertical_text(self) -> None:
        self.set_undoable_property("is_vertical", not self.is_vertical, "update_text")

    def set_horizontal_margin_ratio(self) -> None:
        dialog = MarginRatioDialog(
            tr("title_set_h_margin"), tr("label_char_spacing_horz"), self.horizontal_margin_ratio, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.set_undoable_property("horizontal_margin_ratio", dialog.get_value(), "update_text")

    def set_vertical_margin_ratio(self) -> None:
        dialog = MarginRatioDialog(
            tr("title_set_v_margin"), tr("label_line_spacing_vert"), self.vertical_margin_ratio, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.set_undoable_property("vertical_margin_ratio", dialog.get_value(), "update_text")

    def keyPressEvent(self, event: Any) -> None:
        """キープレスイベントの管理。

        ロック中は配置が変わる操作（ノード追加/ナビ/変形）を無効化する。
        ただし管理系（Delete/H/F）は許可する。

        Args:
            event (Any): QKeyEvent
        """
        try:
            locked: bool = bool(getattr(self, "is_locked", False))

            # --- 管理系（ロック中でも許可）---
            if event.key() == Qt.Key_Delete:
                self.close()
                event.accept()
                return

            if event.key() == Qt.Key_H:
                self.hide_action()
                event.accept()
                return

            if event.key() == Qt.Key_F:
                self.toggle_frontmost()
                event.accept()
                return

            # --- ロック中はここから先を止める ---
            if locked:
                event.accept()
                return

            # --- 配置/ノード操作 ---
            if event.key() == Qt.Key_Tab:
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "create_related_node"
                ):
                    self.main_window.window_manager.create_related_node(self, "child")
                event.accept()
                return

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "create_related_node"
                ):
                    self.main_window.window_manager.create_related_node(self, "sibling")
                event.accept()
                return

            # --- ナビゲーション ---
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "navigate_selection"
                ):
                    self.main_window.window_manager.navigate_selection(self, event.key())
                event.accept()
                return

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Error handling key press: {e}")
            traceback.print_exc()
            event.accept()
            return

        # デフォルト処理
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: Any) -> None:
        if event.modifiers() & Qt.ControlModifier:
            super().mouseDoubleClickEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.change_text()

    def _restore_render_debounce_ms_after_wheel(self) -> None:
        """ホイール操作後に描画デバウンス値を標準へ戻す。"""
        try:
            self._render_debounce_ms = 25
        except Exception:
            pass

    def wheelEvent(self, event: Any) -> None:
        """マウスホイールによるフォントサイズ変更。

        ロック中は誤操作防止のため無効化する。
        """
        try:
            if bool(getattr(self, "is_locked", False)):
                event.accept()
                return

            angle = event.angleDelta().y()
            if angle == 0:
                return

            step = 2
            current_size = self.font_size

            # 上回転で縮小、下回転で拡大
            new_size = (current_size - step) if angle > 0 else (current_size + step)
            new_size = max(5, min(500, new_size))

            if new_size != current_size:
                # Undoは積むが、即時レンダ(update_text)は走らせない
                # → 描画はデバウンス予約で最後の1回に寄せる
                self.set_undoable_property("font_size", new_size, None)
                self.update_text_debounced()

            # ホイール中だけデバウンスを強めて、フリーズ感をさらに減らす
            try:
                # 設定値があればそれを使い、なければ80
                val = getattr(self, "_wheel_debounce_setting", 80)
                self._render_debounce_ms = int(val)
                self._wheel_render_relax_timer.start(150)
            except Exception:
                pass

            event.accept()

        except Exception:
            traceback.print_exc()

    def toggle_text_visibility(self) -> None:
        if self.text_opacity > 0:
            self._previous_text_opacity = self.text_opacity
            new_opacity = 0
        else:
            new_opacity = getattr(self, "_previous_text_opacity", 100)
        self.set_undoable_property("text_opacity", new_opacity, "update_text")

    def toggle_background_visibility(self) -> None:
        if self.background_opacity > 0:
            self._previous_background_opacity = self.background_opacity
            new_opacity = 0
        else:
            new_opacity = getattr(self, "_previous_background_opacity", 100)
        self.set_undoable_property("background_opacity", new_opacity, "update_text")

    def change_text(self) -> None:
        """リアルタイムプレビュー付きでテキストを変更し、変更をログに記録します。"""
        original_text = self.text

        def live_update_callback(new_text: str):
            try:
                self.text = new_text
                self.update_text()
            except Exception as e:
                logger.error(f"Live update failed: {e}")

        try:
            dialog = TextInputDialog(self.text, self, callback=live_update_callback)

            # ダイアログの配置ロジック
            screen = self.screen()
            if screen:
                screen_geo = screen.availableGeometry()
                win_geo = self.geometry()
                dlg_w, dlg_h, padding = dialog.width(), dialog.height(), 20

                target_x = win_geo.right() + padding
                if target_x + dlg_w > screen_geo.right():
                    target_x = win_geo.left() - dlg_w - padding
                target_y = max(screen_geo.top(), min(win_geo.top(), screen_geo.bottom() - dlg_h))
                dialog.move(target_x, target_y)

            if dialog.exec() == QDialog.Accepted:
                final_text = dialog.get_text()
                self.text = original_text
                if final_text != original_text:
                    self.set_undoable_property("text", final_text, "update_text")
                    logger.info(f"Text changed for {self.uuid}")
                else:
                    self.update_text()
            else:
                self.text = original_text
                self.update_text()

        except Exception as e:
            logger.error(f"Error in change_text dialog: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open edit dialog: {e}")
            self.text = original_text
            self.update_text()

    def change_font(self) -> None:
        """フォント選択ダイアログを表示し、適用する。"""
        font_dialog = QFontDialog(self)
        font_dialog.setCurrentFont(QFont(self.font_family, int(self.font_size)))
        if font_dialog.exec() == QFontDialog.Accepted:
            font = font_dialog.selectedFont()
            if isinstance(font, QFont):
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.beginMacro("Change Font")
                self.set_undoable_property("font_family", font.family(), None)
                self.set_undoable_property("font_size", font.pointSize(), None)
                self.auto_detect_offset_mode(font)
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.endMacro()

    def change_font_color(self) -> None:
        color = QColorDialog.getColor(self.font_color, self)
        if color.isValid():
            self.set_undoable_property("font_color", color, "update_text")

    def change_background_color(self) -> None:
        color = QColorDialog.getColor(self.background_color, self)
        if color.isValid():
            self.set_undoable_property("background_color", color, "update_text")

    def toggle_shadow(self) -> None:
        self.set_undoable_property("shadow_enabled", not self.shadow_enabled, "update_text")

    def change_shadow_color(self) -> None:
        color = QColorDialog.getColor(self.shadow_color, self)
        if color.isValid():
            self.set_undoable_property("shadow_color", color, "update_text")

    def add_text_window(self) -> None:
        """新規テキストウィンドウを追加する（WindowManager 経由で生成）。

        目的:
            - 生成経路を WindowManager に統一し、FREE制限・選択同期・シグナル接続・管理リストの整合性を守る。

        """
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            # 自分の近くに出す（少しずらす）
            new_pos: QPoint = self.pos() + QPoint(20, 20)

            _w: Optional["TextWindow"] = mw.window_manager.add_text_window(
                text=tr("new_text_default"),
                pos=new_pos,
                suppress_limit_message=False,
            )
            # None の場合（FREE制限等）は WindowManager 側で通知される想定

        except Exception as e:
            logger.error("Failed to add TextWindow via WindowManager: %s\n%s", e, traceback.format_exc())
            QMessageBox.critical(self, tr("msg_error"), f"Failed to add text window: {e}")

    def clone_text(self) -> None:
        """現在のテキストウィンドウを複製します（WindowManager に委譲）。

        目的:
            - クローンの生成経路を WindowManager に一本化し、制限・選択同期・シグナル接続の整合性を保つ。
        """
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            mw.window_manager.clone_text_window(self)

        except Exception as e:
            logger.error("Failed to clone TextWindow via WindowManager: %s\n%s", e, traceback.format_exc())
            QMessageBox.critical(self, tr("msg_error"), f"Clone failed: {e}")

    def save_as_png(self) -> None:
        """現在の描画結果をPNG画像として保存し、結果をログに記録します。"""
        try:
            first_line = self.text.split("\n")[0]
            file_name, _ = QFileDialog.getSaveFileName(
                self, tr("title_save_png"), f"{first_line}.png", "PNG Files (*.png)"
            )

            if file_name:
                self._update_text_immediate()
                pixmap = self.pixmap()
                if pixmap:
                    if pixmap.save(file_name, "PNG"):
                        logger.info(f"Successfully saved PNG: {file_name}")
                    else:
                        raise IOError(f"Failed to save image file at {file_name}")
                else:
                    raise ValueError("Pixmap is empty, cannot save.")

        except Exception as e:
            logger.error(f"Error saving PNG: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, tr("msg_error"), f"Could not save image: {e}")

    def hide_all_other_windows(self) -> None:
        """自分以外のテキストを隠す（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.hide_all_other_text_windows(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to hide other text windows: {e}")
            traceback.print_exc()

    def close_all_other_windows(self) -> None:
        """自分以外のテキストを閉じる（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.close_all_other_text_windows(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to close other text windows: {e}")
            traceback.print_exc()

    def save_text_to_json(self) -> None:
        """設定をJSONファイルに保存します（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.save_window_to_json(self)

    def load_text_from_json(self) -> None:
        """JSONファイルから設定を読み込みます（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.load_window_from_json(self)

    def toggle_text_gradient(self) -> None:
        self.set_undoable_property("text_gradient_enabled", not self.text_gradient_enabled, "update_text")

    def toggle_background_gradient(self) -> None:
        self.set_undoable_property("background_gradient_enabled", not self.background_gradient_enabled, "update_text")

    def edit_text_gradient(self) -> None:
        dialog = GradientEditorDialog(self.text_gradient, self.text_gradient_angle, self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Edit Text Gradient")
            self.set_undoable_property("text_gradient", dialog.get_gradient(), None)
            self.set_undoable_property("text_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def edit_background_gradient(self) -> None:
        dialog = GradientEditorDialog(self.background_gradient, self.background_gradient_angle, self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Edit Background Gradient")
            self.set_undoable_property("background_gradient", dialog.get_gradient(), None)
            self.set_undoable_property("background_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def _open_slider_dialog(
        self,
        title: str,
        label: str,
        min_val: float,
        max_val: float,
        initial_val: float,
        property_name: str,
        update_method_name: str,
        decimals: int = 0,
        suffix: str = "",
    ) -> None:
        """プレビュー中Undoなし・OKで1回Undoのスライダーダイアログ共通処理（TextWindow版）。

        Args:
            title (str): タイトル
            label (str): ラベル
            min_val (float): 最小
            max_val (float): 最大
            initial_val (float): 初期値（現在値）
            property_name (str): 変更するプロパティ名
            update_method_name (str): 更新メソッド名（例: update_text）
            decimals (int): 小数桁
            suffix (str): サフィックス
        """
        try:
            from ui.dialogs import PreviewCommitDialog

            # Cancel復帰用に「確定前の値」を保持
            try:
                old_value: Any = getattr(self, property_name)
            except Exception:
                old_value = initial_val

            # プレビュー適用（Undoなし）
            def on_preview(val: float) -> None:
                try:
                    # もとの型に寄せる（int/float）
                    target_type = type(old_value)
                    v = target_type(val)

                    setattr(self, property_name, v)
                    if update_method_name and hasattr(self, update_method_name):
                        getattr(self, update_method_name)()
                except Exception:
                    pass

            # 確定適用（Undoあり：1回だけ）
            def on_commit(val: float) -> None:
                try:
                    target_type = type(old_value)
                    new_value = target_type(val)

                    # 変化が無ければ戻して終了（Undoを積まない）
                    if new_value == old_value:
                        on_preview(float(old_value))
                        return

                    # Undo化された変更として積む（内部で command を積む）
                    self.set_undoable_property(property_name, new_value, update_method_name)
                except Exception:
                    pass

            dialog = PreviewCommitDialog(
                title=title,
                label=label,
                min_val=float(min_val),
                max_val=float(max_val),
                initial_val=float(old_value),
                on_preview=on_preview,
                on_commit=on_commit,
                parent=self,
                suffix=suffix,
                decimals=decimals,
            )
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open dialog: {e}")
            traceback.print_exc()

    def open_text_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_text_opacity"), tr("label_opacity"), 0, 100, self.text_opacity, "text_opacity", "update_text"
        )

    def open_background_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_bg_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_opacity,
            "background_opacity",
            "update_text",
        )

    def open_shadow_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.shadow_opacity,
            "shadow_opacity",
            "update_text",
        )

    def open_shadow_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_blur"),
            tr("label_blur"),
            0,
            100,
            self.shadow_blur,
            "shadow_blur",
            "update_text",
            suffix="%",
        )

    def open_shadow_scale_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_shadow_scale"),
            tr("label_shadow_scale"),
            0.01,
            10.0,
            self.shadow_scale,
            "shadow_scale",
            "update_text",
            decimals=2,
        )

    def open_text_gradient_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("menu_set_text_gradient_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.text_gradient_opacity,
            "text_gradient_opacity",
            "update_text",
        )

    def open_background_gradient_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("menu_set_bg_gradient_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_gradient_opacity,
            "background_gradient_opacity",
            "update_text",
        )

    def open_bg_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_bg_outline_width"),
            tr("label_bg_outline_width"),
            0.0,
            1.0,
            self.background_outline_width_ratio,
            "background_outline_width_ratio",
            "update_text",
            decimals=2,
        )

    def open_bg_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_bg_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.background_outline_opacity,
            "background_outline_opacity",
            "update_text",
        )

    def open_bg_corner_ratio_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_bg_corner"),
            tr("label_ratio"),
            0.0,
            2.0,
            self.background_corner_ratio,
            "background_corner_ratio",
            "update_text",
            decimals=2,
        )

    def open_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.outline_opacity,
            "outline_opacity",
            "update_text",
        )

    def open_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.outline_width,
            "outline_width",
            "update_text",
            decimals=1,
        )

    def open_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.outline_blur,
            "outline_blur",
            "update_text",
            suffix="%",
        )

    def open_second_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_second_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.second_outline_opacity,
            "second_outline_opacity",
            "update_text",
        )

    def open_second_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_second_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.second_outline_width,
            "second_outline_width",
            "update_text",
            decimals=1,
        )

    def open_second_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_second_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.second_outline_blur,
            "second_outline_blur",
            "update_text",
            suffix="%",
        )

    def open_third_outline_opacity_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_third_outline_opacity"),
            tr("label_opacity"),
            0,
            100,
            self.third_outline_opacity,
            "third_outline_opacity",
            "update_text",
        )

    def open_third_outline_width_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_set_third_outline_width"),
            tr("label_width"),
            0.1,
            100.0,
            self.third_outline_width,
            "third_outline_width",
            "update_text",
            decimals=1,
        )

    def open_third_outline_blur_dialog(self) -> None:
        self._open_slider_dialog(
            tr("title_change_third_outline_blur"),
            tr("label_blur"),
            0,
            100,
            self.third_outline_blur,
            "third_outline_blur",
            "update_text",
            suffix="%",
        )

    def set_shadow_offsets(self) -> None:
        old_x, old_y = self.shadow_offset_x, self.shadow_offset_y

        def preview_callback(x: float, y: float):
            self.shadow_offset_x, self.shadow_offset_y = x, y
            self.update_text()

        dialog = ShadowOffsetDialog(
            tr("title_set_shadow_offsets"), old_x, old_y, callback=preview_callback, parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            new_x, new_y = dialog.get_offsets()
            if old_x != new_x or old_y != new_y:
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.beginMacro("Set Shadow Offsets")
                self.set_undoable_property("shadow_offset_x", new_x, None)
                self.set_undoable_property("shadow_offset_y", new_y, "update_text")
                if hasattr(self.main_window, "undo_stack"):
                    self.main_window.undo_stack.endMacro()

    def toggle_background_outline(self) -> None:
        self.set_undoable_property("background_outline_enabled", not self.background_outline_enabled, "update_text")

    def change_background_outline_color(self) -> None:
        color = QColorDialog.getColor(self.background_outline_color, self)
        if color.isValid():
            self.set_undoable_property("background_outline_color", color, "update_text")

    def auto_detect_offset_mode(self, font: QFont) -> None:
        fm = QFontMetrics(font)
        self.offset_mode = (
            OffsetMode.MONO if fm.horizontalAdvance("i") == fm.horizontalAdvance("W") else OffsetMode.PROP
        )

    def load_text_defaults(self) -> Dict[str, float]:
        json_path = os.path.join(self.main_window.json_directory, "text_defaults.json")
        default_settings = {
            "h_margin": 0.0,
            "v_margin": 0.2,
            "margin_top": 0.3,
            "margin_bottom": 0.3,
            "margin_left": 0.3,
            "margin_right": 0.0,
        }
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    default_settings.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load text defaults from {json_path}: {e}")
        return default_settings

    def open_spacing_settings(self) -> None:
        dialog = TextSpacingDialog(
            self.horizontal_margin_ratio,
            self.vertical_margin_ratio,
            self.margin_top_ratio,
            self.margin_bottom_ratio,
            self.margin_left_ratio,
            self.margin_right_ratio,
            self,
        )
        if dialog.exec() == QDialog.Accepted:
            vals = dialog.get_values()
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Change Spacing")
            attrs = [
                "horizontal_margin_ratio",
                "vertical_margin_ratio",
                "margin_top_ratio",
                "margin_bottom_ratio",
                "margin_left_ratio",
                "margin_right_ratio",
            ]
            for i, attr in enumerate(attrs[:-1]):
                self.set_undoable_property(attr, vals[i], None)
            self.set_undoable_property(attrs[-1], vals[-1], "update_text")
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def show_property_panel(self) -> None:
        self.sig_request_property_panel.emit(self)

    def propagate_scale_to_children(self, ratio: float) -> None:
        """子ウィンドウに対してスケーリングを伝搬させる。

        Args:
            ratio (float): スケール倍率。
        """
        if not self.child_windows:
            return
        parent_center = self.geometry().center()
        for child in self.child_windows:
            try:
                vec = child.geometry().center() - parent_center
                new_center = parent_center + QPoint(vec.x() * ratio, vec.y() * ratio)
                if hasattr(child, "font_size"):
                    child.font_size *= ratio
                    child.update_text()
                elif hasattr(child, "scale_factor"):
                    child.scale_factor *= ratio
                    child.update_image()
                child.move(int(new_center.x() - child.width() / 2), int(new_center.y() - child.height() / 2))
                if hasattr(child, "propagate_scale_to_children"):
                    child.propagate_scale_to_children(ratio)
            except Exception:
                pass  # Error propagating scale

    # --- UI Menu ---

    def show_context_menu(self, pos: QPoint) -> None:
        """コンテキストメニューを構築して表示する。
        Args:
            pos (QPoint): 表示位置。
        """
        try:
            builder = ContextMenuBuilder(self, self.main_window)

            builder.add_connect_group_menu()
            builder.add_action("menu_show_properties", self.show_property_panel)
            builder.add_separator()

            # スタイルプリセット
            if hasattr(self.main_window, "style_manager"):
                style_menu = builder.add_submenu("menu_style_presets")
                builder.add_action("menu_open_style_gallery", self.open_style_gallery, parent_menu=style_menu)
                builder.add_separator(parent_menu=style_menu)
                builder.add_action(
                    "menu_save_style",
                    lambda: self.main_window.style_manager.save_text_style(self),
                    parent_menu=style_menu,
                )
                builder.add_action(
                    "menu_load_style_file",
                    lambda: self.main_window.style_manager.load_text_style(self),
                    parent_menu=style_menu,
                )

            builder.add_separator()
            builder.add_action("menu_change_text", self.change_text)
            builder.add_action("menu_add_text", self.add_text_window)
            builder.add_action("menu_clone_text", self.clone_text)
            builder.add_action("menu_save_png", self.save_as_png)
            builder.add_action("menu_save_json", self.save_text_to_json)
            builder.add_action("menu_load_json", self.main_window.file_manager.load_scene_from_json)
            builder.add_separator()

            # テキスト表示
            builder.add_action(
                "menu_toggle_text", self.toggle_text_visibility, checkable=True, checked=(self.text_opacity > 0)
            )

            # テキスト設定
            text_menu = builder.add_submenu("menu_text_settings")
            builder.add_action("menu_change_font", self.change_font, parent_menu=text_menu)
            builder.add_action("menu_change_color", self.change_font_color, parent_menu=text_menu)
            builder.add_action("menu_change_text_opacity", self.open_text_opacity_dialog, parent_menu=text_menu)
            builder.add_separator()

            # 背景
            builder.add_action(
                "menu_toggle_background",
                self.toggle_background_visibility,
                checkable=True,
                checked=(self.background_opacity > 0),
            )
            builder.add_action(
                "menu_toggle_bg_outline",
                self.toggle_background_outline,
                checkable=True,
                checked=self.background_outline_enabled,
            )

            bg_menu = builder.add_submenu("menu_bg_settings")
            builder.add_action("menu_change_bg_color", self.change_background_color, parent_menu=bg_menu)
            builder.add_action("menu_change_bg_opacity", self.open_background_opacity_dialog, parent_menu=bg_menu)
            builder.add_separator(parent_menu=bg_menu)
            builder.add_action(
                "menu_change_bg_outline_color", self.change_background_outline_color, parent_menu=bg_menu
            )
            builder.add_action("menu_change_bg_outline_width", self.open_bg_outline_width_dialog, parent_menu=bg_menu)
            builder.add_action(
                "menu_change_bg_outline_opacity", self.open_bg_outline_opacity_dialog, parent_menu=bg_menu
            )
            builder.add_separator(parent_menu=bg_menu)
            builder.add_action("menu_set_bg_corner", self.open_bg_corner_ratio_dialog, parent_menu=bg_menu)
            builder.add_separator()

            # 影
            builder.add_action("menu_toggle_shadow", self.toggle_shadow, checkable=True, checked=self.shadow_enabled)
            shadow_menu = builder.add_submenu("menu_shadow_settings")
            builder.add_action("menu_change_shadow_color", self.change_shadow_color, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_opacity", self.open_shadow_opacity_dialog, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_scale", self.open_shadow_scale_dialog, parent_menu=shadow_menu)
            builder.add_action("menu_set_shadow_offsets", self.set_shadow_offsets, parent_menu=shadow_menu)
            builder.add_action("menu_change_shadow_blur", self.open_shadow_blur_dialog, parent_menu=shadow_menu)
            builder.add_separator()

            # グラデーション（テキスト）
            builder.add_action(
                "menu_toggle_text_gradient",
                self.toggle_text_gradient,
                checkable=True,
                checked=self.text_gradient_enabled,
            )
            grad_text_menu = builder.add_submenu("menu_text_gradient_settings")
            builder.add_action("menu_edit_text_gradient", self.edit_text_gradient, parent_menu=grad_text_menu)
            builder.add_action(
                "menu_set_text_gradient_opacity", self.open_text_gradient_opacity_dialog, parent_menu=grad_text_menu
            )
            builder.add_separator()

            # グラデーション（背景）
            builder.add_action(
                "menu_toggle_bg_gradient",
                self.toggle_background_gradient,
                checkable=True,
                checked=self.background_gradient_enabled,
            )
            grad_bg_menu = builder.add_submenu("menu_bg_gradient_settings")
            builder.add_action("menu_edit_bg_gradient", self.edit_background_gradient, parent_menu=grad_bg_menu)
            builder.add_action(
                "menu_set_bg_gradient_opacity", self.open_background_gradient_opacity_dialog, parent_menu=grad_bg_menu
            )
            builder.add_separator()

            # 縁取り（1〜3）
            outline_parent_menu = builder.add_submenu("menu_outline_parent_settings")
            for i, prefix in enumerate(["", "second_", "third_"], 1):
                enabled = getattr(self, f"{prefix}outline_enabled")
                builder.add_action(
                    f"menu_toggle_{prefix}outline",
                    getattr(self, f"toggle_{prefix}outline"),
                    checkable=True,
                    checked=enabled,
                    parent_menu=outline_parent_menu,
                )
                sub = builder.add_submenu(f"menu_{prefix}outline_settings", parent_menu=outline_parent_menu)
                builder.add_action(
                    f"menu_change_{prefix}outline_color",
                    getattr(self, f"change_{prefix}outline_color"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_opacity",
                    getattr(self, f"open_{prefix}outline_opacity_dialog"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_width",
                    getattr(self, f"open_{prefix}outline_width_dialog"),
                    parent_menu=sub,
                )
                builder.add_action(
                    f"menu_change_{prefix}outline_blur",
                    getattr(self, f"open_{prefix}outline_blur_dialog"),
                    parent_menu=sub,
                )
                if i < 3:
                    builder.add_separator(parent_menu=outline_parent_menu)

            builder.add_separator()

            # 縦書き設定
            builder.add_action(
                "menu_toggle_vertical", self.toggle_vertical_text, checkable=True, checked=self.is_vertical
            )
            vert_menu = builder.add_submenu("menu_vertical_font_type")
            builder.add_action(
                "menu_mono_font",
                self.set_offset_mode_a,
                checkable=True,
                checked=(self.offset_mode == OffsetMode.MONO),
                parent_menu=vert_menu,
            )
            builder.add_action(
                "menu_prop_font",
                self.set_offset_mode_b,
                checkable=True,
                checked=(self.offset_mode == OffsetMode.PROP),
                parent_menu=vert_menu,
            )

            builder.add_separator()

            # 余白設定
            builder.add_action("menu_margin_settings", self.open_spacing_settings)
            builder.add_separator()

            # --- アニメ関連は完全撤去（MainWindowのAnimationタブに一本化） ---

            builder.add_action(
                "menu_toggle_frontmost", self.toggle_frontmost, checkable=True, checked=self.is_frontmost
            )
            builder.add_action("menu_hide_text", self.hide_action)
            builder.add_action("menu_hide_others", self.hide_all_other_windows)
            builder.add_action("menu_show_text", self.show_action)

            builder.add_separator()

            builder.add_action("menu_close_others", self.close_all_other_windows)
            builder.add_action("menu_close_text", self.close)

            builder.add_separator()

            builder.add_action(
                "menu_lock_transform",
                lambda checked: self.set_undoable_property("is_locked", bool(checked), None),
                checkable=True,
                checked=bool(getattr(self, "is_locked", False)),
            )

            builder.add_separator()

            builder.add_action(
                "menu_click_through",
                lambda: self.set_click_through(not self.is_click_through),
                checkable=True,
                checked=self.is_click_through,
            )

            builder.exec(self.mapToGlobal(pos))

        except Exception:
            pass  # An error occurred in show_context_menu
            # (以下略とさせていただきますが、メニュー内の load_scene_from_json 部分のみの差し替えでOKです)

    def open_style_gallery(self) -> None:
        """スタイルギャラリーダイアログを表示し、選択されたスタイルを適用する。"""
        dialog = StyleGalleryDialog(self.main_window.style_manager, self)
        if dialog.exec() == QDialog.Accepted:
            json_path = dialog.get_selected_style_path()
            if json_path:
                self.main_window.style_manager.load_text_style(self, json_path)
