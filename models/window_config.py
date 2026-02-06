# models/window_config.py

from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .enums import AnchorPosition


class WindowConfigBase(BaseModel):
    """すべてのウィンドウに共通の設定"""

    # 代入時のバリデーションを有効化し、Enumへの変換を自動化
    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    uuid: str = ""
    parent_uuid: Optional[str] = None

    # 座標
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})
    is_frontmost: bool = True
    is_hidden: bool = False
    is_click_through: bool = False
    # --- 追加：ロック（移動/変形の誤操作防止）---
    is_locked: bool = False

    # アニメーション共通
    move_loop_enabled: bool = False
    move_position_only_enabled: bool = False
    move_speed: int = 1000
    move_pause_time: int = 0
    start_position: Optional[Dict[str, int]] = None
    end_position: Optional[Dict[str, int]] = None

    # --- 追加：相対移動アニメ（プリセット向け）---
    move_use_relative: bool = False
    move_offset: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})

    # --- 追加：イージング（保存/復元用）---
    # QEasingCurve.Type をそのままJSON化すると壊れやすいので、名称を保存する
    move_easing: str = "Linear"
    fade_easing: str = "Linear"

    # Anchorの設定
    anchor_position: AnchorPosition = AnchorPosition.AUTO

    # Fade
    is_fading_enabled: bool = False
    fade_in_only_loop_enabled: bool = False
    fade_out_only_loop_enabled: bool = False
    fade_speed: int = 1000
    fade_pause_time: int = 0


class TextWindowConfig(WindowConfigBase):
    """TextWindow用の設定モデル"""

    text: str = "New Text"
    font: str = "Arial"
    font_size: int = 48

    # 色情報
    font_color: str = "#ffffff"
    background_color: str = "#000000"

    text_visible: bool = True
    background_visible: bool = True

    # 透明度 (0-100)
    text_opacity: int = 100
    background_opacity: int = 100

    # 影
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_opacity: int = 100
    shadow_blur: int = 0
    shadow_scale: float = 1.0
    shadow_offset_x: float = 0.1
    shadow_offset_y: float = 0.1

    # 縦書き・オフセット
    is_vertical: bool = False

    # 縁取り 1
    outline_enabled: bool = False
    outline_color: str = "#000000"
    outline_opacity: int = 100
    outline_width: float = 5.0
    outline_blur: int = 0

    # 縁取り 2
    second_outline_enabled: bool = False
    second_outline_color: str = "#ffffff"
    second_outline_opacity: int = 100
    second_outline_width: float = 10.0
    second_outline_blur: int = 0

    # 縁取り 3
    third_outline_enabled: bool = False
    third_outline_color: str = "#000000"
    third_outline_opacity: int = 100
    third_outline_width: float = 15.0
    third_outline_blur: int = 0

    # 背景枠線
    background_outline_enabled: bool = False
    background_outline_color: str = "#000000"
    background_outline_opacity: int = 100
    background_outline_width_ratio: float = 0.05

    # グラデーション
    text_gradient_enabled: bool = False
    text_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#000000"), (1.0, "#FFFFFF")])
    text_gradient_angle: int = 0
    text_gradient_opacity: int = 100

    background_gradient_enabled: bool = False
    background_gradient: List[Tuple[float, str]] = Field(default_factory=lambda: [(0.0, "#000000"), (1.0, "#FFFFFF")])
    background_gradient_angle: int = 0
    background_gradient_opacity: int = 100

    # マージン（比率） - 後方互換性のため維持
    horizontal_margin_ratio: float = 0.0
    vertical_margin_ratio: float = 0.0  # 行間 (Was 0.2)

    # --- Spacing Split (Vertical/Horizontal De-coupling) ---
    # 横書き用
    char_spacing_h: float = 0.0
    line_spacing_h: float = 0.0
    # 縦書き用
    char_spacing_v: float = 0.0
    line_spacing_v: float = 0.0

    # ウィンドウ内余白（比率）
    margin_top: float = 0.0
    margin_bottom: float = 0.0
    margin_left: float = 0.0
    margin_right: float = 0.0
    background_corner_ratio: float = 0.2

    # 縦書きモード専用マージン（Noneの場合は横書き設定を流用）
    v_margin_top: Optional[float] = 0.0
    v_margin_bottom: Optional[float] = 0.0
    v_margin_left: Optional[float] = 0.0
    v_margin_right: Optional[float] = 0.0


class ImageWindowConfig(WindowConfigBase):
    """ImageWindow用の設定モデル"""

    image_path: str = ""

    geometry: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0, "width": 100, "height": 100})

    scale_factor: float = 1.0
    opacity: float = 1.0
    rotation_angle: float = 0.0

    flip_horizontal: bool = False
    flip_vertical: bool = False

    # 追加
    is_locked: bool = False

    animation_speed_factor: float = 1.0
