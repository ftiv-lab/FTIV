# models/window_layer.py
"""
ウィンドウのレイヤー（所属モード）の定義。

各ウィンドウは1つのレイヤーにのみ所属し、
そのレイヤーがアクティブなモードと一致する場合のみ表示される。
"""

from enum import Enum, auto


class WindowLayer(Enum):
    """ウィンドウが所属するレイヤー。"""

    DESKTOP = auto()
    """デスクトップモード専用。"""

    MIND_MAP = auto()
    """マインドマップモード専用。"""
