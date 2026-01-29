from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode


class LayoutStrategy(ABC):
    """レイアウト戦略の基底クラス (Interface)。

    特定のレイアウトアルゴリズム（例: ツリー型、バランス型、魚骨型）を実装する。
    Strategy Pattern の ConcreteStrategy に相当。
    """

    @abstractmethod
    def calculate_positions(self, root_node: "MindMapNode") -> None:
        """ルートノードを基点にノードの配置座標を計算し、一時プロパティに保存する。

        このメソッドはノードの座標を直接変更せず、
        `node._layout_target_pos` 等の属性に計算結果をセットすることを期待する。

        Args:
            root_node: レイアウト対象のルートノード。
        """
        pass

    @abstractmethod
    def calculate_child_position(self, parent_node: "MindMapNode") -> QPointF:
        """単一の子ノード追加時の初期位置を計算する。

        Args:
            parent_node: 親ノード。

        Returns:
            初期配置座標。
        """
        pass

    @abstractmethod
    def calculate_root_sibling_position(self, node: "MindMapNode") -> QPointF:
        """ルート兄弟ノード追加時の初期位置を計算する。

        Args:
            node: 既存のルートノード。

        Returns:
            新しいルートノードの座標。
        """
        pass

    def get_layout_name(self) -> str:
        """レイアウト戦略名を返す（UI表示用）。"""
        return "Unknown Layout"

    def get_recommended_router_type(self) -> str:
        """推奨するエッジルーターの種類を返す。"""
        return "Bezier"
