# -*- coding: utf-8 -*-
"""TextRenderer の計算ロジックテスト (Sprint 4).

影パディング、ぼかし半径、プロファイリング、キャッシュキー生成をカバー。
"""

import json
from unittest.mock import MagicMock

from PySide6.QtCore import QSize

from windows.text_renderer import TextRenderer, _RenderProfile


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------
def _make_mock_window(**overrides):
    """TextRenderer が参照する window mock を作る。"""
    w = MagicMock()
    w.shadow_enabled = True
    w.shadow_blur = 50  # 50%
    w.shadow_offset_x = 0.05
    w.shadow_offset_y = 0.05
    w.font_size = 24
    w.text = "Hello"
    w.is_vertical = False
    w.task_states = []
    for k, v in overrides.items():
        setattr(w, k, v)
    return w


# ============================================================
# _RenderProfile
# ============================================================
class TestRenderProfile:
    def test_add_accumulates(self):
        p = _RenderProfile()
        p.add("draw", 5.0)
        p.add("draw", 3.0)
        assert p.parts_ms["draw"] == 8.0

    def test_inc_accumulates(self):
        p = _RenderProfile()
        p.inc("glyphs", 10)
        p.inc("glyphs", 5)
        assert p.counts["glyphs"] == 15

    def test_add_new_key(self):
        p = _RenderProfile()
        p.add("new_part", 1.5)
        assert p.parts_ms["new_part"] == 1.5

    def test_inc_default_one(self):
        p = _RenderProfile()
        p.inc("calls")
        assert p.counts["calls"] == 1


# ============================================================
# set_profiling
# ============================================================
class TestSetProfiling:
    def test_enable_profiling(self):
        r = TextRenderer()
        r.set_profiling(True, warn_ms=32.0)
        assert r._profile_enabled is True
        assert r._profile_warn_ms == 32.0

    def test_disable_profiling(self):
        r = TextRenderer()
        r.set_profiling(True)
        r.set_profiling(False)
        assert r._profile_enabled is False

    def test_invalid_warn_ms_fallback(self):
        r = TextRenderer()
        r.set_profiling(True, warn_ms="not_a_number")
        assert r._profile_warn_ms == 16.0


# ============================================================
# _prof_add / _prof_inc
# ============================================================
class TestProfAddInc:
    def test_prof_add_with_active_profile(self):
        r = TextRenderer()
        r._active_profile = _RenderProfile()
        r._prof_add("step1", 5.0)
        assert r._active_profile.parts_ms["step1"] == 5.0

    def test_prof_add_no_active_profile(self):
        r = TextRenderer()
        r._active_profile = None
        r._prof_add("step1", 5.0)  # No crash

    def test_prof_inc_with_active_profile(self):
        r = TextRenderer()
        r._active_profile = _RenderProfile()
        r._prof_inc("chars", 3)
        assert r._active_profile.counts["chars"] == 3

    def test_prof_inc_no_active_profile(self):
        r = TextRenderer()
        r._active_profile = None
        r._prof_inc("chars", 3)  # No crash


# ============================================================
# _get_blur_radius_px
# ============================================================
class TestGetBlurRadiusPx:
    def test_shadow_enabled(self):
        r = TextRenderer()
        w = _make_mock_window(shadow_blur=50)
        result = r._get_blur_radius_px(w)
        # 50 * 20.0 / 100.0 = 10.0
        assert result == 10.0

    def test_shadow_disabled(self):
        r = TextRenderer()
        w = _make_mock_window(shadow_enabled=False)
        result = r._get_blur_radius_px(w)
        assert result == 0.0

    def test_shadow_blur_zero(self):
        r = TextRenderer()
        w = _make_mock_window(shadow_blur=0)
        result = r._get_blur_radius_px(w)
        assert result == 0.0

    def test_shadow_blur_100(self):
        r = TextRenderer()
        w = _make_mock_window(shadow_blur=100)
        result = r._get_blur_radius_px(w)
        assert result == 20.0


