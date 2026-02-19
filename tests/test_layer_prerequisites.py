"""
tests/test_layer_prerequisites.py

Layer Tab 実装の前提条件テスト。
Step 3 (window_config) / Step 4 (循環親子チェック) の動作を確認する。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _make_base_window(uuid_str: str = "test-uuid"):
    """テスト用の BaseOverlayWindow を Qt なしで生成する。
    uuid/parent_window_uuid は config プロパティ経由なので config を先に設定する。
    """
    from windows.base_window import BaseOverlayWindow

    with patch.object(BaseOverlayWindow, "__init__", lambda self, *a, **kw: None):
        w = BaseOverlayWindow.__new__(BaseOverlayWindow)

    # config を先に設定（uuid/parent_window_uuid はプロパティで config に委譲される）
    mock_config = MagicMock()
    mock_config.uuid = uuid_str
    mock_config.parent_uuid = None
    mock_config.layer_offset = None
    mock_config.layer_order = None
    mock_config.layer_scale_inherit = None
    mock_config.layer_rotation_inherit = None
    w.config = mock_config
    w.child_windows = []
    w.connected_lines = []
    return w


# ──────────────────────────────────────────────
# Step 3: window_config フィールド存在確認
# ──────────────────────────────────────────────


class TestWindowConfigLayerFields:
    def test_layer_offset_field_exists(self) -> None:
        """WindowConfigBase に layer_offset フィールドがある"""
        from models.window_config import WindowConfigBase

        assert "layer_offset" in WindowConfigBase.model_fields

    def test_layer_order_field_exists(self) -> None:
        """WindowConfigBase に layer_order フィールドがある"""
        from models.window_config import WindowConfigBase

        assert "layer_order" in WindowConfigBase.model_fields

    def test_layer_scale_inherit_field_exists(self) -> None:
        """WindowConfigBase に layer_scale_inherit フィールドがある"""
        from models.window_config import WindowConfigBase

        assert "layer_scale_inherit" in WindowConfigBase.model_fields

    def test_layer_rotation_inherit_field_exists(self) -> None:
        """WindowConfigBase に layer_rotation_inherit フィールドがある"""
        from models.window_config import WindowConfigBase

        assert "layer_rotation_inherit" in WindowConfigBase.model_fields

    def test_layer_fields_default_to_none(self) -> None:
        """Layer フィールドはデフォルトで None（後方互換）"""
        from models.window_config import TextWindowConfig

        cfg = TextWindowConfig()
        assert cfg.layer_offset is None
        assert cfg.layer_order is None
        assert cfg.layer_scale_inherit is None
        assert cfg.layer_rotation_inherit is None

    def test_layer_offset_accepts_dict(self) -> None:
        """layer_offset に {"x": 50, "y": -30} を設定できる"""
        from models.window_config import TextWindowConfig

        cfg = TextWindowConfig()
        cfg.layer_offset = {"x": 50, "y": -30}
        assert cfg.layer_offset == {"x": 50, "y": -30}

    def test_layer_order_accepts_int(self) -> None:
        """layer_order に int を設定できる"""
        from models.window_config import TextWindowConfig

        cfg = TextWindowConfig()
        cfg.layer_order = 2
        assert cfg.layer_order == 2

    def test_old_json_without_layer_fields_loads_ok(self) -> None:
        """layer フィールドがない旧 JSON でも TextWindowConfig が生成できる（後方互換）"""
        from models.window_config import TextWindowConfig

        old_data = {"uuid": "abc", "text": "hello"}
        cfg = TextWindowConfig(**old_data)
        assert cfg.uuid == "abc"
        assert cfg.layer_offset is None  # デフォルト


# ──────────────────────────────────────────────
# Step 4: 循環親子チェック
# ──────────────────────────────────────────────


class TestCyclicParentChildPrevention:
    def test_add_child_basic(self) -> None:
        """通常の親子追加が動作する"""
        parent = _make_base_window("parent")
        child = _make_base_window("child")
        parent.add_child_window(child)
        assert child in parent.child_windows
        assert child.parent_window_uuid == "parent"

    def test_add_self_is_noop(self) -> None:
        """自分自身を子にしようとすると無視される"""
        w = _make_base_window("w")
        w.add_child_window(w)
        assert w not in w.child_windows

    def test_add_existing_child_is_noop(self) -> None:
        """既に子として登録済みなら二重追加されない"""
        parent = _make_base_window("parent")
        child = _make_base_window("child")
        parent.add_child_window(child)
        parent.add_child_window(child)
        assert parent.child_windows.count(child) == 1

    def test_direct_cycle_raises(self) -> None:
        """A→B の後に B→A は ValueError"""
        a = _make_base_window("a")
        b = _make_base_window("b")
        a.add_child_window(b)
        with pytest.raises(ValueError, match="循環親子禁止"):
            b.add_child_window(a)

    def test_indirect_cycle_raises(self) -> None:
        """A→B→C の後に C→A は ValueError（孫レベルの循環）"""
        a = _make_base_window("a")
        b = _make_base_window("b")
        c = _make_base_window("c")
        a.add_child_window(b)
        b.add_child_window(c)
        with pytest.raises(ValueError, match="循環親子禁止"):
            c.add_child_window(a)

    def test_contains_in_subtree_basic(self) -> None:
        """_contains_in_subtree が自分自身で True を返す"""
        w = _make_base_window("w")
        assert w._contains_in_subtree(w) is True

    def test_contains_in_subtree_child(self) -> None:
        """_contains_in_subtree が子ウィンドウで True を返す"""
        parent = _make_base_window("parent")
        child = _make_base_window("child")
        parent.child_windows.append(child)
        assert parent._contains_in_subtree(child) is True

    def test_contains_in_subtree_unrelated_false(self) -> None:
        """_contains_in_subtree が無関係ノードで False を返す"""
        a = _make_base_window("a")
        b = _make_base_window("b")
        assert a._contains_in_subtree(b) is False

    def test_image_on_image_attachment(self) -> None:
        """ImageWindow を ImageWindow の子にできる（同じ BaseOverlayWindow 機構）"""
        parent_img = _make_base_window("img-parent")
        child_img = _make_base_window("img-child")
        parent_img.add_child_window(child_img)
        assert child_img in parent_img.child_windows
        assert child_img.parent_window_uuid == "img-parent"
