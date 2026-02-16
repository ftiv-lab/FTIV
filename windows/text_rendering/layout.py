def get_blur_radius_px(*, shadow_enabled: bool, shadow_blur: float) -> float:
    """ぼかし半径（ピクセル）を返す。"""
    if not shadow_enabled:
        return 0.0
    return float(shadow_blur) * 20.0 / 100.0


def calculate_shadow_padding(
    *,
    font_size: float,
    shadow_enabled: bool,
    shadow_offset_x: float,
    shadow_offset_y: float,
    shadow_blur: float,
) -> tuple[int, int, int, int]:
    """影とぼかしによる追加パディングを計算する。"""
    if not shadow_enabled:
        return 0, 0, 0, 0

    sx = float(font_size) * float(shadow_offset_x)
    sy = float(font_size) * float(shadow_offset_y)
    blur_px = get_blur_radius_px(shadow_enabled=shadow_enabled, shadow_blur=shadow_blur)

    pad_left = int(max(0, -(sx - blur_px)))
    pad_top = int(max(0, -(sy - blur_px)))
    pad_right = int(max(0, (sx + blur_px)))
    pad_bottom = int(max(0, (sy + blur_px)))
    return pad_left, pad_top, pad_right, pad_bottom
