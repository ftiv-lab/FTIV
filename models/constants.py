# models/constants.py


class AppDefaults:
    """システム全体のハードコード値を管理する定数クラス。"""

    # --- Performance / Rendering ---
    RENDER_DEBOUNCE_MS: int = 50
    WHEEL_DEBOUNCE_MS: int = 80
    GLYPH_CACHE_SIZE: int = 512
    RENDER_CACHE_SIZE: int = 32
    BLUR_CACHE_SIZE: int = 32

    # --- Connector ---
    CONNECTOR_WIDTH: int = 4
    CONNECTOR_ARROW_SIZE: int = 15
    CONNECTOR_FONT_SIZE: float = 14.0
    CONNECTOR_COLOR_ALPHA: int = 180  # Default alpha for connector lines

    # --- UI Standard ---
    # Dialogs
    DIALOG_MIN_WIDTH: int = 300
