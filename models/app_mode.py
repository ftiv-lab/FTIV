# models/app_mode.py
"""
アプリケーションモードの定義。

FTIVはデスクトップモードとマインドマップモードの2つのモードを持つ。
"""

from enum import Enum, auto


class AppMode(Enum):
    """アプリケーションの表示モード。"""

    DESKTOP = auto()
    """デスクトップオーバーレイモード。画面上に自由配置。"""

    MIND_MAP = auto()
    """マインドマップモード。専用キャンバス上でノードを配置。"""
