# -*- coding: utf-8 -*-
"""BaseOverlayWindow の計算・状態ロジックテスト (Sprint 4).

QLabel.__init__ をバイパスし、計算メソッド・プロパティアクセサに集中する。
"""

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEasingCurve, QPoint

from models.enums import AnchorPosition
from models.window_config import WindowConfigBase


# ------------------------------------------------------------------
# ヘルパー: QLabel.__init__ を完全にスキップして属性だけ注入
# ------------------------------------------------------------------
def _make_base_window(**overrides):
    """BaseOverlayWindowのインスタンスを __init__ なしで作成する。"""
    from windows.base_window import BaseOverlayWindow

    with patch.object(BaseOverlayWindow, "__init__", lambda self, *a, **kw: None):
        obj = BaseOverlayWindow.__new__(BaseOverlayWindow)
    obj.config = WindowConfigBase()
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
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# Property Accessors (Config ラッパー)
# ============================================================
class TestPropertyAccessors:
    def test_uuid_get_set(self):
        w = _make_base_window()
        w.uuid = "test-uuid-123"
        assert w.uuid == "test-uuid-123"
        assert w.config.uuid == "test-uuid-123"

    def test_parent_window_uuid_get_set(self):
        w = _make_base_window()
        w.parent_window_uuid = "parent-1"
        assert w.parent_window_uuid == "parent-1"
        assert w.config.parent_uuid == "parent-1"

    def test_parent_window_uuid_none(self):
        w = _make_base_window()
        w.parent_window_uuid = None
        assert w.parent_window_uuid is None

    def test_anchor_position_get_set(self):
        w = _make_base_window()
        line = MagicMock()
        w.connected_lines = [line]
        w.anchor_position = AnchorPosition.TOP
        assert w.anchor_position == AnchorPosition.TOP
        line.update_position.assert_called_once()

    def test_is_hidden_get_set(self):
        w = _make_base_window()
        w.is_hidden = True
        assert w.is_hidden is True
        assert w.config.is_hidden is True

    def test_is_click_through_get_set(self):
        w = _make_base_window()
        with patch.object(type(w), "set_click_through", lambda self, v: None):
            w.is_click_through = True
        assert w.config.is_click_through is True

    def test_is_locked_get_set(self):
        w = _make_base_window()
        w.is_locked = True
        assert w.is_locked is True

    def test_is_locked_default_false(self):
        w = _make_base_window()
        assert w.is_locked is False

    def test_is_locked_exception_returns_false(self):
        w = _make_base_window()
        # configが壊れている場合のフォールバック
        w.config = MagicMock()
        w.config.is_locked = property(lambda self: (_ for _ in ()).throw(RuntimeError))
        del w.config.is_locked
        assert w.is_locked is False

    def test_move_loop_enabled_get_set(self):
        w = _make_base_window()
        w.move_loop_enabled = True
        assert w.move_loop_enabled is True

    def test_move_position_only_enabled_get_set(self):
        w = _make_base_window()
        w.move_position_only_enabled = True
        assert w.move_position_only_enabled is True

    def test_move_speed_get_set(self):
        w = _make_base_window()
        w.move_speed = 5000
        assert w.move_speed == 5000

    def test_move_pause_time_get_set(self):
        w = _make_base_window()
        w.move_pause_time = 300
        assert w.move_pause_time == 300

    def test_start_position_get_set(self):
        w = _make_base_window()
        w.start_position = QPoint(100, 200)
        sp = w.start_position
        assert sp.x() == 100
        assert sp.y() == 200

    def test_start_position_none(self):
        w = _make_base_window()
        w.start_position = None
        assert w.start_position is None

    def test_end_position_get_set(self):
        w = _make_base_window()
        w.end_position = QPoint(300, 400)
        ep = w.end_position
        assert ep.x() == 300
        assert ep.y() == 400

    def test_end_position_none(self):
        w = _make_base_window()
        w.end_position = None
        assert w.end_position is None

    def test_is_fading_enabled_get_set(self):
        w = _make_base_window()
        w.is_fading_enabled = True
        assert w.is_fading_enabled is True

    def test_fade_in_only_loop_enabled(self):
        w = _make_base_window()
        w.fade_in_only_loop_enabled = True
        assert w.fade_in_only_loop_enabled is True

    def test_fade_out_only_loop_enabled(self):
        w = _make_base_window()
        w.fade_out_only_loop_enabled = True
        assert w.fade_out_only_loop_enabled is True

    def test_fade_speed_get_set(self):
        w = _make_base_window()
        w.fade_speed = 2000
        assert w.fade_speed == 2000

    def test_fade_pause_time_get_set(self):
        w = _make_base_window()
        w.fade_pause_time = 500
        assert w.fade_pause_time == 500


