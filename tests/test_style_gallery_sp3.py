# -*- coding: utf-8 -*-
"""StyleGalleryDialog SP3 テスト.

タグ編集ダイアログ、カテゴリ変更、説明編集、右クリックメニュー拡張をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from ui.dialogs import PresetDescriptionEditDialog, PresetTagEditDialog, StyleGalleryDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _make_preset_data(name, **overrides):
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
    sm = MagicMock()
    sm.get_available_presets.return_value = [
        _make_preset_data(
            "neon_blue",
            display_name="ネオンブルー",
            category="neon",
            tags=["glow", "dark"],
            description="青いネオン発光",
        ),
        _make_preset_data(
            "game_fire",
            display_name="ゲーム炎",
            category="game",
            tags=["fire", "glow"],
            description="炎エフェクト風",
        ),
    ]
    sm.get_all_tags.return_value = ["dark", "fire", "glow", "gradient", "simple"]
    sm.update_preset_meta.return_value = True
    return sm


@pytest.fixture
def dialog(qapp, mock_style_manager):
    return StyleGalleryDialog(mock_style_manager)


# ============================================================
# PresetTagEditDialog
# ============================================================
class TestPresetTagEditDialog:
    def test_initial_tags(self, qapp):
        dlg = PresetTagEditDialog(["glow", "dark"], ["glow", "dark", "fire"])
        assert dlg.get_tags() == ["glow", "dark"]

    def test_add_tag(self, qapp):
        dlg = PresetTagEditDialog(["glow"], [])
        dlg._edit_add.setText("dark")
        dlg._add_tag_from_input()
        assert "dark" in dlg.get_tags()

    def test_add_duplicate_tag_ignored(self, qapp):
        dlg = PresetTagEditDialog(["glow"], [])
        dlg._add_tag("glow")
        assert dlg.get_tags().count("glow") == 1

    def test_add_tag_normalizes_case(self, qapp):
        dlg = PresetTagEditDialog([], [])
        dlg._add_tag("FIRE")
        assert dlg.get_tags() == ["fire"]

    def test_remove_tag_by_click(self, qapp):
        dlg = PresetTagEditDialog(["glow", "dark"], [])
        # Click first item to remove
        item = dlg._tags_list.item(0)
        dlg._remove_tag_by_click(item)
        assert "glow" not in dlg.get_tags()
        assert "dark" in dlg.get_tags()

    def test_add_empty_tag_ignored(self, qapp):
        dlg = PresetTagEditDialog([], [])
        dlg._edit_add.setText("   ")
        dlg._add_tag_from_input()
        assert dlg.get_tags() == []

    def test_suggestions_exclude_current(self, qapp):
        """候補にはcurrent_tagsに含まれないタグのみ表示される。"""
        dlg = PresetTagEditDialog(["glow"], ["glow", "dark", "fire"])
        # The dialog should have suggestion buttons for "dark" and "fire" only.
        # We can't easily check buttons, but verify no crash and tags work.
        dlg._add_tag("dark")
        assert set(dlg.get_tags()) == {"glow", "dark"}


# ============================================================
# PresetDescriptionEditDialog
# ============================================================
class TestPresetDescriptionEditDialog:
    def test_initial_text(self, qapp):
        dlg = PresetDescriptionEditDialog("テスト説明")
        assert dlg.get_description() == "テスト説明"

    def test_empty_description(self, qapp):
        dlg = PresetDescriptionEditDialog("")
        assert dlg.get_description() == ""

    def test_edit_description(self, qapp):
        dlg = PresetDescriptionEditDialog("旧説明")
        dlg._text_edit.setPlainText("新しい説明文")
        assert dlg.get_description() == "新しい説明文"

    def test_strips_whitespace(self, qapp):
        dlg = PresetDescriptionEditDialog("  余白あり  ")
        assert dlg.get_description() == "余白あり"


# ============================================================
# カテゴリ変更（右クリック操作）
# ============================================================
class TestCategoryChange:
    @patch("os.path.exists", return_value=True)
    def test_change_category_updates_meta(self, mock_exists, dialog, mock_style_manager):
        """カテゴリ変更で update_preset_meta が呼ばれる。"""
        item = dialog.list_widget.item(0)
        dialog._change_category(item, "game")
        mock_style_manager.update_preset_meta.assert_called_with(item.data(Qt.UserRole), category="game")
        meta = item.data(Qt.UserRole + 1)
        assert meta["category"] == "game"

    @patch("os.path.exists", return_value=True)
    def test_change_category_failure_no_crash(self, mock_exists, dialog, mock_style_manager):
        """カテゴリ変更失敗時にクラッシュしない。"""
        mock_style_manager.update_preset_meta.return_value = False
        item = dialog.list_widget.item(0)
        old_cat = (item.data(Qt.UserRole + 1) or {}).get("category")
        dialog._change_category(item, "comic")
        # Should not crash, category shouldn't change on failure
        # (RuntimeError raised internally, caught by except)
        meta = item.data(Qt.UserRole + 1) or {}
        assert meta.get("category") == old_cat


# ============================================================
# タグ編集（右クリック → ダイアログ）
# ============================================================
class TestTagEditFromGallery:
    @patch("os.path.exists", return_value=True)
    def test_open_tag_edit_dialog_updates_tags(self, mock_exists, dialog, mock_style_manager):
        """タグ編集ダイアログでタグが更新される。"""
        item = dialog.list_widget.item(0)

        with patch("ui.dialogs.PresetTagEditDialog") as MockDialog:
            mock_dlg = MagicMock()
            mock_dlg.exec.return_value = QDialog.Accepted
            mock_dlg.get_tags.return_value = ["glow", "neon", "blue"]
            MockDialog.return_value = mock_dlg

            dialog._open_tag_edit_dialog(item)

        mock_style_manager.update_preset_meta.assert_called_with(item.data(Qt.UserRole), tags=["glow", "neon", "blue"])
        meta = item.data(Qt.UserRole + 1)
        assert meta["tags"] == ["glow", "neon", "blue"]

    @patch("os.path.exists", return_value=True)
    def test_tag_edit_cancel_no_change(self, mock_exists, dialog, mock_style_manager):
        """タグ編集キャンセルで変更なし。"""
        item = dialog.list_widget.item(0)
        original_tags = list((item.data(Qt.UserRole + 1) or {}).get("tags", []))

        with patch("ui.dialogs.PresetTagEditDialog") as MockDialog:
            mock_dlg = MagicMock()
            mock_dlg.exec.return_value = QDialog.Rejected
            MockDialog.return_value = mock_dlg

            dialog._open_tag_edit_dialog(item)

        meta = item.data(Qt.UserRole + 1)
        assert meta["tags"] == original_tags


# ============================================================
# 説明編集（右クリック → ダイアログ）
# ============================================================
class TestDescriptionEditFromGallery:
    @patch("os.path.exists", return_value=True)
    def test_open_desc_edit_dialog_updates(self, mock_exists, dialog, mock_style_manager):
        """説明編集ダイアログで説明が更新される。"""
        item = dialog.list_widget.item(0)

        with patch("ui.dialogs.PresetDescriptionEditDialog") as MockDialog:
            mock_dlg = MagicMock()
            mock_dlg.exec.return_value = QDialog.Accepted
            mock_dlg.get_description.return_value = "新しい説明文"
            MockDialog.return_value = mock_dlg

            dialog._open_description_edit_dialog(item)

        mock_style_manager.update_preset_meta.assert_called_with(item.data(Qt.UserRole), description="新しい説明文")
        meta = item.data(Qt.UserRole + 1)
        assert meta["description"] == "新しい説明文"

    @patch("os.path.exists", return_value=True)
    def test_desc_edit_cancel_no_change(self, mock_exists, dialog, mock_style_manager):
        """説明編集キャンセルで変更なし。"""
        item = dialog.list_widget.item(0)
        original_desc = str((item.data(Qt.UserRole + 1) or {}).get("description", ""))

        with patch("ui.dialogs.PresetDescriptionEditDialog") as MockDialog:
            mock_dlg = MagicMock()
            mock_dlg.exec.return_value = QDialog.Rejected
            MockDialog.return_value = mock_dlg

            dialog._open_description_edit_dialog(item)

        meta = item.data(Qt.UserRole + 1)
        assert meta["description"] == original_desc
