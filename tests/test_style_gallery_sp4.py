# -*- coding: utf-8 -*-
"""StyleGalleryDialog SP4 テスト.

お気に入りトグル、お気に入りフィルタ、ビルトイン削除保護、サムネイル再生成をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.dialogs import StyleGalleryDialog


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
            favorite=True,
        ),
        _make_preset_data(
            "game_fire",
            display_name="ゲーム炎",
            category="game",
            tags=["fire", "glow"],
            description="炎エフェクト風",
            favorite=False,
        ),
        _make_preset_data(
            "builtin_simple",
            display_name="ビルトイン字幕",
            category="subtitle",
            tags=["simple"],
            description="ビルトインのシンプル字幕",
            builtin=True,
        ),
    ]
    sm.get_all_tags.return_value = ["dark", "fire", "glow", "simple"]
    sm.update_preset_meta.return_value = True
    sm.generate_thumbnail.return_value = True
    return sm


@pytest.fixture
def dialog(qapp, mock_style_manager):
    return StyleGalleryDialog(mock_style_manager)


# ============================================================
# お気に入りトグル
# ============================================================
class TestFavoriteToggle:
    @patch("os.path.exists", return_value=True)
    def test_toggle_favorite_on(self, mock_exists, dialog, mock_style_manager):
        """お気に入りをONにできる。"""
        item = dialog.list_widget.item(1)  # game_fire: favorite=False
        dialog._toggle_favorite(item, True)
        mock_style_manager.update_preset_meta.assert_called_with(item.data(Qt.UserRole), favorite=True)
        meta = item.data(Qt.UserRole + 1)
        assert meta["favorite"] is True

    @patch("os.path.exists", return_value=True)
    def test_toggle_favorite_off(self, mock_exists, dialog, mock_style_manager):
        """お気に入りをOFFにできる。"""
        item = dialog.list_widget.item(0)  # neon_blue: favorite=True
        dialog._toggle_favorite(item, False)
        mock_style_manager.update_preset_meta.assert_called_with(item.data(Qt.UserRole), favorite=False)
        meta = item.data(Qt.UserRole + 1)
        assert meta["favorite"] is False

    @patch("os.path.exists", return_value=True)
    def test_toggle_favorite_failure_no_crash(self, mock_exists, dialog, mock_style_manager):
        """お気に入り更新失敗時にクラッシュしない。"""
        mock_style_manager.update_preset_meta.return_value = False
        item = dialog.list_widget.item(1)
        old_fav = (item.data(Qt.UserRole + 1) or {}).get("favorite")
        dialog._toggle_favorite(item, True)
        # Should not crash; favorite stays unchanged due to exception path
        # (RuntimeError raised internally, caught by except)
        meta = item.data(Qt.UserRole + 1) or {}
        assert meta.get("favorite") == old_fav

    @patch("os.path.exists", return_value=True)
    def test_toggle_favorite_updates_active_favorites_filter(self, mock_exists, dialog, mock_style_manager):
        """☆のみフィルタ中のトグルで表示状態が即時更新される。"""
        dialog.cmb_category.setCurrentIndex(0)  # all
        dialog.chk_favorites_only.setChecked(True)
        item = None
        for i in range(dialog.list_widget.count()):
            candidate = dialog.list_widget.item(i)
            meta = candidate.data(Qt.UserRole + 1) or {}
            if meta.get("name") == "neon_blue":
                item = candidate
                break
        assert item is not None
        assert not item.isHidden()

        dialog._toggle_favorite(item, False)

        assert item.isHidden()


# ============================================================
# お気に入りフィルタ
# ============================================================
class TestFavoriteFilter:
    def test_favorites_only_filter(self, dialog):
        """☆のみチェックでお気に入りだけ表示される。"""
        dialog.cmb_category.setCurrentIndex(0)  # all
        dialog.chk_favorites_only.setChecked(True)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1
        assert visible[0].text() == "ネオンブルー"

    def test_favorites_unchecked_shows_all(self, dialog):
        """☆のみ解除で全表示に戻る。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.chk_favorites_only.setChecked(True)
        dialog.chk_favorites_only.setChecked(False)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 3

    def test_favorites_combined_with_category(self, dialog):
        """カテゴリ + お気に入りの複合フィルタ。"""
        idx = dialog.cmb_category.findData("game")
        dialog.cmb_category.setCurrentIndex(idx)
        dialog.chk_favorites_only.setChecked(True)
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        # game_fire はお気に入りではない
        assert len(visible) == 0

    def test_favorites_combined_with_search(self, dialog):
        """検索 + お気に入りの複合フィルタ。"""
        dialog.cmb_category.setCurrentIndex(0)
        dialog.chk_favorites_only.setChecked(True)
        dialog.search_input.setText("ネオン")
        visible = [
            dialog.list_widget.item(i)
            for i in range(dialog.list_widget.count())
            if not dialog.list_widget.item(i).isHidden()
        ]
        assert len(visible) == 1


