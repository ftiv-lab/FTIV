# -*- coding: utf-8 -*-
"""TextActions のテスト (Sprint 3).

_get_selected_obj, _is_text_window, add/clone/save/hide/show/close/visibility/layout をカバー。
型チェックメソッドは patch.object で制御し、ビジネスロジックに集中する。
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.controllers.text_actions import TextActions


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.last_selected_window = None
    mw.window_manager = MagicMock()
    mw.window_manager.text_windows = []
    mw.text_tab = MagicMock()
    mw.settings_manager = MagicMock()
    mw.file_manager = MagicMock()
    return mw


@pytest.fixture
def ta(mock_mw):
    return TextActions(mock_mw)


class TestGetSelectedObj:
    def test_returns_none_when_no_selection(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        assert ta._get_selected_obj() is None

    def test_returns_selected_window(self, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        assert ta._get_selected_obj() is w


class TestIsTextWindow:
    def test_non_text_window_returns_false(self, ta):
        assert ta._is_text_window(MagicMock()) is False

    def test_none_returns_false(self, ta):
        # isinstance(None, TextWindow) → False
        assert ta._is_text_window(None) is False


class TestIsTextLike:
    def test_non_text_returns_false(self, ta):
        assert ta._is_text_like(MagicMock()) is False


class TestAddNewTextWindow:
    def test_delegates_to_window_manager(self, ta, mock_mw):
        ta.add_new_text_window()
        mock_mw.window_manager.add_text_window.assert_called_once()

    def test_no_crash_without_window_manager(self):
        mw = MagicMock(spec=["last_selected_window"])
        ta_limited = TextActions(mw)
        ta_limited.add_new_text_window()  # No crash


class TestCloneSelected:
    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.clone_selected()  # No crash

    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_clones_text_window(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.clone_selected()
        w.clone_text.assert_called_once()

    @patch.object(TextActions, "_is_text_window", return_value=False)
    def test_non_text_window_is_noop(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.clone_selected()
        w.clone_text.assert_not_called()


class TestSaveSelectedToJson:
    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_saves_via_file_manager(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.save_selected_to_json()
        mock_mw.file_manager.save_window_to_json.assert_called_once_with(w)

    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.save_selected_to_json()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_no_file_manager_is_noop(self, _mock):
        mw = MagicMock(spec=["last_selected_window"])
        mw.last_selected_window = MagicMock()
        ta_limited = TextActions(mw)
        ta_limited.save_selected_to_json()  # No crash


class TestSavePngSelected:
    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_saves_png(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.save_png_selected()
        w.save_as_png.assert_called_once()

    def test_none_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.save_png_selected()


class TestHideOtherTextWindows:
    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_hides_others(self, _mock, ta, mock_mw):
        selected = MagicMock()
        other = MagicMock()
        other.is_hidden = False
        mock_mw.last_selected_window = selected
        mock_mw.window_manager.text_windows = [selected, other]
        ta.hide_other_text_windows()
        other.hide_action.assert_called_once()

    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_skips_none_and_self(self, _mock, ta, mock_mw):
        selected = MagicMock()
        mock_mw.last_selected_window = selected
        mock_mw.window_manager.text_windows = [selected, None]
        ta.hide_other_text_windows()  # No crash

    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.hide_other_text_windows()


class TestShowOtherTextWindows:
    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_shows_hidden_others(self, _mock, ta, mock_mw):
        selected = MagicMock()
        other = MagicMock()
        other.is_hidden = True
        mock_mw.last_selected_window = selected
        mock_mw.window_manager.text_windows = [selected, other]
        ta.show_other_text_windows()
        other.show_action.assert_called_once()

    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_skips_visible_others(self, _mock, ta, mock_mw):
        selected = MagicMock()
        other = MagicMock()
        other.is_hidden = False
        mock_mw.last_selected_window = selected
        mock_mw.window_manager.text_windows = [selected, other]
        ta.show_other_text_windows()
        other.show_action.assert_not_called()


class TestCloseOtherTextWindows:
    @patch.object(TextActions, "_is_text_window", return_value=True)
    def test_closes_others(self, _mock, ta, mock_mw):
        selected = MagicMock()
        other = MagicMock()
        mock_mw.last_selected_window = selected
        mock_mw.window_manager.text_windows = [selected, other]
        ta.close_other_text_windows()
        other.close.assert_called_once()


class TestRunSelectedVisibilityAction:
    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_show_action(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("show")
        w.show_action.assert_called_once()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_hide_action(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("hide")
        w.hide_action.assert_called_once()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_frontmost_with_checked(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("frontmost", checked=True)
        assert w.is_frontmost is True

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_frontmost_toggle(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("frontmost")
        w.toggle_frontmost.assert_called_once()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_click_through_with_checked(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("click_through", checked=True)
        assert w.is_click_through is True

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_click_through_toggle(self, _mock, ta, mock_mw):
        w = MagicMock()
        w.is_click_through = False
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("click_through")
        assert w.is_click_through is True

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_close_non_label(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_visibility_action("close")
        w.close.assert_called_once()

    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.run_selected_visibility_action("show")  # No crash


class TestSaveAsDefault:
    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_saves_archetype(self, _mock, ta, mock_mw):
        w = MagicMock()
        w.config = MagicMock()
        w.config.model_dump.return_value = {"font": "Arial"}
        mock_mw.last_selected_window = w
        mock_mw.settings_manager.save_text_archetype.return_value = True
        ta.save_as_default()
        mock_mw.settings_manager.save_text_archetype.assert_called_once()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_no_config_returns_early(self, _mock, ta, mock_mw):
        w = MagicMock(spec=["some_attr"])
        mock_mw.last_selected_window = w
        ta.save_as_default()

    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.save_as_default()


class TestRunSelectedLayoutAction:
    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_set_vertical(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_layout_action("set_vertical", checked=True)
        w.set_undoable_property.assert_called_once_with("is_vertical", True, "update_text")

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_set_vertical_without_checked_is_noop(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_layout_action("set_vertical")
        w.set_undoable_property.assert_not_called()

    @patch.object(TextActions, "_is_text_like", return_value=True)
    def test_open_spacing_settings(self, _mock, ta, mock_mw):
        w = MagicMock()
        mock_mw.last_selected_window = w
        ta.run_selected_layout_action("open_spacing_settings")
        w.open_spacing_settings.assert_called_once()

    def test_none_selection_is_noop(self, ta, mock_mw):
        mock_mw.last_selected_window = None
        ta.run_selected_layout_action("set_vertical", checked=True)
