# models/default_node_style.py
"""
新規ノードに適用されるデフォルトスタイル設定。

MindMapNodeConfig のサブセットで、新規ノード作成時に適用される
スタイル値を保持する。
"""

from typing import TYPE_CHECKING, List, Tuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from models.mindmap_node_config import MindMapNodeConfig


class DefaultNodeStyle(BaseModel):
    """新規ノードに適用されるデフォルトスタイル設定"""

    model_config = ConfigDict(validate_assignment=True)

    # ============================================
    # フォント
    # ============================================
    font_family: str = "Segoe UI"
    font_size: int = 14

    # ============================================
    # 色
    # ============================================
    font_color: str = "#ffffff"
    background_color: str = "#3c3c5c"
    border_color: str = "#5c5c8c"

    # ============================================
    # 透明度
    # ============================================
    text_opacity: int = 100
    background_opacity: int = 100

    # ============================================
    # 影
    # ============================================
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_opacity: int = 100
    shadow_blur: int = 0
    shadow_offset_x: float = 0.1
    shadow_offset_y: float = 0.1

    # ============================================
    # 縁取り (1)
    # ============================================
    outline_enabled: bool = False
    outline_color: str = "#000000"
    outline_opacity: int = 100
    outline_width: float = 3.0
    outline_blur: int = 0

    # ============================================
    # グラデーション
    # ============================================
    text_gradient_enabled: bool = False
    text_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#ffffff"), (1.0, "#6c9fff")])
    text_gradient_angle: int = 0

    background_gradient_enabled: bool = False
    background_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#3c3c5c"), (1.0, "#5c5c8c")])
    background_gradient_angle: int = 0

    # ============================================
    # マージン・角丸
    # ============================================
    background_corner_ratio: float = 0.3

    def to_dict(self) -> dict:
        """辞書形式にエクスポートする。"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "DefaultNodeStyle":
        """辞書形式からインスタンスを生成する。"""
        return cls.model_validate(data)

    def apply_to_config(self, config: "MindMapNodeConfig") -> None:
        """DefaultNodeStyle の値を MindMapNodeConfig に適用する。

        Args:
            config: 適用先の設定オブジェクト。

        Note:
            既存の手動コピー処理と同等の動作。
            新規コードでの利用を推奨。
        """
        config.font_family = self.font_family
        config.font_size = self.font_size
        config.font_color = self.font_color
        config.background_color = self.background_color
        config.text_opacity = self.text_opacity
        config.background_opacity = self.background_opacity
        config.shadow_enabled = self.shadow_enabled
        config.shadow_color = self.shadow_color
        config.shadow_opacity = self.shadow_opacity
        config.shadow_blur = self.shadow_blur
        config.shadow_offset_x = self.shadow_offset_x
        config.shadow_offset_y = self.shadow_offset_y
        config.outline_enabled = self.outline_enabled
        config.outline_color = self.outline_color
        config.outline_opacity = self.outline_opacity
        config.outline_width = self.outline_width
        config.outline_blur = self.outline_blur
        config.text_gradient_enabled = self.text_gradient_enabled
        config.text_gradient = self.text_gradient
        config.text_gradient_angle = self.text_gradient_angle
        config.background_gradient_enabled = self.background_gradient_enabled
        config.background_gradient = self.background_gradient
        config.background_gradient_angle = self.background_gradient_angle
        config.background_corner_ratio = self.background_corner_ratio

    def copy_from_config(self, config: "MindMapNodeConfig") -> None:
        """MindMapNodeConfig の値を DefaultNodeStyle にコピーする。

        Args:
            config: コピー元の設定オブジェクト。
        """
        self.font_family = config.font_family
        self.font_size = config.font_size
        self.font_color = config.font_color
        self.background_color = config.background_color
        self.text_opacity = config.text_opacity
        self.background_opacity = config.background_opacity
        self.shadow_enabled = config.shadow_enabled
        self.shadow_color = config.shadow_color
        self.shadow_opacity = config.shadow_opacity
        self.shadow_blur = config.shadow_blur
        self.shadow_offset_x = config.shadow_offset_x
        self.shadow_offset_y = config.shadow_offset_y
        self.outline_enabled = config.outline_enabled
        self.outline_color = config.outline_color
        self.outline_opacity = config.outline_opacity
        self.outline_width = config.outline_width
        self.outline_blur = config.outline_blur
        self.text_gradient_enabled = config.text_gradient_enabled
        self.text_gradient = config.text_gradient
        self.text_gradient_angle = config.text_gradient_angle
        self.background_gradient_enabled = config.background_gradient_enabled
        self.background_gradient = config.background_gradient
        self.background_gradient_angle = config.background_gradient_angle
        self.background_corner_ratio = config.background_corner_ratio
