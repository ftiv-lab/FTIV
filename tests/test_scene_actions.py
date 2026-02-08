# -*- coding: utf-8 -*-
"""SceneActions のテスト (Sprint 3).

QInputDialog / QMessageBox を patch してカテゴリ・シーンの CRUD をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.controllers.scene_actions import SceneActions


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.scenes = {}
    mw.scene_tab = MagicMock()
    mw.file_manager = MagicMock()
    return mw


@pytest.fixture
def sa(mock_mw):
    return SceneActions(mock_mw)


# ============================================================
# add_new_category
# ============================================================
class TestAddNewCategory:
    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_adds_category(self, mock_dialog, sa, mock_mw):
        mock_dialog.getText.return_value = ("TestCat", True)
        sa.add_new_category()
        assert "TestCat" in mock_mw.scenes
        mock_mw.scene_tab.refresh_category_list.assert_called_once()

    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_cancel_does_nothing(self, mock_dialog, sa, mock_mw):
        mock_dialog.getText.return_value = ("", False)
        sa.add_new_category()
        assert len(mock_mw.scenes) == 0

    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_empty_name_ok_does_nothing(self, mock_dialog, sa, mock_mw):
        mock_dialog.getText.return_value = ("", True)
        sa.add_new_category()
        assert len(mock_mw.scenes) == 0

    @patch("ui.controllers.scene_actions.QMessageBox")
    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_duplicate_shows_warning(self, mock_input, mock_msg, sa, mock_mw):
        mock_mw.scenes["Existing"] = {}
        mock_input.getText.return_value = ("Existing", True)
        sa.add_new_category()
        mock_msg.warning.assert_called_once()


# ============================================================
# add_new_scene
# ============================================================
class TestAddNewScene:
    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_adds_scene(self, mock_dialog, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat1"
        mock_mw.scenes["Cat1"] = {}
        mock_dialog.getText.return_value = ("Scene1", True)
        mock_mw.file_manager.get_scene_data.return_value = {"data": 1}
        sa.add_new_scene()
        assert "Scene1" in mock_mw.scenes["Cat1"]
        mock_mw.scene_tab.refresh_scene_list.assert_called_once()

    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_no_category_warns(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = None
        sa.add_new_scene()
        mock_msg.warning.assert_called_once()

    @patch("ui.controllers.scene_actions.QMessageBox")
    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_duplicate_scene_warns(self, mock_input, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat1"
        mock_mw.scenes["Cat1"] = {"ExistingScene": {}}
        mock_input.getText.return_value = ("ExistingScene", True)
        sa.add_new_scene()
        mock_msg.warning.assert_called_once()

    @patch("ui.controllers.scene_actions.QInputDialog")
    def test_cancel_does_nothing(self, mock_dialog, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat1"
        mock_mw.scenes["Cat1"] = {}
        mock_dialog.getText.return_value = ("", False)
        sa.add_new_scene()
        assert len(mock_mw.scenes["Cat1"]) == 0


# ============================================================
# load_selected_scene
# ============================================================
class TestLoadSelectedScene:
    def test_loads_scene(self, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = "S1"
        mock_mw.scenes["Cat"] = {"S1": {"windows": []}}
        sa.load_selected_scene()
        mock_mw.file_manager.load_scene_from_data.assert_called_once_with({"windows": []})

    def test_no_selection_is_noop(self, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = None
        mock_mw.scene_tab.get_current_scene.return_value = None
        sa.load_selected_scene()
        mock_mw.file_manager.load_scene_from_data.assert_not_called()

    def test_no_scene_tab_is_noop(self):
        mw = MagicMock(spec=["scenes", "file_manager"])
        sa_limited = SceneActions(mw)
        sa_limited.load_selected_scene()

    def test_missing_scene_data_is_noop(self, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = "Missing"
        mock_mw.scenes["Cat"] = {}
        sa.load_selected_scene()
        mock_mw.file_manager.load_scene_from_data.assert_not_called()


# ============================================================
# update_selected_scene
# ============================================================
class TestUpdateSelectedScene:
    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_updates_scene(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = "S1"
        mock_mw.scenes["Cat"] = {"S1": {"old": True}}
        mock_msg.question.return_value = mock_msg.Yes
        mock_mw.file_manager.get_scene_data.return_value = {"new": True}
        sa.update_selected_scene()
        assert mock_mw.scenes["Cat"]["S1"] == {"new": True}

    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_cancel_keeps_old_data(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = "S1"
        mock_mw.scenes["Cat"] = {"S1": {"old": True}}
        mock_msg.question.return_value = mock_msg.No
        sa.update_selected_scene()
        assert mock_mw.scenes["Cat"]["S1"] == {"old": True}

    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_no_selection_warns(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = None
        mock_mw.scene_tab.get_current_scene.return_value = None
        sa.update_selected_scene()
        mock_msg.warning.assert_called_once()

    def test_no_scene_tab_is_noop(self):
        mw = MagicMock(spec=["scenes", "file_manager"])
        sa_limited = SceneActions(mw)
        sa_limited.update_selected_scene()


# ============================================================
# delete_selected_item
# ============================================================
class TestDeleteSelectedItem:
    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_delete_scene(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = "S1"
        mock_mw.scenes["Cat"] = {"S1": {}}
        mock_msg.question.return_value = mock_msg.Yes
        sa.delete_selected_item()
        assert "S1" not in mock_mw.scenes["Cat"]
        mock_mw.scene_tab.refresh_scene_list.assert_called_once()

    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_delete_category(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = None
        mock_mw.scenes["Cat"] = {}
        mock_msg.question.return_value = mock_msg.Yes
        sa.delete_selected_item()
        assert "Cat" not in mock_mw.scenes
        mock_mw.scene_tab.refresh_category_list.assert_called_once()

    @patch("ui.controllers.scene_actions.QMessageBox")
    def test_cancel_keeps_data(self, mock_msg, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = "Cat"
        mock_mw.scene_tab.get_current_scene.return_value = None
        mock_mw.scenes["Cat"] = {}
        mock_msg.question.return_value = mock_msg.No
        sa.delete_selected_item()
        assert "Cat" in mock_mw.scenes

    def test_nothing_selected_is_noop(self, sa, mock_mw):
        mock_mw.scene_tab.get_current_category.return_value = None
        mock_mw.scene_tab.get_current_scene.return_value = None
        sa.delete_selected_item()

    def test_no_scene_tab_is_noop(self):
        mw = MagicMock(spec=["scenes"])
        sa_limited = SceneActions(mw)
        sa_limited.delete_selected_item()
