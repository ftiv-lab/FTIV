# -*- coding: utf-8 -*-
"""StyleGalleryDialog SP2 テスト.

カテゴリフィルタ、拡張検索、ソート、説明文表示、display_name表示をカバー。
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.dialogs import StyleGalleryDialog


@pytest.fixture(scope="module")
def qapp():
    """QApplication インスタンスを保証する。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def presets_dir(tmp_path):
    """テスト用プリセットディレクトリを作成する。"""
    d = tmp_path / "presets"
    d.mkdir()
    return d


def _write_preset(presets_dir, name: str, **meta) -> str:
    """ヘルパー: プリセットJSONを書き込む。"""
    data = {"_type": "ftiv_text_style", "_version": "1.1", "font": "Arial"}
    data.update({f"_{k}" if not k.startswith("_") else k: v for k, v in meta.items()})
    # Normalize key names: remove double underscore
    normalized = {}
    for k, v in data.items():
        key = k if not k.startswith("__") else k[1:]
        normalized[key] = v
    path = presets_dir / f"{name}.json"
    path.write_text(json.dumps(normalized, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _make_preset_data(name, **overrides):
    """ヘルパー: get_available_presets() が返す辞書を模擬する。"""
    base = {
        "name": name,
        "json_path": f"/tmp/presets/{name}.json",
        "thumb_path": None,
        "display_name": overrides.get("display_name", name),
        "description": overrides.get("description", ""),
        "category": overrides.get("category", "other"),
        "tags": overrides.get("tags", []),
        "favorite": overrides.get("favorite", False),
        "builtin": overrides.get("builtin", False),
        "created": overrides.get("created", ""),
        "author": overrides.get("author", "user"),
        "version": "1.1",
        "type": "ftiv_text_style",
    }
    base.update(overrides)
    return base


@pytest.fixture
def mock_style_manager():
    """StyleManager のモック。"""
    sm = MagicMock()
    sm.get_available_presets.return_value = [
        _make_preset_data(
            "neon_blue",
            display_name="ネオンブルー",
            category="neon",
            tags=["glow", "dark"],
            description="青いネオン発光",
            created="2026-02-20",
        ),
        _make_preset_data(
            "game_fire",
            display_name="ゲーム炎",
            category="game",
            tags=["fire", "glow"],
            description="炎エフェクト風",
            created="2026-02-21",
        ),
        _make_preset_data(
            "subtitle_simple",
            display_name="シンプル字幕",
            category="subtitle",
            tags=["simple"],
            description="白テキスト黒背景",
            created="2026-02-22",
        ),
        _make_preset_data(
            "gold_elegant",
            display_name="ゴールドエレガント",
            category="elegant",
            tags=["gradient", "gold"],
            description="金文字グラデーション",
            created="2026-02-19",
        ),
        _make_preset_data(
            "memo_dark",
            display_name="ダークメモ",
            category="card",
            tags=["dark", "bg"],
            description="暗いカード風",
            created="2026-02-18",
        ),
    ]
    return sm


@pytest.fixture
def dialog(qapp, mock_style_manager):
    """StyleGalleryDialog インスタンスを作成する。"""
    dlg = StyleGalleryDialog(mock_style_manager)
    return dlg


# ============================================================
# PRESET_CATEGORIES 定数
# ============================================================
class TestPresetCategories:
    def test_categories_defined(self):
        cats = StyleGalleryDialog.PRESET_CATEGORIES
        assert len(cats) >= 10
        ids = [c[0] for c in cats]
        assert "all" in ids
        assert "neon" in ids
        assert "game" in ids
        assert "subtitle" in ids

    def test_categories_have_tr_keys(self):
        for cat_id, tr_key in StyleGalleryDialog.PRESET_CATEGORIES:
            assert tr_key.startswith("preset_cat_")


# ============================================================
# load_presets: display_name + メタ情報保持
# ============================================================
class TestLoadPresets:
    def test_items_use_display_name(self, dialog):
        """display_name がアイテムテキストに使われる。"""
        texts = [dialog.list_widget.item(i).text() for i in range(dialog.list_widget.count())]
        assert "ネオンブルー" in texts
        assert "ゲーム炎" in texts
        assert "シンプル字幕" in texts

    def test_meta_stored_in_user_role_plus_1(self, dialog):
        """メタ情報が UserRole+1 に保持される。"""
        item = dialog.list_widget.item(0)
        meta = item.data(Qt.UserRole + 1)
        assert isinstance(meta, dict)
        assert "category" in meta
        assert "tags" in meta
        assert "description" in meta
        assert "display_name" in meta

    def test_json_path_in_user_role(self, dialog):
        """json_path が UserRole に保持される。"""
        item = dialog.list_widget.item(0)
        path = item.data(Qt.UserRole)
        assert path.endswith(".json")


# ============================================================
# カテゴリフィルタ
# ============================================================
class TestCategoryFilter:
    def test_all_category_shows_all(self, dialog):
        """'すべて' カテゴリでは全アイテムが表示される。"""
        dialog.cmb_category.setCurrentIndex(0)  # "all"
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 5

    def test_neon_category_filters(self, dialog):
        """'ネオン' カテゴリで neon のみ表示される。"""
        idx = dialog.cmb_category.findData("neon")
        dialog.cmb_category.setCurrentIndex(idx)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1
        assert visible[0].text() == "ネオンブルー"

    def test_game_category_filters(self, dialog):
        """'ゲーム' カテゴリで game のみ表示される。"""
        idx = dialog.cmb_category.findData("game")
        dialog.cmb_category.setCurrentIndex(idx)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1
        assert visible[0].text() == "ゲーム炎"

    def test_empty_category_shows_none(self, dialog):
        """該当なしカテゴリでは何も表示されない。"""
        idx = dialog.cmb_category.findData("comic")
        dialog.cmb_category.setCurrentIndex(idx)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 0


# ============================================================
# 拡張検索（名前 + タグ + 説明）
# ============================================================
class TestExtendedSearch:
    def test_search_by_display_name(self, dialog):
        """display_name での検索。"""
        dialog.cmb_category.setCurrentIndex(0)  # all
        dialog.search_input.setText("ネオン")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1
        assert visible[0].text() == "ネオンブルー"

    def test_search_by_tag(self, dialog):
        """タグでの検索。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.search_input.setText("glow")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        # neon_blue と game_fire の両方が "glow" タグを持つ
        assert len(visible) == 2

    def test_search_by_description(self, dialog):
        """説明文での検索。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.search_input.setText("グラデーション")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1
        assert visible[0].text() == "ゴールドエレガント"

    def test_search_combined_with_category(self, dialog):
        """カテゴリ + 検索の複合フィルタ。"""
        idx = dialog.cmb_category.findData("neon")
        dialog.cmb_category.setCurrentIndex(idx)
        dialog.search_input.setText("dark")  # neon_blue has "dark" tag
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1

    def test_search_no_match(self, dialog):
        """一致なしの検索。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.search_input.setText("xxxxxxnonexistent")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 0

    def test_clear_search_restores_all(self, dialog):
        """検索クリアで全表示に戻る。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.search_input.setText("ネオン")
        dialog.search_input.setText("")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 5


# ============================================================
# ソート
# ============================================================
class TestSort:
    def test_sort_by_name(self, dialog, mock_style_manager):
        """名前順ソート。"""
        idx = dialog.cmb_sort.findData("name")
        dialog.cmb_sort.setCurrentIndex(idx)
        texts = [dialog.list_widget.item(i).text() for i in range(dialog.list_widget.count())]
        # Japanese sort: ア行 < カ行 < サ行 < タ行 < ナ行
        # ゲーム炎, ゴールドエレガント, シンプル字幕, ダークメモ, ネオンブルー
        assert texts == sorted(texts, key=str.lower)

    def test_sort_by_date(self, dialog, mock_style_manager):
        """作成日順ソート（新しい順）。"""
        idx = dialog.cmb_sort.findData("created")
        dialog.cmb_sort.setCurrentIndex(idx)
        items_meta = [dialog.list_widget.item(i).data(Qt.UserRole + 1) for i in range(dialog.list_widget.count())]
        dates = [m.get("created", "") for m in items_meta]
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_category(self, dialog, mock_style_manager):
        """カテゴリ順ソート。"""
        idx = dialog.cmb_sort.findData("category")
        dialog.cmb_sort.setCurrentIndex(idx)
        items_meta = [dialog.list_widget.item(i).data(Qt.UserRole + 1) for i in range(dialog.list_widget.count())]
        categories = [m.get("category", "") for m in items_meta]
        assert categories == sorted(categories)


# ============================================================
# 説明文表示
# ============================================================
class TestDescriptionDisplay:
    def test_selection_shows_description(self, dialog):
        """アイテム選択で説明文が表示される。"""
        dialog.list_widget.setCurrentRow(0)
        text = dialog.lbl_description.text()
        assert text  # not empty

    def test_no_selection_empty_description(self, dialog):
        """選択解除で説明文が空になる。"""
        dialog._on_selection_changed(None, None)
        assert dialog.lbl_description.text() == ""

    def test_description_includes_tags(self, dialog):
        """説明にタグ情報が含まれる。"""
        # Find neon_blue item
        for i in range(dialog.list_widget.count()):
            item = dialog.list_widget.item(i)
            meta = item.data(Qt.UserRole + 1)
            if meta.get("category") == "neon":
                dialog.list_widget.setCurrentItem(item)
                break
        text = dialog.lbl_description.text()
        assert "glow" in text or "dark" in text


# ============================================================
# on_item_changed: display_name 更新
# ============================================================
class TestItemChanged:
    @patch("os.path.exists", return_value=True)
    def test_rename_updates_display_name_meta(self, mock_exists, dialog, mock_style_manager):
        """名前変更で update_preset_meta が呼ばれる。"""
        mock_style_manager.update_preset_meta.return_value = True
        item = dialog.list_widget.item(0)
        old_path = item.data(Qt.UserRole)
        # Simulate edit
        item.setText("新しい名前")
        mock_style_manager.update_preset_meta.assert_called_with(old_path, display_name="新しい名前")
        meta = item.data(Qt.UserRole + 1)
        assert meta["display_name"] == "新しい名前"

    @patch("os.path.exists", return_value=True)
    def test_rename_reverts_when_update_returns_false(self, mock_exists, dialog, mock_style_manager):
        """update_preset_meta が False を返したら表示名を元に戻す。"""
        mock_style_manager.update_preset_meta.return_value = False
        item = dialog.list_widget.item(0)
        original_text = item.text()
        original_meta = dict(item.data(Qt.UserRole + 1) or {})

        with patch("ui.dialogs.QMessageBox.critical") as mock_critical, patch("ui.dialogs.traceback.print_exc"):
            item.setText("保存失敗の名前")

        mock_critical.assert_called_once()
        assert item.text() == original_text
        meta = item.data(Qt.UserRole + 1)
        assert meta["display_name"] == original_meta["display_name"]

    @patch("os.path.exists", return_value=True)
    def test_empty_name_reverts(self, mock_exists, dialog, mock_style_manager):
        """空文字の名前変更は元に戻る。"""
        item = dialog.list_widget.item(0)
        item.setText("")
        # Should revert to original display_name
        assert item.text() != ""


# ============================================================
# UI構造テスト
# ============================================================
class TestUIStructure:
    def test_has_category_combo(self, dialog):
        assert hasattr(dialog, "cmb_category")
        assert dialog.cmb_category.count() >= 10

    def test_has_sort_combo(self, dialog):
        assert hasattr(dialog, "cmb_sort")
        assert dialog.cmb_sort.count() == 3

    def test_has_description_label(self, dialog):
        assert hasattr(dialog, "lbl_description")

    def test_has_search_input(self, dialog):
        assert hasattr(dialog, "search_input")

    def test_icon_size_140(self, dialog):
        """サムネイルサイズが140に拡大されている。"""
        size = dialog.list_widget.iconSize()
        assert size.width() == 140
        assert size.height() == 140

    def test_dialog_size(self, dialog):
        """ダイアログサイズが拡大されている。"""
        assert dialog.width() >= 640 or dialog.height() >= 550
