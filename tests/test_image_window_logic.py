# -*- coding: utf-8 -*-
"""ImageWindow の計算・状態ロジックテスト (Sprint 4).

QLabel.__init__ をバイパスし、プロパティ / to_dict / apply_data /
fit_to_display / center / snap / propagate 系に集中する。
"""

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEasingCurve, QPoint

from models.window_config import ImageWindowConfig


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------
def _make_image_window(**overrides):
    """ImageWindow を __init__ バイパスで作成。"""
    from windows.image_window import ImageWindow

    with patch.object(ImageWindow, "__init__", lambda self, *a, **kw: None):
        obj = ImageWindow.__new__(ImageWindow)
    obj.config = ImageWindowConfig()
    obj.config.image_path = "test.png"
    obj.main_window = MagicMock()
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    obj.is_dragging = False
    obj.last_mouse_pos = None
    obj._drag_start_pos_global = None
    obj.fade_animation = None
    obj.fade_easing_curve = QEasingCurve.Type.Linear
    obj.move_animation = None
    obj.easing_curve = QEasingCurve.Type.Linear
    obj.frames = []
    obj.current_frame = 0
    obj.original_speed = 100
    obj.original_animation_speed_factor = 1.0
    obj.timer = MagicMock()
    obj.last_directory = ""
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


def _make_mock_pixmap(w=200, h=100):
    pix = MagicMock()
    pix.width.return_value = w
    pix.height.return_value = h
    sz = MagicMock()
    sz.width.return_value = w
    sz.height.return_value = h
    pix.size.return_value = sz
    return pix