# ============================================================
# _calculate_shadow_padding
# ============================================================
class TestCalculateShadowPadding:
    def test_shadow_disabled_zero_padding(self):
        r = TextRenderer()
        w = _make_mock_window(shadow_enabled=False)
        assert r._calculate_shadow_padding(w) == (0, 0, 0, 0)

    def test_zero_offset_symmetric(self):
        r = TextRenderer()
        w = _make_mock_window(
            shadow_offset_x=0.0,
            shadow_offset_y=0.0,
            shadow_blur=50,
            font_size=20,
        )
        left, top, right, bottom = r._calculate_shadow_padding(w)
        # blur_px = 50 * 20 / 100 = 10.0
        # sx = 20 * 0.0 = 0, sy = 20 * 0.0 = 0
        # pad_left = max(0, -(0-10)) = 10
        # pad_top = max(0, -(0-10)) = 10
        # pad_right = max(0, (0+10)) = 10
        # pad_bottom = max(0, (0+10)) = 10
        assert left == 10
        assert top == 10
        assert right == 10
        assert bottom == 10

    def test_positive_offset(self):
        r = TextRenderer()
        w = _make_mock_window(
            shadow_offset_x=0.5,  # → sx = 24*0.5 = 12
            shadow_offset_y=0.25,  # → sy = 24*0.25 = 6
            shadow_blur=50,  # → blur_px = 10.0
            font_size=24,
        )
        left, top, right, bottom = r._calculate_shadow_padding(w)
        # pad_left = max(0, -(12-10)) = 0
        # pad_top = max(0, -(6-10)) = 4
        # pad_right = max(0, 12+10) = 22
        # pad_bottom = max(0, 6+10) = 16
        assert left == 0
        assert top == 4
        assert right == 22
        assert bottom == 16

    def test_negative_offset(self):
        r = TextRenderer()
        w = _make_mock_window(
            shadow_offset_x=-0.5,  # → sx = 24*(-0.5) = -12
            shadow_offset_y=-0.25,  # → sy = 24*(-0.25) = -6
            shadow_blur=50,
            font_size=24,
        )
        left, top, right, bottom = r._calculate_shadow_padding(w)
        # pad_left = max(0, -(-12-10)) = max(0, 22) = 22
        # pad_top = max(0, -(-6-10)) = max(0, 16) = 16
        # pad_right = max(0, -12+10) = 0
        # pad_bottom = max(0, -6+10) = 4
        assert left == 22
        assert top == 16
        assert right == 0
        assert bottom == 4


# ============================================================
# _make_render_cache_key
# ============================================================
class TestMakeRenderCacheKey:
    def test_returns_string(self):
        r = TextRenderer()
        w = _make_mock_window()
        w.config = MagicMock()
        w.config.model_dump.return_value = {"font_size": 24, "text": "Hello"}
        key = r._make_render_cache_key(w)
        assert isinstance(key, str)

    def test_excludes_position_fields(self):
        r = TextRenderer()
        w = _make_mock_window()
        w.config = MagicMock()
        w.config.model_dump.return_value = {"font_size": 24}
        r._make_render_cache_key(w)
        w.config.model_dump.assert_called_once_with(mode="json", exclude={"uuid", "parent_uuid", "position"})

    def test_includes_type_name(self):
        r = TextRenderer()
        w = _make_mock_window()
        w.config = MagicMock()
        w.config.model_dump.return_value = {}
        key = r._make_render_cache_key(w)
        parsed = json.loads(key)
        assert parsed["extra"]["_type"] == "MagicMock"

    def test_no_config_fallback(self):
        r = TextRenderer()
        w = MagicMock(spec=[])
        key = r._make_render_cache_key(w)
        assert isinstance(key, str)

    def test_config_without_model_dump(self):
        r = TextRenderer()
        w = _make_mock_window()
        w.config = "not_a_pydantic_model"
        key = r._make_render_cache_key(w)
        assert isinstance(key, str)
        # Should still produce a valid key (maybe JSON with empty cfg)
        parsed = json.loads(key)
        assert parsed["cfg"] == {}

    def test_different_configs_different_keys(self):
        r = TextRenderer()
        w1 = _make_mock_window()
        w1.config = MagicMock()
        w1.config.model_dump.return_value = {"font_size": 24}
        w2 = _make_mock_window()
        w2.config = MagicMock()
        w2.config.model_dump.return_value = {"font_size": 36}
        assert r._make_render_cache_key(w1) != r._make_render_cache_key(w2)


# ============================================================
# _render_cache_put
# ============================================================
class TestRenderCachePut:
    def test_stores_pixmap(self):
        r = TextRenderer()
        r._render_cache_size = 10
        pix = MagicMock()
        r._render_cache_put("key1", pix)
        assert r._render_cache["key1"] is pix

    def test_evicts_oldest(self):
        r = TextRenderer()
        r._render_cache_size = 2
        r._render_cache_put("k1", MagicMock())
        r._render_cache_put("k2", MagicMock())
        r._render_cache_put("k3", MagicMock())
        assert "k1" not in r._render_cache
        assert "k2" in r._render_cache
        assert "k3" in r._render_cache

    def test_disabled_cache(self):
        r = TextRenderer()
        r._render_cache_size = 0
        r._render_cache_put("k1", MagicMock())
        assert len(r._render_cache) == 0


