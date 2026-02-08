# -*- coding: utf-8 -*-
"""ConnectorLine / ConnectorLabel の計算・状態ロジックテスト (Sprint 4).

get_edge_point, calculate_path_in_global, set_line_color, _begin_delete,
is_label_visible, set_label_visible をカバー。
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QColor

from models.enums import AnchorPosition, ArrowStyle


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------
def _make_connector_line(**overrides):
    """ConnectorLine を __init__ なしで作成。"""
    from windows.connector import ConnectorLine

    with patch.object(ConnectorLine, "__init__", lambda self, *a, **kw: None):
        obj = ConnectorLine.__new__(ConnectorLine)
    obj.start_window = MagicMock()
    obj.end_window = MagicMock()
    obj.line_color = QColor(100, 200, 255, 180)
    obj.line_width = 2
    obj.pen_style = MagicMock()
    obj.arrow_style = ArrowStyle.NONE
    obj.arrow_size = 15
    obj.is_selected = False
    obj.label_window = None
    obj.main_window = MagicMock()
    obj._label_forced_hidden = False
    obj._deleted = False
    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


def _make_mock_rect_window(x, y, w, h, anchor=AnchorPosition.AUTO):
    """geometry() が QRect を返す mock window を作る。"""
    win = MagicMock()
    rect = QRect(x, y, w, h)
    win.geometry.return_value = rect
    win.anchor_position = anchor
    return win


# ============================================================
# get_edge_point
# ============================================================
class TestGetEdgePoint:
    def test_auto_right_direction(self):
        """ターゲットが右にある場合、右辺上の点を返す。"""
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100)
        target = QPointF(500, 50)  # 右方向
        point = conn.get_edge_point(win, target)
        assert isinstance(point, QPointF)
        # 右辺: x=200
        assert point.x() == pytest.approx(200.0, abs=1.0)

    def test_auto_left_direction(self):
        """ターゲットが左にある場合、左辺上の点を返す。"""
        conn = _make_connector_line()
        win = _make_mock_rect_window(200, 0, 200, 100)
        target = QPointF(0, 50)  # 左方向
        point = conn.get_edge_point(win, target)
        # 左辺: x=200
        assert point.x() == pytest.approx(200.0, abs=1.0)

    def test_auto_bottom_direction(self):
        """ターゲットが下にある場合、下辺上の点を返す。"""
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100)
        target = QPointF(100, 500)  # 真下
        point = conn.get_edge_point(win, target)
        # 下辺: y=100
        assert point.y() == pytest.approx(100.0, abs=1.0)

    def test_auto_same_center(self):
        """ターゲットがウィンドウ中心と同じ場合。"""
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100)
        # QRect(0,0,200,100).center() → (99, 49) in Qt integer math
        rect = QRect(0, 0, 200, 100)
        cx, cy = rect.center().x(), rect.center().y()
        center = QPointF(cx, cy)
        point = conn.get_edge_point(win, center)
        assert point.x() == pytest.approx(float(cx), abs=1.0)
        assert point.y() == pytest.approx(float(cy), abs=1.0)

    def test_anchor_top(self):
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100, AnchorPosition.TOP)
        point = conn.get_edge_point(win, QPointF(300, 300))
        rect = QRect(0, 0, 200, 100)
        assert point.x() == pytest.approx(float(rect.center().x()), abs=1.0)
        assert point.y() == pytest.approx(0.0, abs=1.0)  # top

    def test_anchor_bottom(self):
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100, AnchorPosition.BOTTOM)
        point = conn.get_edge_point(win, QPointF(300, 300))
        rect = QRect(0, 0, 200, 100)
        assert point.x() == pytest.approx(float(rect.center().x()), abs=1.0)
        assert point.y() == pytest.approx(float(rect.bottom()), abs=1.0)

    def test_anchor_left(self):
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100, AnchorPosition.LEFT)
        point = conn.get_edge_point(win, QPointF(300, 300))
        rect = QRect(0, 0, 200, 100)
        assert point.x() == pytest.approx(0.0, abs=1.0)
        assert point.y() == pytest.approx(float(rect.center().y()), abs=1.0)

    def test_anchor_right(self):
        conn = _make_connector_line()
        win = _make_mock_rect_window(0, 0, 200, 100, AnchorPosition.RIGHT)
        point = conn.get_edge_point(win, QPointF(300, 300))
        rect = QRect(0, 0, 200, 100)
        assert point.x() == pytest.approx(float(rect.right()), abs=1.0)
        assert point.y() == pytest.approx(float(rect.center().y()), abs=1.0)


# ============================================================
# calculate_path_in_global
# ============================================================
class TestCalculatePathInGlobal:
    def test_returns_path(self):
        conn = _make_connector_line()
        conn.start_window = _make_mock_rect_window(0, 0, 200, 100)
        conn.end_window = _make_mock_rect_window(400, 0, 200, 100)
        path = conn.calculate_path_in_global()
        # path should be a QPainterPath
        from PySide6.QtGui import QPainterPath

        assert isinstance(path, QPainterPath)

    def test_path_has_elements(self):
        conn = _make_connector_line()
        conn.start_window = _make_mock_rect_window(0, 0, 200, 100)
        conn.end_window = _make_mock_rect_window(400, 0, 200, 100)
        path = conn.calculate_path_in_global()
        assert path.elementCount() > 0


# ============================================================
# set_line_color
# ============================================================
class TestSetLineColor:
    def test_set_valid_qcolor(self):
        conn = _make_connector_line()
        color = QColor(255, 0, 0)
        with patch.object(type(conn), "update"):
            conn.set_line_color(color)
        assert conn.line_color.red() == 255

    def test_set_color_from_string(self):
        conn = _make_connector_line()
        with patch.object(type(conn), "update"):
            conn.set_line_color("#FF0000")
        assert conn.line_color.red() == 255

    def test_set_invalid_color_noop(self):
        conn = _make_connector_line()
        QColor(conn.line_color)
        with patch.object(type(conn), "update") as mock_upd:
            conn.set_line_color("not_a_color")
        mock_upd.assert_not_called()

    def test_set_argb_string(self):
        conn = _make_connector_line()
        with patch.object(type(conn), "update"):
            conn.set_line_color("#80FF0000")
        assert conn.line_color.alpha() == 128
        assert conn.line_color.red() == 255


# ============================================================
# set_line_style / set_arrow_style
# ============================================================
class TestSetStyles:
    def test_set_line_style(self):
        conn = _make_connector_line()
        style = MagicMock()
        with patch.object(type(conn), "update"):
            conn.set_line_style(style)
        assert conn.pen_style is style

    def test_set_arrow_style(self):
        conn = _make_connector_line()
        with patch.object(type(conn), "update_position"):
            conn.set_arrow_style(ArrowStyle.END)
        assert conn.arrow_style == ArrowStyle.END


# ============================================================
# _begin_delete
# ============================================================
class TestBeginDelete:
    def test_first_call_returns_true(self):
        conn = _make_connector_line()
        conn._deleted = False
        assert conn._begin_delete() is True
        assert conn._deleted is True

    def test_second_call_returns_false(self):
        conn = _make_connector_line()
        conn._deleted = False
        conn._begin_delete()
        assert conn._begin_delete() is False

    def test_already_deleted(self):
        conn = _make_connector_line()
        conn._deleted = True
        assert conn._begin_delete() is False


# ============================================================
# is_label_visible
# ============================================================
class TestIsLabelVisible:
    def test_no_label_window(self):
        conn = _make_connector_line()
        conn.label_window = None
        assert conn.is_label_visible() is False

    def test_label_forced_hidden(self):
        conn = _make_connector_line()
        conn.label_window = MagicMock()
        conn._label_forced_hidden = True
        assert conn.is_label_visible() is False

    def test_label_visible(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.isHidden.return_value = False
        conn.label_window = lw
        conn._label_forced_hidden = False
        assert conn.is_label_visible() is True

    def test_label_hidden_widget(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.isHidden.return_value = True
        conn.label_window = lw
        conn._label_forced_hidden = False
        assert conn.is_label_visible() is False


# ============================================================
# set_label_visible
# ============================================================
class TestSetLabelVisible:
    def test_no_label_window_noop(self):
        conn = _make_connector_line()
        conn.label_window = None
        conn.set_label_visible(True)  # No crash

    def test_hide_label(self):
        conn = _make_connector_line()
        lw = MagicMock()
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.set_label_visible(False)
        assert conn._label_forced_hidden is True
        lw.hide_action.assert_called_once()

    def test_show_label_with_text(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = "Hello"
        lw.isHidden.return_value = True
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.set_label_visible(True)
        assert conn._label_forced_hidden is False
        lw.show.assert_called()
        lw.raise_.assert_called()

    def test_show_label_empty_text_edits(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = ""
        lw.isHidden.return_value = True
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.set_label_visible(True)
        lw.show.assert_called()
        lw.edit_text_realtime.assert_called()

    def test_show_label_whitespace_text_edits(self):
        conn = _make_connector_line()
        lw = MagicMock()
        lw.text = "   "
        lw.isHidden.return_value = False
        conn.label_window = lw
        with patch.object(type(conn), "update_position"):
            conn.set_label_visible(True)
        lw.edit_text_realtime.assert_called()


# ============================================================
# set_selected
# ============================================================
class TestSetSelected:
    def test_sets_is_selected(self):
        conn = _make_connector_line()
        lw = MagicMock()
        conn.label_window = lw
        with patch.object(type(conn), "update"):
            conn.set_selected(True)
        assert conn.is_selected is True
        lw.set_selected.assert_called_with(True)

    def test_no_label_window(self):
        conn = _make_connector_line()
        conn.label_window = None
        with patch.object(type(conn), "update"):
            conn.set_selected(False)
        assert conn.is_selected is False
