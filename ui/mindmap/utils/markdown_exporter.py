from typing import List

if False:
    from ui.mindmap.mindmap_node import MindMapNode


class MarkdownExporter:
    """マインドマップをMarkdownテキストに変換する。"""

    def export_node(self, node: "MindMapNode") -> str:
        """ノード（とその子孫）をMarkdownテキストに変換する。

        Args:
            node: ルートとなるノード

        Returns:
            str: 生成されたMarkdownテキスト
        """
        lines = []
        self._recursive_export(node, 0, lines)
        return "\n".join(lines)

    def _recursive_export(self, node: "MindMapNode", level: int, lines: List[str]):
        """再帰的にMarkdown行を生成する。"""
        # ルートノード(level=0)はヘッダー(#)にするか、リスト(-)にするか？
        # 一般的なアウトライナーとの互換性のため、全てリスト形式(-)で出力する。
        # ただし、クリップボード貼り付け時の利便性を考え、ルートだけはそのまま出すという手もあるが
        # ここではインデントベースのリスト形式に統一する。

        indent = "    " * level

        # テキスト内の改行を除去・置換
        clean_text = node.text.replace("\n", " ")

        # アイコンがあれば付与
        prefix = ""
        if node.config and node.config.icon:
            prefix = f"{node.config.icon} "

        line = f"{indent}- {prefix}{clean_text}"

        # Configにあるメモがあれば、次の行に引用形式で追加するオプションもあり
        # if node.config and node.config.memo:
        #     memo_indent = indent + "    "
        #     line += f"\n{memo_indent}> {node.config.memo}"

        lines.append(line)

        # 子ノード処理 (位置順にソートして出力するのが望ましいが、get_child_nodesの順序依存)
        # Y座標順にソートすることで視覚的な順序と合わせる
        children = sorted(node.get_child_nodes(), key=lambda n: n.scenePos().y())

        for child in children:
            self._recursive_export(child, level + 1, lines)
