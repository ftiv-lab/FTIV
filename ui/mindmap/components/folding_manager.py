import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.mindmap.mindmap_node import MindMapNode

logger = logging.getLogger(__name__)


class FoldingManager:
    """MindMapNode の折りたたみ（Folding）ロジックを管理するクラス。

    ノードの展開・折りたたみ状態と、子孫ノードの可視性制御（再帰的更新）を担当する。
    """

    def __init__(self, node: "MindMapNode"):
        """初期化。

        Args:
            node: 管理対象のMindMapNode。
        """
        self.node = node

    def toggle_fold(self) -> None:
        """折りたたみ状態を切り替える。"""
        current_state = self.is_expanded()
        new_state = not current_state

        self.set_expanded(new_state)

        # 可視性の再帰更新
        self.update_children_visibility(self.node, new_state)

        # 再描画 (ボタンの +/- 表示更新のため)
        self.node.update()

        logger.debug(f"Node {self.node.uuid[:8]} folded: {not new_state}")

    def is_expanded(self) -> bool:
        """展開状態を取得する。"""
        # NodeのConfigまたは内部状態を参照
        if self.node.config:
            return self.node.config.is_expanded
        return getattr(self.node, "_is_expanded", True)

    def set_expanded(self, expanded: bool) -> None:
        """展開状態を設定する。"""
        if self.node.config:
            self.node.config.is_expanded = expanded
        self.node._is_expanded = expanded

    def update_children_visibility(self, node: "MindMapNode", visible: bool) -> None:
        """再帰的に子ノードとエッジの表示状態を更新する。

        Args:
            node: 更新起点となるノード
            visible: このノードの子供を表示すべきかどうか
        """
        for child in node.get_child_nodes():
            # 子が表示される条件:
            # 1. 親(visible引数) が True であること
            # 2. (再帰時) その親自身が展開されていること -> これは再帰呼び出し側で制御

            # ここでは単純に visible を適用し、
            # さらに child が展開済みなら孫を表示、そうでなければ孫を非表示にする

            # child自体の可視性設定
            child.setVisible(visible)

            # エッジの更新
            for edge in child.edges:
                edge.update_visibility()

            # 再帰呼び出し: 孫以降の制御
            if visible:
                # 子が表示されている場合のみ、その子の展開設定を確認
                # child.folding_manager を経由するのが理想だが、
                # 直接属性アクセスして高速化しても良い。ここでは安全に Manager 経由を想定したいが、
                # まだリファクタリング途中なので Config/Attribute 直接参照も考慮。

                child_expanded = True
                if hasattr(child, "folding_manager"):
                    child_expanded = child.folding_manager.is_expanded()
                elif child.config:
                    child_expanded = child.config.is_expanded
                else:
                    child_expanded = getattr(child, "_is_expanded", True)

                # 自分が表示されており、かつ自分が展開されているなら、子供（孫）を表示する
                self.update_children_visibility(child, child_expanded)
            else:
                # 自分が非表示なら、子供（孫）も強制的に非表示
                self.update_children_visibility(child, False)
