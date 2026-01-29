import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from ui.mindmap.mindmap_edge import MindMapEdge
from ui.mindmap.mindmap_node import MindMapNode


@pytest.fixture
def folding_setup(qapp):
    """
    構造:
    Root
      |-- Child1
      |     |-- GrandChild1
      |
      |-- Child2
    """
    root = MindMapNode("Root")
    child1 = MindMapNode("Child1")
    grandchild1 = MindMapNode("GrandChild1")
    child2 = MindMapNode("Child2")

    # シーンに追加しないと itemChange とかが動かない可能性はあるが、
    # visibility は setVisible で制御されるので一旦単体でテスト

    # 接続 (Edge作成)
    MindMapEdge(root, child1)
    MindMapEdge(child1, grandchild1)
    MindMapEdge(root, child2)

    return root, child1, grandchild1, child2


def test_initial_state(folding_setup):
    root, child1, grandchild1, child2 = folding_setup

    assert root.config.is_expanded is True
    assert root.isVisible() is True
    assert child1.isVisible() is True
    assert grandchild1.isVisible() is True
    assert child2.isVisible() is True


def test_collapse_leaf_parent(folding_setup):
    """子ノード(Child1)を閉じる -> 孫(GrandChild1)が消える"""
    root, child1, grandchild1, child2 = folding_setup

    child1.toggle_fold()

    assert child1.config.is_expanded is False
    assert grandchild1.isVisible() is False
    # 自分自身と兄弟は消えない
    assert child1.isVisible() is True
    assert child2.isVisible() is True


def test_collapse_root(folding_setup):
    """ルートを閉じる -> 子と孫が全て消える"""
    root, child1, grandchild1, child2 = folding_setup

    root.toggle_fold()

    assert root.config.is_expanded is False
    assert child1.isVisible() is False
    assert child2.isVisible() is False
    assert grandchild1.isVisible() is False  # 再帰的に消える


def test_expand_root_restore_state(folding_setup):
    """
    状態復元のテスト:
    1. Child1 を閉じる (GrandChild1 非表示)
    2. Root を閉じる (Child1, GrandChild1 非表示)
    3. Root を開く -> Child1 は表示、GrandChild1 は非表示のまま維持されるべき
    """
    root, child1, grandchild1, child2 = folding_setup

    # 1. Child1 visible, GrandChild1 hidden
    child1.toggle_fold()
    assert child1.isVisible() is True
    assert grandchild1.isVisible() is False

    # 2. All children hidden
    root.toggle_fold()
    assert child1.isVisible() is False
    assert grandchild1.isVisible() is False

    # 3. Restore visibility
    root.toggle_fold()
    assert root.config.is_expanded is True

    # Child1 は親が開いたので見える
    assert child1.isVisible() is True

    # Child1 は閉じているので、GrandChild1 は見えないまま
    assert child1.config.is_expanded is False
    assert grandchild1.isVisible() is False


def test_has_children(folding_setup):
    root, child1, grandchild1, child2 = folding_setup

    assert root.has_children() is True
    assert child1.has_children() is True
    assert grandchild1.has_children() is False  # 葉ノード
    assert child2.has_children() is False  # 葉ノード
