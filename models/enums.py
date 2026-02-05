# models/enums.py

from enum import Enum


class AnchorPosition(str, Enum):
    """接続線のアンカー位置"""

    AUTO = "auto"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class ArrowStyle(str, Enum):
    """接続線の矢印スタイル"""

    NONE = "none"
    START = "start"
    END = "end"
    BOTH = "both"
