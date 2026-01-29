from ui.mindmap.mindmap_node import MindMapNode
from ui.mindmap.utils.markdown_exporter import MarkdownExporter
from ui.mindmap.utils.markdown_importer import MarkdownImporter


def test_import_header_structure():
    """Import headers (#) structure."""
    md = """
# Root
## Child 1
### Grandchild 1
## Child 2
"""
    importer = MarkdownImporter()
    nodes = importer.parse_markdown(md)

    assert len(nodes) == 1
    root = nodes[0]
    assert root["text"] == "Root"
    assert len(root["children"]) == 2

    child1 = root["children"][0]
    assert child1["text"] == "Child 1"
    assert len(child1["children"]) == 1
    assert child1["children"][0]["text"] == "Grandchild 1"


def test_import_bullet_structure():
    """Import bullet points (-) structure."""
    md = """
- Root
    - Child 1
        - Grandchild 1
    - Child 2
"""
    importer = MarkdownImporter()
    nodes = importer.parse_markdown(md)

    assert len(nodes) == 1
    root = nodes[0]
    assert root["text"] == "Root"
    assert len(root["children"]) == 2


def test_export_structure(qapp):
    """Export node structure to Markdown."""
    # Build tree
    root = MindMapNode("Root")
    child1 = MindMapNode("Child 1")
    child2 = MindMapNode("Child 2")

    # Mock edges/relationships normally handled by widget/canvas
    # Here we mock get_child_nodes logic by creating edges manually or mocking
    # Since MindMapNode uses edges to find children, we need edges.
    from ui.mindmap.mindmap_edge import MindMapEdge

    edge1 = MindMapEdge(root, child1)
    root.add_edge(edge1)
    child1.add_edge(edge1)

    edge2 = MindMapEdge(root, child2)
    root.add_edge(edge2)
    child2.add_edge(edge2)

    # Sort order depends on Y position
    root.setPos(0, 0)
    child1.setPos(100, 0)
    child2.setPos(100, 100)

    exporter = MarkdownExporter()
    md = exporter.export_node(root)

    expected = """- Root
    - Child 1
    - Child 2"""

    assert md.strip() == expected


# ==========================================
# TDD: A - フィードバック追加のテスト
# ==========================================


def test_parse_markdown_with_stats_returns_statistics():
    """parse_markdown_with_stats がパース統計を返すことを確認。"""
    md = """
# Root
## Child 1
## Child 2
"""
    importer = MarkdownImporter()
    result = importer.parse_markdown_with_stats(md)

    # 結果は (nodes, stats) のタプル
    assert "nodes" in result
    assert "stats" in result

    stats = result["stats"]
    assert stats["total_lines"] == 3  # 空行除く
    assert stats["parsed_lines"] == 3  # #で始まる3行
    assert stats["skipped_lines"] == 0  # 無視された行
    assert stats["node_count"] == 3  # 作成されたノード数


def test_parse_markdown_with_stats_empty_input():
    """空のテキストの場合のパース統計。"""
    importer = MarkdownImporter()
    result = importer.parse_markdown_with_stats("")

    assert result["nodes"] == []
    assert result["stats"]["total_lines"] == 0
    assert result["stats"]["parsed_lines"] == 0
    assert result["stats"]["node_count"] == 0


# ==========================================
# TDD: B - 寛容なパースのテスト
# ==========================================


def test_import_numbered_list():
    """番号付きリスト (1., 2.) をパースできることを確認。"""
    md = """
1. First item
2. Second item
   1. Nested first
   2. Nested second
3. Third item
"""
    importer = MarkdownImporter()
    nodes = importer.parse_markdown(md)

    assert len(nodes) == 3
    assert nodes[0]["text"] == "First item"
    assert nodes[1]["text"] == "Second item"
    assert len(nodes[1]["children"]) == 2
    assert nodes[1]["children"][0]["text"] == "Nested first"


def test_import_plain_text_with_indent():
    """インデントのみのプレーンテキストをパースできることを確認。"""
    md = """
Root Node
    Child Node 1
        Grandchild
    Child Node 2
"""
    importer = MarkdownImporter()
    nodes = importer.parse_markdown(md)

    assert len(nodes) == 1
    root = nodes[0]
    assert root["text"] == "Root Node"
    assert len(root["children"]) == 2
    assert root["children"][0]["text"] == "Child Node 1"
    assert len(root["children"][0]["children"]) == 1


def test_import_mixed_formats():
    """混合フォーマット（ヘッダー + ブレット + 番号 + プレーンテキスト）。"""
    md = """
# Main Topic
- Point A
- Point B
    1. Sub point 1
    2. Sub point 2
"""
    importer = MarkdownImporter()
    nodes = importer.parse_markdown(md)

    assert len(nodes) == 1
    root = nodes[0]
    assert root["text"] == "Main Topic"
    assert len(root["children"]) == 2  # Point A, Point B
    assert root["children"][1]["text"] == "Point B"
    assert len(root["children"][1]["children"]) == 2  # Sub points