# ============================================================
# get_move_offset / set_move_offset / _is_zero_offset
# ============================================================
class TestMoveOffset:
    def test_get_move_offset_empty_config(self):
        w = _make_base_window()
        # move_offset defaults to {"x": 0, "y": 0}; test via getattr fallback
        w.config.move_offset = {"x": 0, "y": 0}
        offset = w.get_move_offset()
        assert offset.x() == 0
        assert offset.y() == 0

    def test_get_move_offset_with_values(self):
        w = _make_base_window()
        w.config.move_offset = {"x": 50, "y": -30}
        offset = w.get_move_offset()
        assert offset.x() == 50
        assert offset.y() == -30

    def test_set_move_offset(self):
        w = _make_base_window()
        w.set_move_offset(QPoint(100, 200))
        assert w.config.move_offset == {"x": 100, "y": 200}

    def test_is_zero_offset_true(self):
        w = _make_base_window()
        assert w._is_zero_offset(QPoint(0, 0)) is True

    def test_is_zero_offset_false(self):
        w = _make_base_window()
        assert w._is_zero_offset(QPoint(1, 0)) is False
        assert w._is_zero_offset(QPoint(0, 1)) is False


# ============================================================
# record_absolute / relative positions
# ============================================================
class TestPositionRecording:
    def test_record_absolute_start_pos(self):
        w = _make_base_window()
        with patch.object(type(w), "pos", return_value=QPoint(10, 20)):
            with patch.object(type(w), "_emit_status_warning"):
                w.record_absolute_start_pos()
        assert w.config.move_use_relative is False
        assert w.config.start_position == {"x": 10, "y": 20}

    def test_record_absolute_end_pos(self):
        w = _make_base_window()
        with patch.object(type(w), "pos", return_value=QPoint(30, 40)):
            with patch.object(type(w), "_emit_status_warning"):
                w.record_absolute_end_pos()
        assert w.config.move_use_relative is False
        assert w.config.end_position == {"x": 30, "y": 40}

    def test_record_relative_move_base(self):
        w = _make_base_window()
        with patch.object(type(w), "pos", return_value=QPoint(5, 10)):
            with patch.object(type(w), "_emit_status_warning"):
                w.record_relative_move_base()
        assert w._rel_record_base_pos == QPoint(5, 10)

    def test_record_relative_move_end_as_offset(self):
        w = _make_base_window()
        w._rel_record_base_pos = QPoint(10, 20)
        w._rel_move_anim = None
        w._rel_base_pos = None
        w._rel_direction = 1
        with patch.object(type(w), "pos", return_value=QPoint(60, 80)):
            with patch.object(type(w), "_emit_status_warning"):
                w.record_relative_move_end_as_offset()
        assert w.config.move_use_relative is True
        assert w.config.move_offset == {"x": 50, "y": 60}
        assert w._rel_record_base_pos is None

    def test_record_relative_end_no_base(self):
        w = _make_base_window()
        w._rel_record_base_pos = None
        w._rel_move_anim = None
        w._rel_base_pos = None
        w._rel_direction = 1
        with patch.object(type(w), "_emit_status_warning") as mock_warn:
            w.record_relative_move_end_as_offset()
        mock_warn.assert_called()

    def test_clear_relative_move_offset(self):
        w = _make_base_window()
        w.config.move_offset = {"x": 99, "y": 99}
        with patch.object(type(w), "_emit_status_warning"):
            w.clear_relative_move_offset()
        assert w.config.move_use_relative is True
        assert w.config.move_offset == {"x": 0, "y": 0}


# ============================================================
# _easing_name_from_type / _apply_easing_from_config
# ============================================================
class TestEasing:
    def test_easing_name_from_type_linear(self):
        w = _make_base_window()
        assert w._easing_name_from_type(QEasingCurve.Type.Linear) == "Linear"

    def test_easing_name_from_type_in_quad(self):
        w = _make_base_window()
        assert w._easing_name_from_type(QEasingCurve.Type.InQuad) == "InQuad"

    def test_easing_name_from_type_invalid(self):
        w = _make_base_window()
        result = w._easing_name_from_type(9999)
        # Should fallback to "Linear" or return a valid name
        assert isinstance(result, str)

    def test_apply_easing_from_config_default(self):
        w = _make_base_window()
        w._apply_easing_from_config()
        assert w.easing_curve == QEasingCurve.Type.Linear
        assert w.fade_easing_curve == QEasingCurve.Type.Linear

    def test_apply_easing_from_config_custom(self):
        w = _make_base_window()
        w.config.move_easing = "OutBounce"
        w.config.fade_easing = "InExpo"
        w._apply_easing_from_config()
        assert w.easing_curve == QEasingCurve.Type.OutBounce
        assert w.fade_easing_curve == QEasingCurve.Type.InExpo

    def test_apply_easing_from_config_invalid_fallback(self):
        w = _make_base_window()
        w.config.move_easing = "NonExistentCurve"
        w._apply_easing_from_config()
        assert w.easing_curve == QEasingCurve.Type.Linear


