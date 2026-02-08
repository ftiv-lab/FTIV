# -*- coding: utf-8 -*-
"""ImageActions のテスト (Sprint 3).

_get_selected_image を patch.object で制御し、
各アクション（transform, visibility, playback, manage, normalize, bulk）をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.controllers.image_actions import ImageActions


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.last_selected_window = None
    mw.window_manager = MagicMock()
    mw.window_manager.image_windows = []
    mw.image_tab = MagicMock()
    mw.undo_stack = MagicMock()
    mw.file_manager = MagicMock()
    return mw


@pytest.fixture
def ia(mock_mw):
    return ImageActions(mock_mw)


# ============================================================
# _get_selected_image / get_selected_image
# ============================================================
class TestGetSelectedImage:
    def test_none_returns_none(self, ia, mock_mw):
        mock_mw.last_selected_window = None
        assert ia._get_selected_image() is None
        assert ia.get_selected_image() is None

    def test_non_image_returns_none(self, ia, mock_mw):
        mock_mw.last_selected_window = MagicMock()
        assert ia._get_selected_image() is None


# ============================================================
# add_image_from_path
# ============================================================
class TestAddImageFromPath:
    def test_delegates_to_window_manager(self, ia, mock_mw):
        ia.add_image_from_path("/path/to/image.png")
        mock_mw.window_manager.add_image_window.assert_called_once_with("/path/to/image.png")

    def test_sets_last_directory(self, ia, mock_mw):
        ia.add_image_from_path("/path/to/image.png")
        assert mock_mw.last_directory == "/path/to"


# ============================================================
# run_selected_transform_action
# ============================================================
class TestRunSelectedTransformAction:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.run_selected_transform_action("size")

    @patch.object(ImageActions, "_get_selected_image")
    def test_size_action(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_transform_action("size")
        w.open_size_dialog.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_opacity_action(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_transform_action("opacity")
        w.open_opacity_dialog.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_rotation_action(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_transform_action("rotation")
        w.open_rotation_dialog.assert_called_once()


# ============================================================
# run_selected_visibility_action
# ============================================================
class TestRunSelectedVisibilityAction:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.run_selected_visibility_action("show")

    @patch.object(ImageActions, "_get_selected_image")
    def test_show(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("show")
        w.show_action.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_hide(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("hide")
        w.hide_action.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_frontmost_with_checked(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("frontmost", checked=True)
        w.set_frontmost.assert_called_once_with(True)

    @patch.object(ImageActions, "_get_selected_image")
    def test_frontmost_toggle(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("frontmost")
        w.toggle_frontmost.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_click_through_with_checked(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("click_through", checked=True)
        w.set_click_through.assert_called_once_with(True)

    @patch.object(ImageActions, "_get_selected_image")
    def test_click_through_toggle(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_visibility_action("click_through")
        w.toggle_click_through.assert_called_once()


# ============================================================
# close_selected_image
# ============================================================
class TestCloseSelectedImage:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.close_selected_image()

    @patch.object(ImageActions, "_get_selected_image")
    def test_closes_with_close_action(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.close_selected_image()
        w.close_action.assert_called_once()


# ============================================================
# run_selected_playback_action
# ============================================================
class TestRunSelectedPlaybackAction:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.run_selected_playback_action("toggle")

    @patch.object(ImageActions, "_get_selected_image")
    def test_toggle(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_playback_action("toggle")
        w.toggle_image_animation_speed.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_speed(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_playback_action("speed")
        w.open_anim_speed_dialog.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_reset(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_playback_action("reset")
        w.reset_animation_speed.assert_called_once()


# ============================================================
# run_selected_other_images_action
# ============================================================
class TestRunSelectedOtherImagesAction:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.run_selected_other_images_action("hide_others")

    @patch.object(ImageActions, "_get_selected_image")
    def test_hide_others(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_other_images_action("hide_others")
        w.hide_all_other_windows.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_show_others(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        other = MagicMock()
        mock_get.return_value = selected
        mock_mw.window_manager.image_windows = [selected, other]
        ia.run_selected_other_images_action("show_others")
        other.show_action.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_show_others_skips_none(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        mock_get.return_value = selected
        mock_mw.window_manager.image_windows = [selected, None]
        ia.run_selected_other_images_action("show_others")

    @patch.object(ImageActions, "_get_selected_image")
    def test_close_others(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_other_images_action("close_others")
        w.close_all_other_images.assert_called_once()


# ============================================================
# set_selected_rotation_angle
# ============================================================
class TestSetSelectedRotationAngle:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.set_selected_rotation_angle(90)

    @patch.object(ImageActions, "_get_selected_image")
    def test_sets_via_undoable(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.set_selected_rotation_angle(90)
        w.set_undoable_property.assert_called_once_with("rotation_angle", 90.0, "update_image")

    @patch.object(ImageActions, "_get_selected_image")
    def test_invalid_angle_is_noop(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.set_selected_rotation_angle("not_a_number")
        w.set_undoable_property.assert_not_called()


# ============================================================
# flip_selected
# ============================================================
class TestFlipSelected:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.flip_selected("h")

    @patch.object(ImageActions, "_get_selected_image")
    def test_horizontal(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.flip_selected("h")
        w.flip_horizontal_action.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_vertical(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.flip_selected("v")
        w.flip_vertical_action.assert_called_once()


# ============================================================
# reset_selected_transform
# ============================================================
class TestResetSelectedTransform:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.reset_selected_transform("size")

    @patch.object(ImageActions, "_get_selected_image")
    def test_size(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.reset_selected_transform("size")
        w.reset_image_size.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_opacity(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.reset_selected_transform("opacity")
        w.reset_opacity.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_rotation(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.reset_selected_transform("rotation")
        w.reset_rotation.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_flips(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.reset_selected_transform("flips")
        w.reset_flip.assert_called_once()


# ============================================================
# run_selected_manage_action
# ============================================================
class TestRunSelectedManageAction:
    @patch.object(ImageActions, "_get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.run_selected_manage_action("reselect")

    @patch.object(ImageActions, "_get_selected_image")
    def test_reselect(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_manage_action("reselect")
        w.reselect_image.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_clone(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_manage_action("clone")
        w.clone_image.assert_called_once()

    @patch.object(ImageActions, "_get_selected_image")
    def test_save_json(self, mock_get, ia, mock_mw):
        w = MagicMock()
        mock_get.return_value = w
        ia.run_selected_manage_action("save_json")
        mock_mw.file_manager.save_window_to_json.assert_called_once_with(w)


# ============================================================
# fit / center / snap
# ============================================================
class TestFitCenterSnap:
    @patch.object(ImageActions, "get_selected_image", return_value=None)
    def test_fit_none(self, _mock, ia):
        ia.fit_selected_to_display(0)

    @patch.object(ImageActions, "get_selected_image")
    def test_fit(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.fit_selected_to_display(0)
        w.fit_to_display.assert_called_once_with(0)

    @patch.object(ImageActions, "get_selected_image")
    def test_center(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.center_selected_on_display(1)
        w.center_on_display.assert_called_once_with(1)

    @patch.object(ImageActions, "get_selected_image")
    def test_snap_edge(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.snap_selected_to_display_edge(0, "left")
        w.snap_to_display_edge.assert_called_once_with(0, "left")

    @patch.object(ImageActions, "get_selected_image")
    def test_snap_corner(self, mock_get, ia):
        w = MagicMock()
        mock_get.return_value = w
        ia.snap_selected_to_display_corner(0, "top-left")
        w.snap_to_display_corner.assert_called_once_with(0, "top-left")


# ============================================================
# _get_all_images
# ============================================================
class TestGetAllImages:
    def test_from_window_manager(self, ia, mock_mw):
        w1 = MagicMock()
        mock_mw.window_manager.image_windows = [w1]
        assert ia._get_all_images() == [w1]

    def test_empty(self, ia, mock_mw):
        mock_mw.window_manager.image_windows = []
        assert ia._get_all_images() == []

    def test_fallback_to_mw(self):
        mw = MagicMock(spec=["image_windows"])
        mw.image_windows = [MagicMock()]
        ia_limited = ImageActions(mw)
        assert len(ia_limited._get_all_images()) == 1


# ============================================================
# Bulk realtime methods
# ============================================================
class TestBulkRealtimeMethods:
    def test_set_all_image_opacity_realtime(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.set_all_image_opacity_realtime(50)
        w.set_opacity.assert_called_once_with(0.5)

    def test_opacity_skips_none(self, ia, mock_mw):
        mock_mw.window_manager.image_windows = [None]
        ia.set_all_image_opacity_realtime(50)

    def test_set_all_image_size_realtime(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.set_all_image_size_realtime(200)
        assert w.scale_factor == 2.0
        w.update_image.assert_called_once()

    def test_set_all_image_rotation_realtime(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.set_all_image_rotation_realtime(90)
        w.set_rotation_angle.assert_called_once_with(90.0)

    def test_set_all_gif_apng_speed_realtime(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.set_all_gif_apng_playback_speed_realtime(200)
        w.set_animation_speed_factor.assert_called_once_with(200)


# ============================================================
# Reset / toggle all
# ============================================================
class TestResetAll:
    def test_reset_all_flips(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.reset_all_flips()
        w.reset_flip.assert_called_once()

    def test_reset_all_flips_skips_none(self, ia, mock_mw):
        mock_mw.window_manager.image_windows = [None]
        ia.reset_all_flips()

    def test_reset_all_animation_speeds(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.reset_all_animation_speeds()
        w.reset_animation_speed.assert_called_once()

    def test_stop_all_image_animations(self, ia, mock_mw):
        w = MagicMock()
        mock_mw.window_manager.image_windows = [w]
        ia.stop_all_image_animations()
        w.set_animation_speed_factor.assert_called_once_with(0)

    def test_toggle_all_speed_stops_when_playing(self, ia, mock_mw):
        w = MagicMock()
        w.animation_speed_factor = 100
        mock_mw.window_manager.image_windows = [w]
        ia.toggle_all_image_animation_speed()
        w.set_animation_speed_factor.assert_called_once_with(0)

    def test_toggle_all_speed_plays_when_stopped(self, ia, mock_mw):
        w = MagicMock()
        w.animation_speed_factor = 0
        mock_mw.window_manager.image_windows = [w]
        ia.toggle_all_image_animation_speed()
        w.reset_animation_speed.assert_called_once()

    def test_toggle_empty_is_noop(self, ia, mock_mw):
        mock_mw.window_manager.image_windows = []
        ia.toggle_all_image_animation_speed()


# ============================================================
# normalize_all_images_by_selected
# ============================================================
class TestNormalizeAllImages:
    @patch.object(ImageActions, "get_selected_image", return_value=None)
    def test_none_is_noop(self, _mock, ia):
        ia.normalize_all_images_by_selected("same_pct")

    @patch.object(ImageActions, "get_selected_image")
    def test_same_pct(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        selected.scale_factor = 2.0
        selected.width.return_value = 100
        selected.height.return_value = 200
        mock_get.return_value = selected

        other = MagicMock()
        other.scale_factor = 1.0
        other.width.return_value = 50
        other.height.return_value = 100
        mock_mw.window_manager.image_windows = [selected, other]

        ia.normalize_all_images_by_selected("same_pct")
        other.set_undoable_property.assert_called()

    @patch.object(ImageActions, "get_selected_image")
    def test_same_width(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        selected.scale_factor = 1.0
        selected.width.return_value = 200
        selected.height.return_value = 100
        mock_get.return_value = selected

        other = MagicMock()
        other.scale_factor = 1.0
        other.width.return_value = 100
        other.height.return_value = 50
        mock_mw.window_manager.image_windows = [other]

        ia.normalize_all_images_by_selected("same_width")
        other.set_undoable_property.assert_called()

    @patch.object(ImageActions, "get_selected_image")
    def test_same_height(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        selected.scale_factor = 1.0
        selected.width.return_value = 200
        selected.height.return_value = 100
        mock_get.return_value = selected

        other = MagicMock()
        other.scale_factor = 1.0
        other.width.return_value = 100
        other.height.return_value = 50
        mock_mw.window_manager.image_windows = [other]

        ia.normalize_all_images_by_selected("same_height")
        other.set_undoable_property.assert_called()

    @patch.object(ImageActions, "get_selected_image")
    def test_empty_windows(self, mock_get, ia, mock_mw):
        selected = MagicMock()
        selected.scale_factor = 1.0
        selected.width.return_value = 100
        selected.height.return_value = 100
        mock_get.return_value = selected
        mock_mw.window_manager.image_windows = []
        ia.normalize_all_images_by_selected("same_pct")