def _make_mock_screen(x=0, y=0, w=1920, h=1080):
    geo = MagicMock()
    geo.x.return_value = x
    geo.y.return_value = y
    geo.width.return_value = w
    geo.height.return_value = h
    geo.left.return_value = x
    geo.top.return_value = y
    geo.right.return_value = x + w
    geo.bottom.return_value = y + h
    geo.center.return_value = MagicMock(x=lambda: x + w // 2, y=lambda: y + h // 2)
    screen = MagicMock()
    screen.geometry.return_value = geo
    screen.availableGeometry.return_value = geo
    return screen


# ============================================================
# Property Accessors
# ============================================================
class TestImagePropertyAccessors:
    def test_image_path(self):
        w = _make_image_window()
        w.image_path = "/img/test.png"
        assert w.image_path == "/img/test.png"
        assert w.config.image_path == "/img/test.png"

    def test_image_path_empty_string(self):
        w = _make_image_window()
        w.image_path = ""
        assert w.image_path == ""

    def test_scale_factor(self):
        w = _make_image_window()
        w.scale_factor = 2.5
        assert w.scale_factor == 2.5

    def test_opacity(self):
        w = _make_image_window()
        w.opacity = 0.75
        assert w.opacity == 0.75

    def test_rotation_angle(self):
        w = _make_image_window()
        w.rotation_angle = 90.0
        assert w.rotation_angle == 90.0

    def test_flip_horizontal(self):
        w = _make_image_window()
        w.flip_horizontal = True
        assert w.flip_horizontal is True

    def test_flip_vertical(self):
        w = _make_image_window()
        w.flip_vertical = True
        assert w.flip_vertical is True

    def test_animation_speed_factor(self):
        w = _make_image_window()
        w.animation_speed_factor = 0.5
        assert w.animation_speed_factor == 0.5

    def test_is_locked_default(self):
        w = _make_image_window()
        assert w.is_locked is False

    def test_is_locked_set(self):
        w = _make_image_window()
        w.is_locked = True
        assert w.is_locked is True


# ============================================================
# to_dict / apply_data
# ============================================================
class TestToDict:
    def test_returns_dict_with_type(self):
        w = _make_image_window()
        w.config.geometry = {"x": 10, "y": 20, "width": 100, "height": 50}
        w.config.position = {"x": 10, "y": 20}
        with (
            patch.object(type(w), "x", return_value=10),
            patch.object(type(w), "y", return_value=20),
            patch.object(type(w), "width", return_value=100),
            patch.object(type(w), "height", return_value=50),
        ):
            result = w.to_dict()
        assert result["type"] == "image"
        assert "uuid" in result

    def test_clears_legacy_positions(self):
        w = _make_image_window()
        w.config.start_position = {"x": 1, "y": 2}
        w.config.end_position = {"x": 3, "y": 4}
        with (
            patch.object(type(w), "x", return_value=0),
            patch.object(type(w), "y", return_value=0),
            patch.object(type(w), "width", return_value=100),
            patch.object(type(w), "height", return_value=100),
        ):
            result = w.to_dict()
        # start_position/end_position should be None and excluded
        assert "start_position" not in result
        assert "end_position" not in result


class TestApplyData:
    def test_applies_config_values(self):
        w = _make_image_window()
        with (
            patch.object(type(w), "_update_animation_timer"),
            patch.object(type(w), "update_image"),
            patch.object(type(w), "show"),
            patch.object(type(w), "setGeometry"),
            patch.object(type(w), "setWindowFlags"),
            patch.object(type(w), "windowFlags", return_value=0),
            patch.object(type(w), "set_click_through"),
        ):
            w.apply_data({"scale_factor": 3.0, "opacity": 0.5})
        assert w.config.scale_factor == 3.0
        assert w.config.opacity == 0.5

    def test_restores_geometry_in_config(self):
        w = _make_image_window()
        w.sig_properties_changed = MagicMock()
        with (
            patch.object(type(w), "_update_animation_timer"),
            patch.object(type(w), "update_image"),
            patch.object(type(w), "show"),
            patch.object(type(w), "setGeometry"),
            patch.object(type(w), "setWindowFlags"),
            patch.object(type(w), "windowFlags", return_value=0),
            patch.object(type(w), "setAttribute"),
            patch.object(type(w), "set_click_through"),
        ):
            w.apply_data({"geometry": {"x": 10, "y": 20, "width": 200, "height": 100}})
        # Config should have the geometry values
        assert w.config.geometry == {"x": 10, "y": 20, "width": 200, "height": 100}


# ============================================================
# _update_animation_timer
# ============================================================
class TestUpdateAnimationTimer:
    def test_starts_timer_when_speed_positive(self):
        w = _make_image_window()
        w.original_speed = 100
        w.config.animation_speed_factor = 2.0
        w.sig_properties_changed = MagicMock()
        w._update_animation_timer()
        w.timer.start.assert_called_once_with(50)

    def test_stops_timer_when_speed_zero(self):
        w = _make_image_window()
        w.original_speed = 100
        w.config.animation_speed_factor = 0.0
        w.sig_properties_changed = MagicMock()
        w._update_animation_timer()
        w.timer.stop.assert_called_once()

    def test_stops_timer_when_original_speed_zero(self):
        w = _make_image_window()
        w.original_speed = 0
        w.config.animation_speed_factor = 1.0
        w.sig_properties_changed = MagicMock()
        w._update_animation_timer()
        w.timer.stop.assert_called_once()


# ============================================================
# fit_to_display
# ============================================================
class TestFitToDisplay:
    @patch("windows.image_window.QApplication")
    def test_fit_calculates_correct_scale(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        pix = _make_mock_pixmap(960, 540)
        w.frames = [pix]

        with (
            patch.object(type(w), "set_undoable_property") as mock_prop,
            patch.object(type(w), "_center_to_geometry"),
            patch.object(type(w), "width", return_value=960),
            patch.object(type(w), "height", return_value=540),
        ):
            w.fit_to_display(0)
        # 1920/960 = 2.0, 1080/540 = 2.0 → min(2.0, 2.0) = 2.0
        mock_prop.assert_called_once_with("scale_factor", 2.0, "update_image")

    @patch("windows.image_window.QApplication")
    def test_fit_invalid_screen_index(self, mock_qapp):
        w = _make_image_window()
        mock_qapp.screens.return_value = [_make_mock_screen()]
        w.fit_to_display(5)  # Should return early, no crash

    @patch("windows.image_window.QApplication")
    def test_fit_empty_frames(self, mock_qapp):
        w = _make_image_window()
        mock_qapp.screens.return_value = [_make_mock_screen()]
        w.frames = []
        w.fit_to_display(0)  # No crash

    @patch("windows.image_window.QApplication")
    def test_fit_aspect_preserving(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        # Wide image: 1920 x 200 → scale_x = 1.0, scale_y = 5.4 → min = 1.0
        pix = _make_mock_pixmap(1920, 200)
        w.frames = [pix]

        with patch.object(type(w), "set_undoable_property") as mock_prop, patch.object(type(w), "_center_to_geometry"):
            w.fit_to_display(0)
        mock_prop.assert_called_once_with("scale_factor", 1.0, "update_image")


# ============================================================
# _center_to_geometry
# ============================================================
class TestCenterToGeometry:
    def test_centers_correctly(self):
        w = _make_image_window()
        geo = MagicMock()
        geo.x.return_value = 0
        geo.y.return_value = 0
        geo.width.return_value = 1920
        geo.height.return_value = 1080
        with (
            patch.object(type(w), "width", return_value=200),
            patch.object(type(w), "height", return_value=100),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(0, 0)),
            patch.object(type(w), "x", return_value=860),
            patch.object(type(w), "y", return_value=490),
        ):
            w._center_to_geometry(geo)
        # target_x = (1920-200)/2 = 860, target_y = (1080-100)/2 = 490
        mock_move.assert_called_once_with(860, 490)


# ============================================================
# snap_to_display_edge
# ============================================================
class TestSnapToDisplayEdge:
    @patch("windows.image_window.QApplication")
    def test_snap_left(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "x", return_value=500),
            patch.object(type(w), "y", return_value=300),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
        ):
            w.snap_to_display_edge(0, "left")
        mock_move.assert_called_once_with(0, 300)

    @patch("windows.image_window.QApplication")
    def test_snap_right(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "x", return_value=500),
            patch.object(type(w), "y", return_value=300),
            patch.object(type(w), "width", return_value=200),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
        ):
            w.snap_to_display_edge(0, "right")
        mock_move.assert_called_once_with(1720, 300)

    @patch("windows.image_window.QApplication")
    def test_snap_top(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "x", return_value=500),
            patch.object(type(w), "y", return_value=300),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
        ):
            w.snap_to_display_edge(0, "top")
        mock_move.assert_called_once_with(500, 0)

    @patch("windows.image_window.QApplication")
    def test_snap_bottom(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "x", return_value=500),
            patch.object(type(w), "y", return_value=300),
            patch.object(type(w), "height", return_value=100),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
        ):
            w.snap_to_display_edge(0, "bottom")
        mock_move.assert_called_once_with(500, 980)

    @patch("windows.image_window.QApplication")
    def test_snap_invalid_edge(self, mock_qapp):
        w = _make_image_window()
        mock_qapp.screens.return_value = [_make_mock_screen()]
        with (
            patch.object(type(w), "x", return_value=0),
            patch.object(type(w), "y", return_value=0),
            patch.object(type(w), "move") as mock_move,
        ):
            w.snap_to_display_edge(0, "invalid")
        mock_move.assert_not_called()