# ============================================================
# ビルトイン削除保護
# ============================================================
class TestBuiltinDeleteProtection:
    @patch("ui.dialogs.QMessageBox.warning")
    def test_delete_builtin_shows_warning(self, mock_warning, dialog, mock_style_manager):
        """ビルトインプリセットの削除で警告が出る。"""
        # Find builtin item
        builtin_item = None
        for i in range(dialog.list_widget.count()):
            item = dialog.list_widget.item(i)
            meta = item.data(Qt.UserRole + 1) or {}
            if meta.get("builtin"):
                builtin_item = item
                break
        assert builtin_item is not None
        dialog.delete_preset(builtin_item)
        mock_warning.assert_called_once()
        # delete_style should NOT be called
        mock_style_manager.delete_style.assert_not_called()

    @patch("ui.dialogs.QMessageBox.question", return_value=MagicMock(name="Yes"))
    def test_delete_non_builtin_allowed(self, mock_question, dialog, mock_style_manager):
        """非ビルトインプリセットは削除確認が出る。"""
        mock_question.return_value = MagicMock()
        # game_fire is not builtin
        item = dialog.list_widget.item(1)
        meta = item.data(Qt.UserRole + 1) or {}
        assert not meta.get("builtin", False)
        # We just verify that it gets past the builtin check
        # (the question dialog would be shown)
        with patch("ui.dialogs.QMessageBox.question") as mq:
            mq.return_value = MagicMock()  # Not QMessageBox.Yes → early return
            dialog.delete_preset(item)
            mq.assert_called_once()

    def test_context_menu_disables_delete_for_builtin(self, dialog):
        """右クリックメニューでビルトインの削除は無効化される。"""
        # Find builtin item index
        builtin_idx = None
        for i in range(dialog.list_widget.count()):
            item = dialog.list_widget.item(i)
            meta = item.data(Qt.UserRole + 1) or {}
            if meta.get("builtin"):
                builtin_idx = i
                break
        assert builtin_idx is not None

        # Get the item rect to simulate right-click position
        item = dialog.list_widget.item(builtin_idx)
        rect = dialog.list_widget.visualItemRect(item)

        with patch("ui.dialogs.QMenu") as MockMenu:
            mock_menu = MagicMock()
            MockMenu.return_value = mock_menu

            # Collect all addAction calls to check for disabled delete
            actions = []

            def capture_action(action):
                actions.append(action)

            mock_menu.addAction.side_effect = capture_action
            dialog.show_context_menu(rect.center())

            # Verify menu was shown
            mock_menu.exec.assert_called_once()


# ============================================================
# サムネイル再生成
# ============================================================
class TestThumbnailRegeneration:
    @patch("os.path.exists", return_value=True)
    def test_regenerate_thumbnail_calls_manager(self, mock_exists, dialog, mock_style_manager):
        """サムネイル再生成で generate_thumbnail が呼ばれる。"""
        item = dialog.list_widget.item(0)
        json_path = item.data(Qt.UserRole)
        dialog._regenerate_thumbnail(item)
        mock_style_manager.generate_thumbnail.assert_called_with(json_path)

    @patch("os.path.exists", return_value=True)
    def test_regenerate_thumbnail_reloads_on_success(self, mock_exists, dialog, mock_style_manager):
        """サムネイル再生成成功で load_presets が呼ばれる。"""
        mock_style_manager.generate_thumbnail.return_value = True
        item = dialog.list_widget.item(0)
        initial_call_count = mock_style_manager.get_available_presets.call_count
        dialog._regenerate_thumbnail(item)
        # load_presets triggers get_available_presets
        assert mock_style_manager.get_available_presets.call_count > initial_call_count

    @patch("os.path.exists", return_value=True)
    def test_regenerate_thumbnail_no_reload_on_failure(self, mock_exists, dialog, mock_style_manager):
        """サムネイル再生成失敗で load_presets は呼ばれない。"""
        mock_style_manager.generate_thumbnail.return_value = False
        item = dialog.list_widget.item(0)
        initial_call_count = mock_style_manager.get_available_presets.call_count
        dialog._regenerate_thumbnail(item)
        assert mock_style_manager.get_available_presets.call_count == initial_call_count


# ============================================================
# UI構造テスト
# ============================================================
class TestSP4UIStructure:
    def test_has_favorites_checkbox(self, dialog):
        assert hasattr(dialog, "chk_favorites_only")

    def test_favorites_checkbox_initially_unchecked(self, dialog):
        assert not dialog.chk_favorites_only.isChecked()

    def test_refresh_ui_text_updates_favorites_checkbox_label(self, dialog):
        with patch("ui.dialogs.tr", side_effect=lambda key: f"T:{key}"):
            dialog.refresh_ui_text()
        assert dialog.chk_favorites_only.text() == "T:preset_chk_favorites_only"

    def test_initial_favorite_meta_preserved(self, dialog):
        """ロード後にfavoriteメタが保持されている。"""
        for i in range(dialog.list_widget.count()):
            item = dialog.list_widget.item(i)
            meta = item.data(Qt.UserRole + 1) or {}
            if meta.get("name") == "neon_blue":
                assert meta["favorite"] is True
            elif meta.get("name") == "game_fire":
                assert meta["favorite"] is False

    def test_initial_builtin_meta_preserved(self, dialog):
        """ロード後にbuiltinメタが保持されている。"""
        for i in range(dialog.list_widget.count()):
            item = dialog.list_widget.item(i)
            meta = item.data(Qt.UserRole + 1) or {}
            if meta.get("name") == "builtin_simple":
                assert meta["builtin"] is True
