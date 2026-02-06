import logging
import traceback
from typing import Any, Union

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from models.constants import AppDefaults
from windows.text_renderer import TextRenderer

logger = logging.getLogger(__name__)


class TextPropertiesMixin:
    """
    Mixin to provide common text properties and rendering logic for BaseOverlayWindow.
    Assumes self.config exists and follows TextWindowConfig structure.
    """

    def _init_text_renderer(self, main_window: Any) -> None:
        """Initialize renderer and timers. Call this from __init__."""
        try:
            self.renderer = TextRenderer()

            # --- Apply Performance Settings ---
            try:
                self.renderer._glyph_cache_size = int(
                    getattr(main_window.app_settings, "glyph_cache_size", AppDefaults.GLYPH_CACHE_SIZE)
                )
            except Exception:
                pass

            # --- Timers ---
            # Debounce timer for high-load rendering (e.g., resizing)
            self._render_timer: QTimer = QTimer(self)
            self._render_timer.setSingleShot(True)
            self._render_timer.timeout.connect(self._update_text_immediate)

            # Debounce relaxation timer for wheel operations
            self._wheel_render_relax_timer: QTimer = QTimer(self)
            self._wheel_render_relax_timer.setSingleShot(True)
            self._wheel_render_relax_timer.timeout.connect(self._restore_render_debounce_ms_after_wheel)

            # --- Load settings ---
            if hasattr(main_window, "app_settings") and main_window.app_settings:
                self._render_debounce_ms: int = int(
                    getattr(main_window.app_settings, "render_debounce_ms", AppDefaults.RENDER_DEBOUNCE_MS)
                )
                self._wheel_debounce_setting: int = int(
                    getattr(main_window.app_settings, "wheel_debounce_ms", AppDefaults.WHEEL_DEBOUNCE_MS)
                )
            else:
                self._render_debounce_ms = AppDefaults.RENDER_DEBOUNCE_MS
                self._wheel_debounce_setting = AppDefaults.WHEEL_DEBOUNCE_MS

        except Exception as e:
            logger.error(f"Failed to initialize TextPropertiesMixin: {e}")

    # ==========================================
    # Properties
    # ==========================================

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

    # --- Shadow ---
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

    # --- Outlines ---
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

    # --- Gradients ---
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

    # --- Vertical ---
    @property
    def is_vertical(self) -> bool:
        return self.config.is_vertical

    @is_vertical.setter
    def is_vertical(self, v: bool):
        self.config.is_vertical = v

    # --- Margins & Spacing ---
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
    def char_spacing_h(self) -> float:
        return getattr(self.config, "char_spacing_h", self.config.horizontal_margin_ratio)

    @char_spacing_h.setter
    def char_spacing_h(self, v: float):
        self.config.char_spacing_h = float(v)

    @property
    def line_spacing_h(self) -> float:
        return getattr(self.config, "line_spacing_h", 0.0)

    @line_spacing_h.setter
    def line_spacing_h(self, v: float):
        self.config.line_spacing_h = float(v)

    @property
    def char_spacing_v(self) -> float:
        return getattr(self.config, "char_spacing_v", 0.0)

    @char_spacing_v.setter
    def char_spacing_v(self, v: float):
        self.config.char_spacing_v = float(v)

    @property
    def line_spacing_v(self) -> float:
        return getattr(self.config, "line_spacing_v", self.config.vertical_margin_ratio)

    @line_spacing_v.setter
    def line_spacing_v(self, v: float):
        self.config.line_spacing_v = float(v)

    @property
    def v_margin_top_ratio(self) -> float:
        return self.config.v_margin_top if self.config.v_margin_top is not None else 0.0

    @v_margin_top_ratio.setter
    def v_margin_top_ratio(self, v: float):
        self.config.v_margin_top = float(v)

    @property
    def v_margin_bottom_ratio(self) -> float:
        return self.config.v_margin_bottom if self.config.v_margin_bottom is not None else 0.0

    @v_margin_bottom_ratio.setter
    def v_margin_bottom_ratio(self, v: float):
        self.config.v_margin_bottom = float(v)

    @property
    def v_margin_left_ratio(self) -> float:
        return self.config.v_margin_left if self.config.v_margin_left is not None else 0.0

    @v_margin_left_ratio.setter
    def v_margin_left_ratio(self, v: float):
        self.config.v_margin_left = float(v)

    @property
    def v_margin_right_ratio(self) -> float:
        return self.config.v_margin_right if self.config.v_margin_right is not None else 0.0

    @v_margin_right_ratio.setter
    def v_margin_right_ratio(self, v: float):
        self.config.v_margin_right = float(v)

    @property
    def background_corner_ratio(self) -> float:
        return self.config.background_corner_ratio

    @background_corner_ratio.setter
    def background_corner_ratio(self, v: float):
        self.config.background_corner_ratio = float(v)

    # ==========================================
    # Rendering Methods
    # ==========================================

    def update_text(self) -> None:
        """TextRendererの描画をデバウンスして実行する。"""
        try:
            if hasattr(self, "_render_timer"):
                self._render_timer.start(int(getattr(self, "_render_debounce_ms", AppDefaults.RENDER_DEBOUNCE_MS)))
                return
        except Exception:
            pass
        self._update_text_immediate()

    def update_text_debounced(self) -> None:
        """描画更新をデバウンス予約する（外部から呼ぶ用）。"""
        try:
            if hasattr(self, "_render_timer"):
                self._render_timer.start(int(getattr(self, "_render_debounce_ms", AppDefaults.RENDER_DEBOUNCE_MS)))
                return
        except Exception:
            pass
        self._update_text_immediate()

    def _update_text_immediate(self) -> None:
        """TextRendererを使用して即時描画する（内部用）。
        Subclasses can override, but calling super()._update_text_immediate() is recommended.
        """
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
            logger.error(
                f"Render error in TextPropertiesMixin (uuid={getattr(self, 'uuid', 'unknown')}): {e}\n{traceback.format_exc()}"
            )

    def _restore_render_debounce_ms_after_wheel(self) -> None:
        """ホイール操作後に描画デバウンス値を標準へ戻す。"""
        try:
            self._render_debounce_ms = 25
        except Exception:
            pass