# ============================================================
# snap_to_display_corner
# ============================================================
class TestSnapToDisplayCorner:
    @patch("windows.image_window.QApplication")
    def test_snap_top_left(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
            patch.object(type(w), "x", return_value=0),
            patch.object(type(w), "y", return_value=0),
        ):
            w.snap_to_display_corner(0, "tl")
        mock_move.assert_called_once_with(0, 0)

    @patch("windows.image_window.QApplication")
    def test_snap_top_right(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "width", return_value=200),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
            patch.object(type(w), "x", return_value=1720),
            patch.object(type(w), "y", return_value=0),
        ):
            w.snap_to_display_corner(0, "tr")
        mock_move.assert_called_once_with(1720, 0)

    @patch("windows.image_window.QApplication")
    def test_snap_bottom_left(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "height", return_value=100),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
            patch.object(type(w), "x", return_value=0),
            patch.object(type(w), "y", return_value=980),
        ):
            w.snap_to_display_corner(0, "bl")
        mock_move.assert_called_once_with(0, 980)

    @patch("windows.image_window.QApplication")
    def test_snap_bottom_right(self, mock_qapp):
        w = _make_image_window()
        screen = _make_mock_screen(0, 0, 1920, 1080)
        mock_qapp.screens.return_value = [screen]
        with (
            patch.object(type(w), "width", return_value=200),
            patch.object(type(w), "height", return_value=100),
            patch.object(type(w), "move") as mock_move,
            patch.object(type(w), "pos", return_value=QPoint(500, 300)),
            patch.object(type(w), "x", return_value=1720),
            patch.object(type(w), "y", return_value=980),
        ):
            w.snap_to_display_corner(0, "br")
        mock_move.assert_called_once_with(1720, 980)

    @patch("windows.image_window.QApplication")
    def test_snap_invalid_corner(self, mock_qapp):
        w = _make_image_window()
        mock_qapp.screens.return_value = [_make_mock_screen()]
        with patch.object(type(w), "move") as mock_move:
            w.snap_to_display_corner(0, "xx")
        mock_move.assert_not_called()


