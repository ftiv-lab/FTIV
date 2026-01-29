from ui.mindmap.layouts.logical_strategy import LogicalStrategy


class RightLogicalStrategy(LogicalStrategy):
    """右方向へのロジカルツリー。

    LogicalStrategy(1) のエイリアス。
    """

    def __init__(self):
        super().__init__(direction=1)