# ============================================================
# task mode rendering helpers
# ============================================================
class TestTaskRendering:
    def test_build_render_lines_note_mode_keeps_text(self):
        r = TextRenderer()
        w = _make_mock_window(text="[x] done\nplain", content_mode="note")
        lines, done_flags = r._build_render_lines(w)
        assert lines == ["[x] done", "plain"]
        assert done_flags == [False, False]

    def test_build_render_lines_task_mode_uses_task_states_and_keeps_text(self):
        r = TextRenderer()
        w = _make_mock_window(text="done\ntodo\nplain", content_mode="task", task_states=[True, False, True])
        lines, done_flags = r._build_render_lines(w)
        assert lines == ["done", "todo", "plain"]
        assert done_flags == [True, False, True]

    def test_horizontal_task_strike_flow_called(self):
        r = TextRenderer()
        painter = MagicMock()
        painter.font.return_value = MagicMock()
        fm = MagicMock()
        fm.ascent.return_value = 10
        fm.height.return_value = 20
        fm.horizontalAdvance.side_effect = lambda ch: 10
        w = _make_mock_window(
            content_mode="task",
            shadow_enabled=False,
            third_outline_enabled=False,
            second_outline_enabled=False,
            outline_enabled=False,
            font_color="#ffffff",
            text_opacity=100,
            text_gradient_enabled=False,
            text_gradient=[],
        )

        r._draw_horizontal_text_content = MagicMock()  # type: ignore[assignment]
        r._draw_horizontal_task_checkboxes = MagicMock()  # type: ignore[assignment]
        r._draw_horizontal_task_strike = MagicMock()  # type: ignore[assignment]

        r._draw_horizontal_text_elements(
            painter=painter,
            window=w,
            canvas_size=QSize(200, 80),
            lines=["done"],
            fm=fm,
            shadow_offset_x=0,
            shadow_offset_y=0,
            margin_left=0,
            margin_top=0,
            margin=0,
            outline_width=1.0,
            line_spacing=0,
            done_flags=[True],
        )

        r._draw_horizontal_task_checkboxes.assert_called_once()  # type: ignore[union-attr]
        r._draw_horizontal_task_strike.assert_called_once()  # type: ignore[union-attr]
        call_kwargs = r._draw_horizontal_task_checkboxes.call_args.kwargs  # type: ignore[union-attr]
        assert float(call_kwargs["start_x"]) > 1.0

    def test_vertical_task_marker_flow_not_called_when_vertical(self):
        r = TextRenderer()
        painter = MagicMock()
        painter.font.return_value = MagicMock()
        w = _make_mock_window(
            content_mode="task",
            is_vertical=True,
            shadow_enabled=False,
            third_outline_enabled=False,
            second_outline_enabled=False,
            outline_enabled=False,
            font_color="#ffffff",
            text_opacity=100,
            text_gradient_enabled=False,
            text_gradient=[],
            font_family="Arial",
        )

        r._draw_vertical_text_content = MagicMock()  # type: ignore[assignment]
        r._draw_vertical_task_completion_marker = MagicMock()  # type: ignore[assignment]

        r._draw_vertical_text_elements(
            painter=painter,
            window=w,
            canvas_size=QSize(200, 200),
            lines=["☑ done"],
            top_margin=4,
            margin=0,
            right_margin=0,
            shadow_x=0,
            shadow_y=0,
            outline_width=1.0,
            line_spacing_ratio=0.0,
            col_width=30.0,
            done_flags=[True, False],
        )

        r._draw_vertical_task_completion_marker.assert_not_called()  # type: ignore[union-attr]

    def test_get_task_line_rects_vertical_returns_empty(self):
        r = TextRenderer()
        w = _make_mock_window(content_mode="task", is_vertical=True, text="a\nb", task_states=[True, False])
        assert r.get_task_line_rects(w) == []

    def test_get_task_line_rects_horizontal_uses_task_rail(self):
        r = TextRenderer()
        fm = MagicMock()
        fm.horizontalAdvance.side_effect = lambda ch: {"☐": 12, " ": 6}.get(ch, 10)
        fm.height.return_value = 20

        w = _make_mock_window(
            content_mode="task",
            is_vertical=False,
            font_size=24,
            margin_top_ratio=0.0,
            margin_left_ratio=0.0,
            background_outline_enabled=False,
            background_outline_width_ratio=0.0,
            shadow_enabled=False,
            line_spacing_h=0.0,
        )

        rects = r._get_task_line_rects_horizontal(w, ["task line"], fm)
        rail_width, _marker_width, _gap, _pad = r._get_task_rail_metrics(w, fm)

        assert len(rects) == 1
        assert rects[0].width() == rail_width
        # rail starts at left margin + outline width (outline min=1)
        assert rects[0].x() == 1


# ============================================================
# __init__ defaults
# ============================================================
class TestInit:
    def test_default_cache_sizes(self):
        r = TextRenderer()
        assert r._blur_cache_size >= 0
        assert r._render_cache_size >= 0
        assert r._profile_enabled is False

    def test_custom_blur_cache_size(self):
        r = TextRenderer(blur_cache_size=5)
        assert r._blur_cache_size == 5

    def test_negative_blur_cache_size_clamped(self):
        r = TextRenderer(blur_cache_size=-10)
        assert r._blur_cache_size == 0