# ============================================================
# _ensure_relative_move_state
# ============================================================
class TestEnsureRelativeMoveState:
    def test_creates_missing_attributes(self):
        w = _make_base_window()
        w._ensure_relative_move_state()
        assert w._rel_move_anim is None
        assert w._rel_base_pos is None
        assert w._rel_direction == 1
        assert w._rel_record_base_pos is None

    def test_preserves_existing_attributes(self):
        w = _make_base_window()
        w._rel_move_anim = "existing"
        w._rel_direction = -1
        w._ensure_relative_move_state()
        assert w._rel_move_anim == "existing"
        assert w._rel_direction == -1


# ============================================================
# _get_easing_curve_names
# ============================================================
class TestGetEasingCurveNames:
    def test_returns_dict(self):
        w = _make_base_window()
        names = w._get_easing_curve_names()
        assert isinstance(names, dict)
        assert "Linear" in names
        assert "OutBounce" in names
        assert names["Linear"] == QEasingCurve.Type.Linear

    def test_has_many_curves(self):
        w = _make_base_window()
        names = w._get_easing_curve_names()
        assert len(names) >= 30


# ============================================================
# Child window management
# ============================================================
class TestChildWindowManagement:
    def test_add_child_window(self):
        parent = _make_base_window()
        child = MagicMock()
        child.parent_window_uuid = None
        child._contains_in_subtree.return_value = False  # 循環チェック: 非循環
        parent.add_child_window(child)
        assert child in parent.child_windows
        assert child.parent_window_uuid == parent.uuid

    def test_add_child_window_self_not_added(self):
        w = _make_base_window()
        w.add_child_window(w)
        assert w not in w.child_windows

    def test_add_child_window_duplicate(self):
        parent = _make_base_window()
        child = MagicMock()
        child._contains_in_subtree.return_value = False  # 循環チェック: 非循環
        parent.add_child_window(child)
        parent.add_child_window(child)
        assert parent.child_windows.count(child) == 1

    def test_remove_child_window(self):
        parent = _make_base_window()
        child = MagicMock()
        parent.child_windows = [child]
        parent.remove_child_window(child)
        assert child not in parent.child_windows
        assert child.parent_window_uuid is None

    def test_remove_child_window_not_in_list(self):
        parent = _make_base_window()
        child = MagicMock()
        parent.remove_child_window(child)  # No crash


# ============================================================
# _emit_status_warning
# ============================================================
class TestEmitStatusWarning:
    def test_uses_main_window_show_status(self):
        w = _make_base_window()
        w.main_window.show_status_message = MagicMock()
        w._emit_status_warning("test_key", fallback_text="fallback")
        w.main_window.show_status_message.assert_called_once()

    def test_fallback_when_no_show_status(self):
        w = _make_base_window()
        w.main_window = MagicMock(spec=[])
        w._emit_status_warning("test_key", fallback_text="fallback")
        # Should not crash


# ============================================================
# _shift_relative_move_base_by_delta
# ============================================================
class TestShiftRelativeMoveBase:
    def test_shifts_base_pos(self):
        w = _make_base_window()
        w._rel_move_anim = None
        w._rel_base_pos = QPoint(100, 200)
        w._rel_direction = 1
        w._rel_record_base_pos = None
        w._shift_relative_move_base_by_delta(QPoint(10, -5))
        assert w._rel_base_pos == QPoint(110, 195)

    def test_noop_when_no_base_pos(self):
        w = _make_base_window()
        w._rel_move_anim = None
        w._rel_base_pos = None
        w._rel_direction = 1
        w._rel_record_base_pos = None
        w._shift_relative_move_base_by_delta(QPoint(10, 10))
        assert w._rel_base_pos is None


# ============================================================
# _clear_absolute_move_fields
# ============================================================
class TestClearAbsoluteMoveFields:
    def test_clears_positions(self):
        w = _make_base_window()
        w.config.start_position = {"x": 1, "y": 2}
        w.config.end_position = {"x": 3, "y": 4}
        w._clear_absolute_move_fields()
        assert w.config.start_position is None
        assert w.config.end_position is None


# ============================================================
# stop_all_animations
# ============================================================
class TestStopAllAnimations:
    def test_calls_stop_animation_five_types(self):
        w = _make_base_window()
        with patch.object(type(w), "stop_animation") as mock_stop:
            w.stop_all_animations()
        assert mock_stop.call_count == 5


# ============================================================
# set_selected
# ============================================================
class TestSetSelected:
    def test_sets_is_selected(self):
        w = _make_base_window()
        with patch.object(type(w), "update"):
            w.set_selected(True)
        assert w.is_selected is True

    def test_unsets_is_selected(self):
        w = _make_base_window()
        w.is_selected = True
        with patch.object(type(w), "update"):
            w.set_selected(False)
        assert w.is_selected is False