# ============================================================
# propagate_scale_to_children
# ============================================================
class TestPropagateScaleToChildren:
    def test_no_children_noop(self):
        w = _make_image_window()
        w.child_windows = []
        w.propagate_scale_to_children(2.0)  # No crash

    def test_does_not_scale_image_child(self):
        w = _make_image_window()
        child = MagicMock()
        child.scale_factor = 1.0
        w.child_windows = [child]
        w.propagate_scale_to_children(2.0)
        assert child.scale_factor == 1.0
        child.update_image.assert_not_called()
        child.move.assert_not_called()

    def test_does_not_scale_text_child(self):
        w = _make_image_window()
        child = MagicMock(
            spec=[
                "font_size",
                "update_text",
                "geometry",
                "move",
                "width",
                "height",
                "background_corner_radius",
                "background_corner_ratio",
                "propagate_scale_to_children",
            ]
        )
        child.font_size = 24.0
        child.background_corner_ratio = 0.1
        w.child_windows = [child]
        w.propagate_scale_to_children(2.0)
        assert child.font_size == 24.0
        child.update_text.assert_not_called()


# ============================================================
# propagate_rotation_to_children
# ============================================================
class TestPropagateRotationToChildren:
    def test_no_children_noop(self):
        w = _make_image_window()
        w.child_windows = []
        w.propagate_rotation_to_children(45.0)  # No crash

    def test_does_not_rotate_child(self):
        w = _make_image_window()
        child = MagicMock()
        child.rotation_angle = 0.0

        w.child_windows = [child]
        w.propagate_rotation_to_children(90.0)

        child.move.assert_not_called()
        assert child.rotation_angle == 0.0
        child.update_image.assert_not_called()


# ============================================================
# toggle_image_animation_speed
# ============================================================
class TestToggleImageAnimationSpeed:
    def test_pause_animation(self):
        w = _make_image_window()
        w.config.animation_speed_factor = 1.0
        w.original_animation_speed_factor = 1.0
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_image_animation_speed()
        mock_prop.assert_called_with("animation_speed_factor", 0.0, "_update_animation_timer")

    def test_resume_animation(self):
        w = _make_image_window()
        w.config.animation_speed_factor = 0.0
        w.original_animation_speed_factor = 2.0
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.toggle_image_animation_speed()
        mock_prop.assert_called_with("animation_speed_factor", 2.0, "_update_animation_timer")


# ============================================================
# Action methods (reset/flip)
# ============================================================
class TestActionMethods:
    def test_reset_rotation(self):
        w = _make_image_window()
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.reset_rotation()
        mock_prop.assert_called_with("rotation_angle", 0.0, "update_image")

    def test_reset_opacity(self):
        w = _make_image_window()
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.reset_opacity()
        mock_prop.assert_called_with("opacity", 1.0, "update_image")

    def test_reset_image_size(self):
        w = _make_image_window()
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.reset_image_size()
        mock_prop.assert_called_with("scale_factor", 1.0, "update_image")

    def test_reset_animation_speed(self):
        w = _make_image_window()
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.reset_animation_speed()
        mock_prop.assert_called_with("animation_speed_factor", 1.0, "_update_animation_timer")

    def test_flip_horizontal_action(self):
        w = _make_image_window()
        w.config.flip_horizontal = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.flip_horizontal_action()
        mock_prop.assert_called_with("flip_horizontal", True, "update_image")

    def test_flip_vertical_action(self):
        w = _make_image_window()
        w.config.flip_vertical = False
        with patch.object(type(w), "set_undoable_property") as mock_prop:
            w.flip_vertical_action()
        mock_prop.assert_called_with("flip_vertical", True, "update_image")

    def test_next_frame(self):
        w = _make_image_window()
        w.frames = [MagicMock(), MagicMock(), MagicMock()]
        w.current_frame = 1
        with patch.object(type(w), "update_image"):
            w.next_frame()
        assert w.current_frame == 2

    def test_next_frame_wraps(self):
        w = _make_image_window()
        w.frames = [MagicMock(), MagicMock()]
        w.current_frame = 1
        with patch.object(type(w), "update_image"):
            w.next_frame()
        assert w.current_frame == 0

    def test_next_frame_empty(self):
        w = _make_image_window()
        w.frames = []
        w.next_frame()  # No crash
