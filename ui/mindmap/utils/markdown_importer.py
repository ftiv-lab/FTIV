import re
from typing import Dict, List, Tuple, TypedDict


class ParseStats(TypedDict):
    """パース統計情報。"""

    total_lines: int
    parsed_lines: int
    skipped_lines: int
    node_count: int


class ParseResult(TypedDict):
    """パース結果（ノードと統計情報）。"""

    nodes: List[Dict]
    stats: ParseStats


class MarkdownImporter:
    """Markdownテキストを解析し、マインドマップノード構造に変換する。"""

    def parse_markdown(self, text: str) -> List[Dict]:
        """Markdownテキストをパースし、NodeConfigの辞書リスト（階層構造）を返す。

        Supported formats:
        - Headers (#, ##, ###)
        - Bullet points (-, *, +)
        - Numbered lists (1., 2., 3.)
        - Plain text with indentation

        Returns:
            List[Dict]: ルートノードのリスト（再帰的構造）
        """
        result = self.parse_markdown_with_stats(text)
        return result["nodes"]

    def parse_markdown_with_stats(self, text: str) -> ParseResult:
        """Markdownテキストをパースし、ノードと統計情報を返す。

        Returns:
            ParseResult: ノードリストとパース統計
        """
        lines = text.split("\n")
        root_nodes: List[Dict] = []
        stack: List[Tuple[int, Dict, str]] = []  # (level, node_dict, line_type)

        stats: ParseStats = {
            "total_lines": 0,
            "parsed_lines": 0,
            "skipped_lines": 0,
            "node_count": 0,
        }

        last_header_level = -1  # 最後に見たヘッダーのレベル

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            stats["total_lines"] += 1

            level, content, line_type = self._parse_line_extended(line)

            if level == -1:
                stats["skipped_lines"] += 1
                continue

            stats["parsed_lines"] += 1

            # ヘッダーの場合、レベルを更新
            if line_type == "header":
                last_header_level = level
            elif last_header_level >= 0:
                # 非ヘッダーがヘッダーの後に来た場合、ヘッダーの子として扱う
                # 実質レベルを調整: header_level + 1 + 現在のインデントレベル
                level = last_header_level + 1 + level

            # ノード生成
            node_data: Dict = {
                "text": content,
                "children": [],
                "is_expanded": True,
            }
            stats["node_count"] += 1

            # スタック操作: 自分より深いか同じレベルのものをpopし、親を見つける
            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                # ルートレベル
                root_nodes.append(node_data)
            else:
                # 親の子に追加
                parent = stack[-1][1]
                parent["children"].append(node_data)

            stack.append((level, node_data, line_type))

        return {"nodes": root_nodes, "stats": stats}

    def _parse_line_extended(self, line: str) -> Tuple[int, str, str]:
        """行のインデントレベル、内容、タイプを解析する。

        Returns:
            (level, content, line_type): levelは深さ(0オリジン)。
            line_type は "header", "bullet", "numbered", "plain" のいずれか。
            解析不可なら (-1, "", "unknown")。
        """
        # Tab = 4 spaces
        expanded_line = line.replace("\t", "    ")

        # 1. Header (#) check
        header_match = re.match(r"^(#+)\s+(.*)", line)
        if header_match:
            level = len(header_match.group(1)) - 1
            content = header_match.group(2).strip()
            return level, content, "header"

        # 2. Bullet point check (-, *, +)
        bullet_match = re.match(r"^(\s*)([-*+])\s+(.*)", expanded_line)
        if bullet_match:
            indent_len = len(bullet_match.group(1))
            level = indent_len // 4  # 4 spaces = 1 indent level
            content = bullet_match.group(3).strip()
            return level, content, "bullet"

        # 3. Numbered list check (1., 2., etc.)
        numbered_match = re.match(r"^(\s*)(\d+)\.\s+(.*)", expanded_line)
        if numbered_match:
            indent_len = len(numbered_match.group(1))
            level = indent_len // 3  # 3 spaces = 1 indent level for numbered
            content = numbered_match.group(3).strip()
            return level, content, "numbered"

        # 4. Plain text with indentation
        plain_match = re.match(r"^(\s*)(\S.*)", expanded_line)
        if plain_match:
            indent_len = len(plain_match.group(1))
            level = indent_len // 4  # 4 spaces = 1 indent level
            content = plain_match.group(2).strip()
            return level, content, "plain"

        return -1, "", "unknown"

    def _parse_line(self, line: str) -> Tuple[int, str]:
        """後方互換性のための旧メソッド。"""
        level, content, _ = self._parse_line_extended(line)
        return level, content
