# ui/mindmap/mindmap_text_adapter.py
"""
MindMapNode と TextRenderer を繋ぐアダプタクラス。

TextRenderer は window オブジェクトの各プロパティを直接読み取るため、
MindMapNodeConfig の値を TextRenderer が期待する形式で提供する。
"""

import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QPixmap

if TYPE_CHECKING:
    from models.mindmap_node_config import MindMapNodeConfig
    from windows.text_renderer import TextRenderer

logger = logging.getLogger(__name__)


class MindMapTextAdapter:
    """MindMapNodeConfig を TextRenderer 用のインターフェースに変換するアダプタ。

    TextRenderer.render() は window オブジェクトの属性を直接参照するため、
    このアダプタが MindMapNodeConfig の値を提供する。

    Attributes:
        config: MindMapNodeConfig インスタンス。
        canvas_size: レンダリング結果のキャンバスサイズ（TextRenderer が設定）。
    """

    def __init__(self, config: "MindMapNodeConfig") -> None:
        """MindMapTextAdapter を初期化する。

        Args:
            config: MindMapNodeConfig インスタンス。
        """
        self._config = config
        self._canvas_size: QSize = QSize(100, 50)
        self._position: QPoint = QPoint(0, 0)

    # ============================================
    # Config Proxy Properties
    # ============================================

    @property
    def config(self) -> "MindMapNodeConfig":
        """設定オブジェクト。"""
        return self._config

    @property
    def text(self) -> str:
        return self._config.text

    @property
    def font_family(self) -> str:
        return self._config.font_family

    @property
    def font_size(self) -> int:
        return self._config.font_size

    @property
    def font_color(self) -> str:
        return self._config.font_color

    @property
    def background_color(self) -> str:
        return self._config.background_color

    @property
    def text_visible(self) -> bool:
        return self._config.text_visible

    @property
    def background_visible(self) -> bool:
        return self._config.background_visible

    @property
    def text_opacity(self) -> int:
        return self._config.text_opacity

    @property
    def background_opacity(self) -> int:
        return self._config.background_opacity

    # ============================================
    # Shadow Properties
    # ============================================

    @property
    def shadow_enabled(self) -> bool:
        return self._config.shadow_enabled

    @property
    def shadow_color(self) -> str:
        return self._config.shadow_color

    @property
    def shadow_opacity(self) -> int:
        return self._config.shadow_opacity

    @property
    def shadow_blur(self) -> int:
        return self._config.shadow_blur

    @property
    def shadow_scale(self) -> float:
        return self._config.shadow_scale

    @property
    def shadow_offset_x(self) -> float:
        return self._config.shadow_offset_x

    @property
    def shadow_offset_y(self) -> float:
        return self._config.shadow_offset_y

    # ============================================
    # Vertical / Offset
    # ============================================

    @property
    def is_vertical(self) -> bool:
        return self._config.is_vertical

    @property
    def offset_mode(self) -> Any:
        return self._config.offset_mode

    # ============================================
    # Outline 1
    # ============================================

    @property
    def outline_enabled(self) -> bool:
        return self._config.outline_enabled

    @property
    def outline_color(self) -> str:
        return self._config.outline_color

    @property
    def outline_opacity(self) -> int:
        return self._config.outline_opacity

    @property
    def outline_width(self) -> float:
        return self._config.outline_width

    @property
    def outline_blur(self) -> int:
        return self._config.outline_blur

    # ============================================
    # Outline 2
    # ============================================

    @property
    def second_outline_enabled(self) -> bool:
        return self._config.second_outline_enabled

    @property
    def second_outline_color(self) -> str:
        return self._config.second_outline_color

    @property
    def second_outline_opacity(self) -> int:
        return self._config.second_outline_opacity

    @property
    def second_outline_width(self) -> float:
        return self._config.second_outline_width

    @property
    def second_outline_blur(self) -> int:
        return self._config.second_outline_blur

    # ============================================
    # Outline 3
    # ============================================

    @property
    def third_outline_enabled(self) -> bool:
        return self._config.third_outline_enabled

    @property
    def third_outline_color(self) -> str:
        return self._config.third_outline_color

    @property
    def third_outline_opacity(self) -> int:
        return self._config.third_outline_opacity

    @property
    def third_outline_width(self) -> float:
        return self._config.third_outline_width

    @property
    def third_outline_blur(self) -> int:
        return self._config.third_outline_blur

    # ============================================
    # Background Outline
    # ============================================

    @property
    def background_outline_enabled(self) -> bool:
        return self._config.background_outline_enabled

    @property
    def background_outline_color(self) -> str:
        return self._config.background_outline_color

    @property
    def background_outline_opacity(self) -> int:
        return self._config.background_outline_opacity

    @property
    def background_outline_width_ratio(self) -> float:
        return self._config.background_outline_width_ratio

    # ============================================
    # Gradient
    # ============================================

    @property
    def text_gradient_enabled(self) -> bool:
        return self._config.text_gradient_enabled

    @property
    def text_gradient(self) -> list:
        return self._config.text_gradient

    @property
    def text_gradient_angle(self) -> int:
        return self._config.text_gradient_angle

    @property
    def text_gradient_opacity(self) -> int:
        return self._config.text_gradient_opacity

    @property
    def background_gradient_enabled(self) -> bool:
        return self._config.background_gradient_enabled

    @property
    def background_gradient(self) -> list:
        return self._config.background_gradient

    @property
    def background_gradient_angle(self) -> int:
        return self._config.background_gradient_angle

    @property
    def background_gradient_opacity(self) -> int:
        return self._config.background_gradient_opacity

    # ============================================
    # Margin / Corner
    # ============================================

    @property
    def horizontal_margin_ratio(self) -> float:
        return self._config.horizontal_margin_ratio

    @property
    def vertical_margin_ratio(self) -> float:
        return self._config.vertical_margin_ratio

    @property
    def margin_top_ratio(self) -> float:
        return self._config.margin_top_ratio

    @property
    def margin_bottom_ratio(self) -> float:
        return self._config.margin_bottom_ratio

    @property
    def margin_left_ratio(self) -> float:
        return self._config.margin_left_ratio

    @property
    def margin_right_ratio(self) -> float:
        return self._config.margin_right_ratio

    @property
    def background_corner_ratio(self) -> float:
        return self._config.background_corner_ratio

    # ============================================
    # TextRenderer Required Methods / Properties
    # ============================================

    @property
    def canvas_size(self) -> QSize:
        """レンダリング結果のキャンバスサイズ。"""
        return self._canvas_size

    @canvas_size.setter
    def canvas_size(self, value: QSize) -> None:
        """TextRenderer がレンダリング後にサイズを設定する。"""
        self._canvas_size = value

    def pos(self) -> QPoint:
        """ウィンドウ位置（TextRenderer が setGeometry で使用）。"""
        return self._position

    def setGeometry(self, rect: QRect) -> None:
        """TextRenderer がレイアウト更新時に呼び出す（MindMapNode では無視）。

        Args:
            rect: ジオメトリ矩形。
        """
        # QGraphicsItem の位置は別途管理するため、ここでは何もしない
        self._canvas_size = rect.size()


def render_node_text(
    renderer: "TextRenderer",
    config: "MindMapNodeConfig",
) -> QPixmap:
    """MindMapNodeConfig を使用してテキストをレンダリングする。

    Args:
        renderer: TextRenderer インスタンス。
        config: MindMapNodeConfig インスタンス。

    Returns:
        レンダリングされた QPixmap。
    """
    adapter = MindMapTextAdapter(config)
    return renderer.render(adapter)
