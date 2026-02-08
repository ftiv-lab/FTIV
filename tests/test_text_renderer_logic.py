# -*- coding: utf-8 -*-
"""TextRenderer の計算ロジックテスト (Sprint 4).

影パディング、ぼかし半径、プロファイリング、キャッシュキー生成をカバー。
"""

import json
from unittest.mock import MagicMock

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
