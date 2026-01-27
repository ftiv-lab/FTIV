import logging
from typing import TYPE_CHECKING, Literal, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QGuiApplication

from ui.mindmap.layout_manager import LayoutManager
from ui.mindmap.mindmap_edge import MindMapEdge
from ui.mindmap.mindmap_node import MindMapNode
from ui.mindmap.styles.edge_routers import BezierRouter, OrthogonalRouter
from utils.translator import tr

if TYPE_CHECKING:
    from ui.mindmap.mindmap_widget import MindMapWidget

logger = logging.getLogger(__name__)


class MindMapController:
    """マインドマップのビジネスロジックを管理するコントローラー。

    MindMapCanvas および MindMapWidget からロジックを分離し、
    操作（追加、削除、編集）を集約する。
    """

    def __init__(self, widget: "MindMapWidget") -> None:
        """初期化。

        Args:
            widget: 親となる MindMapWidget インスタンス。
        """
        self.widget = widget
        self.canvas = widget.canvas
        self.layout_manager = LayoutManager()
        self.layout_mode: Literal["auto", "manual"] = "manual"  # デフォルトはManualモード
        # シーンはプロパティ経由で取得したほうが安全（Canvas再生成の可能性は低いが）

    @property
    def scene(self):
        return self.canvas.scene()

    def add_node(self, text: str = "New Node", position: Optional[QPointF] = None) -> MindMapNode:
        """ノードを追加する。"""
        if position is None:
            position = self.canvas.get_scene_pos_at_center()

        node = MindMapNode(text=text, position=position)

        # デフォルトスタイルを適用
        if self.widget.mw and hasattr(self.widget.mw, "default_node_style") and node.config:
            self.widget.mw.default_node_style.apply_to_config(node.config)

        # Signal 接続 (Widget側のハンドラを利用)
        if hasattr(self.widget, "_handle_set_as_default"):
            node.sig_request_set_as_default.connect(self.widget._handle_set_as_default)

        self.scene.addItem(node)

        logger.info(f"Node added: '{text}' at ({position.x():.0f}, {position.y():.0f})")
        return node

    def add_child_node(self, parent_node: Optional[MindMapNode] = None) -> Optional[MindMapNode]:
        """指定した親ノードに子ノードを追加する。"""
        if parent_node is None:
            items = self.scene.selectedItems()
            nodes = [i for i in items if isinstance(i, MindMapNode)]
            if not nodes:
                return None
            parent_node = nodes[0]

        # 初期配置計算 (LayoutManager)
        new_pos = self.layout_manager.calculate_child_position(parent_node)

        # ノード作成
        new_node = MindMapNode(tr("mm_new_node"), position=new_pos)
        self.scene.addItem(new_node)

        # エッジ作成
        edge = MindMapEdge(parent_node, new_node)
        # 現在のレイアウトに合わせたルーターを設定
        edge.set_router(self._create_current_router())
        self.scene.addItem(edge)

        # 選択切り替え
        self.scene.clearSelection()
        new_node.setSelected(True)

        # 自動レイアウト適用 (Autoモード時のみ)
        if self.layout_mode == "auto":
            root = self._find_root(new_node)
            self.layout_manager.arrange_tree(root, animate=True)

        # シグナル発行
        self.canvas.sig_node_added.emit(new_node)

        logger.info(f"Child node added. Parent: {parent_node.text}")
        return new_node

    def add_sibling_node(self, node: Optional[MindMapNode] = None) -> Optional[MindMapNode]:
        """指定したノードの兄弟（同じ親を持つ）ノードを追加する。"""
        if node is None:
            items = self.scene.selectedItems()
            nodes = [i for i in items if isinstance(i, MindMapNode)]
            if not nodes:
                return None
            node = nodes[0]

        # 親を探す
        parent_node = None
        for edge in node.edges:
            if edge.target_node == node:
                parent_node = edge.source_node
                break

        if parent_node:
            return self.add_child_node(parent_node)
        else:
            # ルートの兄弟（＝別のルート）
            new_pos = self.layout_manager.calculate_root_sibling_position(node)
            new_node = MindMapNode(tr("mm_new_root"), position=new_pos)
            self.scene.addItem(new_node)

            self.scene.clearSelection()
            new_node.setSelected(True)
            self.canvas.sig_node_added.emit(new_node)

            logger.info("Sibling (Root) node added.")
            return new_node

    def delete_selected_items(self) -> None:
        """選択中のノード・エッジを削除する。"""
        items = self.scene.selectedItems()
        if not items:
            return

        nodes_to_delete = []
        edges_to_delete = []

        for item in items:
            if isinstance(item, MindMapNode):
                nodes_to_delete.append(item)
            elif isinstance(item, MindMapEdge):
                edges_to_delete.append(item)

        # 影響を受けるルートノードを特定（削除前に）
        roots_to_update = set()
        for node in nodes_to_delete:
            parent = self._find_parent(node)
            if parent and parent not in nodes_to_delete:
                root = self._find_root(parent)
                roots_to_update.add(root)

        # 削除対象ノードに接続しているエッジも全て削除リストへ
        for node in nodes_to_delete:
            for edge in list(node.edges):
                if edge not in edges_to_delete:
                    edges_to_delete.append(edge)

        # 削除実行
        count_edges = len(edges_to_delete)
        count_nodes = len(nodes_to_delete)

        for edge in edges_to_delete:
            edge.remove()

        for node in nodes_to_delete:
            if node.scene() == self.scene:
                self.scene.removeItem(node)

        # 自動レイアウト更新 (Autoモード時のみ)
        if self.layout_mode == "auto":
            for root in roots_to_update:
                if root.scene() == self.scene:
                    self.layout_manager.arrange_tree(root, animate=True)

        logger.info(f"Deleted {count_nodes} nodes and {count_edges} edges")

    def navigate(self, key: int) -> bool:
        """矢印キーによるノード移動。"""
        items = self.scene.selectedItems()
        nodes = [i for i in items if isinstance(i, MindMapNode)]
        if not nodes:
            return False

        current = nodes[0]
        target = None

        if key == Qt.Key.Key_Left:
            # 親へ
            target = self._find_parent(current)
        elif key == Qt.Key.Key_Right:
            # 子へ (Y座標が近いもの)
            children = current.get_child_nodes()
            if children:
                current_y = current.y()
                target = min(children, key=lambda c: abs(c.y() - current_y))
        elif key == Qt.Key.Key_Up or key == Qt.Key.Key_Down:
            # 兄弟へ
            parent = self._find_parent(current)
            candidates = []
            if parent:
                candidates = parent.get_child_nodes()
            else:
                # ルート兄弟
                candidates = [
                    i for i in self.scene.items() if isinstance(i, MindMapNode) and self._find_parent(i) is None
                ]

            if key == Qt.Key.Key_Up:
                filtered = [c for c in candidates if c.y() < current.y()]
                if filtered:
                    target = max(filtered, key=lambda c: c.y())
            else:
                filtered = [c for c in candidates if c.y() > current.y()]
                if filtered:
                    target = min(filtered, key=lambda c: c.y())

        if target:
            self.scene.clearSelection()
            target.setSelected(True)
            target.ensureVisible()
            return True

        return False

    def auto_layout_all(self, animate: bool = True) -> None:
        """全てのツリーを自動整列する。"""
        # 親を持たないノード＝ルートノードを探す
        roots = []
        for item in self.scene.items():
            if isinstance(item, MindMapNode) and self._find_parent(item) is None:
                roots.append(item)

        if not roots:
            logger.info("No root nodes found for auto-layout.")
            return

        for root in roots:
            self.layout_manager.arrange_tree(root, animate=animate)

        logger.info(f"Auto-layout applied to {len(roots)} trees.")

    def set_layout_strategy(self, strategy_type: str) -> None:
        """レイアウト戦略を変更し、適用する。"""
        from ui.mindmap.layouts.balanced_strategy import BalancedMapStrategy
        from ui.mindmap.layouts.org_chart_strategy import OrgChartStrategy
        from ui.mindmap.layouts.right_logical_strategy import RightLogicalStrategy

        strategy = None
        if strategy_type == "right_logical":
            strategy = RightLogicalStrategy()
        elif strategy_type == "balanced_map":
            strategy = BalancedMapStrategy()
        elif strategy_type == "org_chart":
            strategy = OrgChartStrategy()

        if strategy:
            self.layout_manager.set_strategy(strategy)

            # Update all edges to recommended router
            self._update_all_edges_style()

            self.auto_layout_all(animate=True)
            logger.info(f"Layout Switch: {strategy_type}")

    def set_layout_mode(self, mode: Literal["auto", "manual"]) -> None:
        """レイアウトモードを変更する。

        Args:
            mode: "auto" (自動レイアウト) または "manual" (手動配置)
        """
        self.layout_mode = mode
        logger.info(f"Layout mode changed to: {mode}")

        # Autoモードに切り替えた場合は即座にレイアウトを適用
        if mode == "auto":
            self.auto_layout_all(animate=True)

    def _update_all_edges_style(self) -> None:
        """全てのエッジのルーターを現在の戦略に合わせる。"""
        recommended = self.layout_manager.strategy.get_recommended_router_type()

        # エッジを収集
        edges = []
        for item in self.scene.items():
            if isinstance(item, MindMapEdge):
                edges.append(item)

        # 更新
        for edge in edges:
            # 同じタイプなら再計算のみ、違うなら差し替え
            # 簡易的に常に新しいルーターをセット
            if recommended == "Orthogonal":
                edge.set_router(OrthogonalRouter())
            else:
                edge.set_router(BezierRouter())

    def _create_current_router(self):
        """現在の戦略に合わせたルーターを生成する。"""
        recommended = self.layout_manager.strategy.get_recommended_router_type()
        if recommended == "Orthogonal":
            return OrthogonalRouter()
        else:
            return BezierRouter()

    def _find_root(self, node: MindMapNode) -> MindMapNode:
        """指定したノードが属するツリーのルートノードを探す。"""
        current = node
        visited = set()
        while True:
            if current in visited:
                break
            visited.add(current)

            parent = self._find_parent(current)
            if parent:
                current = parent
            else:
                break
        return current

    def _find_parent(self, node: MindMapNode) -> Optional[MindMapNode]:
        """親ノードを探す。"""
        for edge in node.edges:
            if edge.target_node == node:
                return edge.source_node
        return None

    def paste_nodes_from_markdown(self, text: str, target_parent: Optional[MindMapNode] = None) -> int:
        """Markdownテキストを解析し、ノードとして貼り付ける。

        Returns:
            int: 作成されたルートノード数
        """
        from ui.mindmap.utils.markdown_importer import MarkdownImporter

        importer = MarkdownImporter()
        root_dicts = importer.parse_markdown(text)

        if not root_dicts:
            return 0

        return self.paste_nodes_from_parsed_data(root_dicts, target_parent)

    def paste_nodes_from_parsed_data(
        self, root_dicts: list, target_parent: Optional[MindMapNode] = None
    ) -> int:
        """パース済みのノードデータからノードを作成する。

        Args:
            root_dicts: パース済みのノードデータリスト
            target_parent: 親ノード（None の場合はルートとして追加）

        Returns:
            int: 作成されたルートノード数
        """
        if not root_dicts:
            return 0

        # ターゲット位置計算
        if target_parent:
            base_pos = target_parent.scenePos()
        else:
            base_pos = self.canvas.get_scene_pos_at_center()

        # ルートノードが複数ある場合も考慮して追加
        created_nodes = []
        for i, root_data in enumerate(root_dicts):
            # 位置を少しずらす
            pos = base_pos + QPointF(20 * i, 50 * i)

            if target_parent:
                # 親がいる場合は子として追加
                node = self._create_subtree_recursive(root_data, target_parent)
            else:
                # 親がいない場合はルートとして追加
                node = self._create_subtree_recursive(root_data, None, pos)

            if node:
                created_nodes.append(node)

        if created_nodes:
            # Autoモード時のみ自動レイアウト
            if self.layout_mode == "auto":
                self.auto_layout_all(animate=True)
            logger.info(f"Pasted {len(created_nodes)} root nodes from Markdown")

        return len(created_nodes)

    def _create_subtree_recursive(
        self, data: dict, parent: Optional[MindMapNode] = None, position: Optional[QPointF] = None
    ) -> Optional[MindMapNode]:
        """再帰的にノードツリーを作成する。"""
        text = data.get("text", "Node")

        node = None
        if parent:
            # add_child_node は位置計算や選択状態変更を行うため、
            # ここでは直接 MindMapNode と Edge を生成したほうが高速かつ安全かもしれないが、
            # レイアウトの一貫性のために add_child_node (の手動版) を行う。

            # 位置計算 (LayoutManager)
            new_pos = self.layout_manager.calculate_child_position(parent)
            node = MindMapNode(text=text, position=new_pos)
            self.scene.addItem(node)

            if self.widget.mw and hasattr(self.widget.mw, "default_node_style"):
                self.widget.mw.default_node_style.apply_to_config(node.config)

            edge = MindMapEdge(parent, node)
            edge.set_router(self._create_current_router())
            self.scene.addItem(edge)

        else:
            # ルートノード
            node = MindMapNode(text=text, position=position)
            self.scene.addItem(node)
            if self.widget.mw and hasattr(self.widget.mw, "default_node_style"):
                self.widget.mw.default_node_style.apply_to_config(node.config)

        if not node:
            return None

        # 子ノードの作成
        children = data.get("children", [])
        for child_data in children:
            self._create_subtree_recursive(child_data, node)

        return node

    def copy_all_as_markdown(self) -> None:
        """マップ全体（または選択ツリー）をMarkdownとしてコピーする。"""
        from ui.mindmap.utils.markdown_exporter import MarkdownExporter

        items = self.scene.selectedItems()
        nodes = [i for i in items if isinstance(i, MindMapNode)]

        target_roots = []
        if nodes:
            # 選択されたノード（およびその子孫）を対象とする
            target_roots = nodes
        else:
            # 何も選択されていない場合は、シーン上の全てのルートノードを対象とする
            for item in self.scene.items():
                if isinstance(item, MindMapNode) and self._find_parent(item) is None:
                    target_roots.append(item)

        # Y座標順にソート (視覚的な順序を維持)
        target_roots.sort(key=lambda n: n.scenePos().y())

        exporter = MarkdownExporter()
        output_parts = []

        for root in target_roots:
            md = exporter.export_node(root)
            output_parts.append(md)

        final_text = "\n\n".join(output_parts)

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(final_text)

        logger.info("Copied map as Markdown to clipboard")
