# -*- coding: utf-8 -*-
"""LayoutActions のテスト (Sprint 3).

_get_all_image_windows, pack_all_left_top, pack_all_center, align_images_grid をカバー。
QApplication.screens() を patch してモニタ依存なしでテスト。
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.controllers.layout_actions import LayoutActions


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.window_manager = MagicMock()
    mw.window_manager.image_windows = []
    mw.undo_stack = MagicMock()
    return mw


@pytest.fixture
def la(mock_mw):
    return LayoutActions(mock_mw)


def _make_screen(x: int = 0, y: int = 0, w: int = 1920, h: int = 1080):
    """Helper to create a mock screen with geometry."""
    geo = MagicMock()
    geo.x.return_value = x
    geo.y.return_value = y
    geo.width.return_value = w
    geo.height.return_value = h
    center = MagicMock()
    center.x.return_value = x + w // 2
    center.y.return_value = y + h // 2
    geo.center.return_value = center
    screen = MagicMock()
    screen.geometry.return_value = geo
    return screen


def _make_image_window(w: int = 100, h: int = 50):
    """Helper to create a mock image window."""
    win = MagicMock()
    win.width.return_value = w
    win.height.return_value = h
    return win


# ============================================================
# _get_all_image_windows
# ============================================================
class TestGetAllImageWindows:
    def test_from_window_manager(self, la, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        assert la._get_all_image_windows() == [w]

    def test_empty(self, la, mock_mw):
        mock_mw.window_manager.image_windows = []
        assert la._get_all_image_windows() == []

    def test_fallback_to_mw(self):
        mw = MagicMock(spec=["image_windows"])
        mw.image_windows = [MagicMock()]
        la_limited = LayoutActions(mw)
        assert len(la_limited._get_all_image_windows()) == 1

    def test_no_attribute_returns_empty(self):
        mw = MagicMock(spec=[])
        la_limited = LayoutActions(mw)
        assert la_limited._get_all_image_windows() == []


# ============================================================
# pack_all_left_top
# ============================================================
class TestPackAllLeftTop:
    @patch("ui.controllers.layout_actions.QApplication")
    def test_empty_images_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = []
        la.pack_all_left_top(0)
        mock_qapp.screens.assert_not_called()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_invalid_screen_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = [_make_image_window()]
        mock_qapp.screens.return_value = []
        la.pack_all_left_top(0)

    @patch("ui.controllers.layout_actions.QApplication")
    def test_packs_images(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w1 = _make_image_window(100, 50)
        w2 = _make_image_window(200, 80)
        mock_mw.window_manager.image_windows = [w1, w2]

        la.pack_all_left_top(0)
        w1.set_undoable_geometry.assert_called_once()
        w2.set_undoable_geometry.assert_called_once()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_skips_none_windows(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w1 = _make_image_window()
        mock_mw.window_manager.image_windows = [None, w1]

        la.pack_all_left_top(0)
        w1.set_undoable_geometry.assert_called_once()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_uses_undo_macro(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]
        mock_mw.window_manager.image_windows = [_make_image_window()]

        la.pack_all_left_top(0)
        mock_mw.undo_stack.beginMacro.assert_called_once_with("Pack Left-Top")
        mock_mw.undo_stack.endMacro.assert_called_once()


# ============================================================
# pack_all_center
# ============================================================
class TestPackAllCenter:
    @patch("ui.controllers.layout_actions.QApplication")
    def test_empty_images_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = []
        la.pack_all_center(0)
        mock_qapp.screens.assert_not_called()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_invalid_screen_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = [_make_image_window()]
        mock_qapp.screens.return_value = []
        la.pack_all_center(0)

    @patch("ui.controllers.layout_actions.QApplication")
    def test_packs_center(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w = _make_image_window(100, 50)
        mock_mw.window_manager.image_windows = [w]

        la.pack_all_center(0)
        w.set_undoable_geometry.assert_called_once()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_uses_undo_macro(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]
        mock_mw.window_manager.image_windows = [_make_image_window()]

        la.pack_all_center(0)
        mock_mw.undo_stack.beginMacro.assert_called_once_with("Pack Center")
        mock_mw.undo_stack.endMacro.assert_called_once()


# ============================================================
# align_images_grid
# ============================================================
class TestAlignImagesGrid:
    @patch("ui.controllers.layout_actions.QApplication")
    def test_empty_images_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = []
        la.align_images_grid(3, 10, 0)
        mock_qapp.screens.assert_not_called()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_invalid_screen_returns_early(self, mock_qapp, la, mock_mw):
        mock_mw.window_manager.image_windows = [_make_image_window()]
        mock_qapp.screens.return_value = []
        la.align_images_grid(2, 10, 0)

    @patch("ui.controllers.layout_actions.QApplication")
    def test_grid_alignment(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w1 = _make_image_window(100, 50)
        w2 = _make_image_window(100, 50)
        w3 = _make_image_window(100, 50)
        mock_mw.window_manager.image_windows = [w1, w2, w3]

        la.align_images_grid(2, 10, 0)
        assert w1.set_undoable_geometry.called
        assert w2.set_undoable_geometry.called
        assert w3.set_undoable_geometry.called

    @patch("ui.controllers.layout_actions.QApplication")
    def test_preview_mode_uses_move(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w = _make_image_window(100, 50)
        mock_mw.window_manager.image_windows = [w]

        la.align_images_grid(2, 10, 0, preview_mode=True)
        w.move.assert_called_once()
        w.set_undoable_geometry.assert_not_called()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_uses_undo_macro(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]
        mock_mw.window_manager.image_windows = [_make_image_window()]

        la.align_images_grid(2, 10, 0)
        mock_mw.undo_stack.beginMacro.assert_called_once_with("Align Grid")
        mock_mw.undo_stack.endMacro.assert_called_once()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_preview_mode_no_undo(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]
        mock_mw.window_manager.image_windows = [_make_image_window()]

        la.align_images_grid(2, 10, 0, preview_mode=True)
        mock_mw.undo_stack.beginMacro.assert_not_called()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_skips_none_windows(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        w1 = _make_image_window()
        mock_mw.window_manager.image_windows = [None, w1]

        la.align_images_grid(2, 10, 0)
        w1.set_undoable_geometry.assert_called_once()

    @patch("ui.controllers.layout_actions.QApplication")
    def test_column_wrap(self, mock_qapp, la, mock_mw):
        screen = _make_screen()
        mock_qapp.screens.return_value = [screen]

        wins = [_make_image_window(100, 50) for _ in range(4)]
        mock_mw.window_manager.image_windows = wins

        la.align_images_grid(2, 10, 0)
        for w in wins:
            assert w.set_undoable_geometry.called
