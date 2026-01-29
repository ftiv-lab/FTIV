# models/mindmap_node_config.py
"""
MindMapNode 用の設定モデル。

TextRenderer と互換性のあるプロパティを持ち、
ノードのテキストスタイリング（縁取り、影、グラデーション等）を保存・復元する。
"""

from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .enums import OffsetMode


class MindMapNodeConfig(BaseModel):
    """MindMapNode 用の設定モデル。

    TextWindowConfig の主要なスタイリングプロパティを継承し、
    TextRenderer との互換性を確保する。
    """

    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    # ============================================
    # 識別子
    # ============================================
    uuid: str = ""

    # ============================================
    # 基本テキスト設定
    # ============================================
    text: str = "New Node"
    font_family: str = "Segoe UI"
    font_size: int = 14

    # ============================================
    # 色設定
    # ============================================
    font_color: str = "#ffffff"
    background_color: str = "#3c3c5c"

    text_visible: bool = True
    background_visible: bool = True

    # 透明度 (0-100)
    text_opacity: int = 100
    background_opacity: int = 100

    # ============================================
    # 影
    # ============================================
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_opacity: int = 100
    shadow_blur: int = 0
    shadow_scale: float = 1.0
    shadow_offset_x: float = 0.1
    shadow_offset_y: float = 0.1

    # ============================================
    # 縦書き・オフセット
    # ============================================
    is_vertical: bool = False
    offset_mode: Optional[OffsetMode] = OffsetMode.PROP

    # ============================================
    # 縁取り 1
    # ============================================
    outline_enabled: bool = False
    outline_color: str = "#000000"
    outline_opacity: int = 100
    outline_width: float = 3.0
    outline_blur: int = 0

    # ============================================
    # 縁取り 2
    # ============================================
    second_outline_enabled: bool = False
    second_outline_color: str = "#ffffff"
    second_outline_opacity: int = 100
    second_outline_width: float = 6.0
    second_outline_blur: int = 0

    # ============================================
    # 縁取り 3
    # ============================================
    third_outline_enabled: bool = False
    third_outline_color: str = "#000000"
    third_outline_opacity: int = 100
    third_outline_width: float = 9.0
    third_outline_blur: int = 0

    # ============================================
    # 背景枠線
    # ============================================
    background_outline_enabled: bool = False
    background_outline_color: str = "#5c5c8c"
    background_outline_opacity: int = 100
    background_outline_width_ratio: float = 0.05

    # ============================================
    # 状態管理
    # ============================================
    is_expanded: bool = True

    # ============================================
    # グラデーション
    # ============================================
    text_gradient_enabled: bool = False
    text_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#ffffff"), (1.0, "#6c9fff")])
    text_gradient_angle: int = 0
    text_gradient_opacity: int = 100

    background_gradient_enabled: bool = False
    background_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#3c3c5c"), (1.0, "#5c5c8c")])
    background_gradient_angle: int = 0
    background_gradient_opacity: int = 100

    # ============================================
    # マージン・角丸（TextRenderer 互換）
    # ============================================
    horizontal_margin_ratio: float = 0.0
    vertical_margin_ratio: float = 0.2
    margin_top_ratio: float = 0.3
    margin_bottom_ratio: float = 0.3
    margin_left_ratio: float = 0.3
    margin_right_ratio: float = 0.3
    background_corner_ratio: float = 0.3

    # ============================================
    # 位置（保存用）
    # ============================================
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})

    # ============================================
    # ノード固有設定
    # ============================================
    border_color: str = "#5c5c8c"
    is_expanded: bool = True

    # ============================================
    # 注釈・コンテンツ
    # ============================================
    memo: str = ""
    hyperlink: str = ""
    icon: str = ""  # Emoji or Icon Name (e.g. "✅", "star")
    image_path: str = ""  # Path to embedded image

    def to_dict(self) -> dict:
        """辞書形式にエクスポートする。"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "MindMapNodeConfig":
        """辞書形式からインスタンスを生成する。"""
        return cls.model_validate(data)
