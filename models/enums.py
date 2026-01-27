# models/enums.py

from enum import Enum


class AnchorPosition(str, Enum):
    """接続線のアンカー位置"""

    AUTO = "auto"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class OffsetMode(str, Enum):
    """縦書きの文字配置モード"""

    MONO = "A"  # 等幅フォント向け (Type A)
    PROP = "B"  # プロポーショナルフォント向け (Type B)


class ArrowStyle(str, Enum):
    """接続線の矢印スタイル"""

    NONE = "none"
    START = "start"
    END = "end"
    BOTH = "both"
