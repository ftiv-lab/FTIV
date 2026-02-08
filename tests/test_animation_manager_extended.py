# -*- coding: utf-8 -*-
"""AnimationManager のテスト (Sprint 2).

UI同期部分 (sync_from_selected のUI操作) はスコープ外。
get_target_windows, _get_anim_tab, _get_ui_widget, apply/clear_offset をカバー。
"""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint

from managers.animation_manager import AnimationManager


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.last_selected_window = None
    mw.text_windows = []
    mw.image_windows = []
    mw.connectors = []
    mw.animation_tab = MagicMock()
    return mw


@pytest.fixture
def am(mock_mw):
    return AnimationManager(mock_mw)


class TestGetAnimTab:
    def test_returns_tab_when_exists(self, am, mock_mw):
        tab = am._get_anim_tab()
        assert tab is mock_mw.animation_tab

    def test_returns_none_when_missing(self, am, mock_mw):
        del mock_mw.animation_tab
        tab = am._get_anim_tab()
        assert tab is None


class TestGetUiWidget:
    def test_returns_from_tab(self, am, mock_mw):
        mock_mw.animation_tab.my_widget = "from_tab"
        result = am._get_ui_widget("my_widget")
        assert result == "from_tab"

    def test_fallback_to_mw(self, am, mock_mw):
        mock_mw.animation_tab = MagicMock(spec=[])  # tabにmy_widgetなし
        mock_mw.my_widget = "from_mw"
        result = am._get_ui_widget("my_widget")
        assert result == "from_mw"

    def test_returns_none_when_missing(self, am, mock_mw):
        # tabにもmwにも属性がない場合はNone
        tab = MagicMock(spec=[])  # 空のspec
        mock_mw.animation_tab = tab
        # mock_mwからもhasattrでFalseを返すようにspec制限
        mock_mw_limited = MagicMock(spec=["animation_tab"])
        mock_mw_limited.animation_tab = tab
        am_limited = AnimationManager(mock_mw_limited)
        result = am_limited._get_ui_widget("nonexistent_widget")
        assert result is None


class TestGetTargetWindows:
    def test_idx0_selected_returns_selected(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 0
        mock_mw.animation_tab.anim_target_combo = combo
        selected_window = MagicMock()
        mock_mw.last_selected_window = selected_window
        result = am.get_target_windows()
        assert result == [selected_window]

    def test_idx0_no_selection_returns_empty(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 0
        mock_mw.animation_tab.anim_target_combo = combo
        mock_mw.last_selected_window = None
        result = am.get_target_windows()
        assert result == []

    def test_idx1_returns_all_text(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 1
        mock_mw.animation_tab.anim_target_combo = combo
        tw1 = MagicMock()
        tw2 = MagicMock()
        mock_mw.text_windows = [tw1, tw2]
        mock_mw.connectors = []
        result = am.get_target_windows()
        assert tw1 in result
        assert tw2 in result

    def test_idx1_includes_connector_labels(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 1
        mock_mw.animation_tab.anim_target_combo = combo
        mock_mw.text_windows = []
        conn = MagicMock()
        label = MagicMock()
        conn.label_window = label
        mock_mw.connectors = [conn]
        result = am.get_target_windows()
        assert label in result

    def test_idx2_returns_all_image(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 2
        mock_mw.animation_tab.anim_target_combo = combo
        iw = MagicMock()
        mock_mw.image_windows = [iw]
        result = am.get_target_windows()
        assert result == [iw]

    def test_idx3_returns_all_windows(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 3
        mock_mw.animation_tab.anim_target_combo = combo
        tw = MagicMock()
        iw = MagicMock()
        mock_mw.text_windows = [tw]
        mock_mw.image_windows = [iw]
        mock_mw.connectors = []
        result = am.get_target_windows()
        assert tw in result
        assert iw in result

    def test_deduplicates_results(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 3
        mock_mw.animation_tab.anim_target_combo = combo
        same_window = MagicMock()
        mock_mw.text_windows = [same_window, same_window]
        mock_mw.image_windows = []
        mock_mw.connectors = []
        result = am.get_target_windows()
        assert len(result) == 1

    def test_filters_none_windows(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 3
        mock_mw.animation_tab.anim_target_combo = combo
        mock_mw.text_windows = [None, MagicMock()]
        mock_mw.image_windows = []
        mock_mw.connectors = []
        result = am.get_target_windows()
        assert None not in result
        assert len(result) == 1


class TestSyncFromSelected:
    def test_none_window_is_noop(self, am):
        am.sync_from_selected(None)  # クラッシュしない

    def test_calls_with_valid_window(self, am, mock_mw):
        window = MagicMock()
        window.get_move_offset.return_value = QPoint(10, 20)
        window.move_speed = 100
        window.move_pause_time = 500
        window.fade_speed = 200
        window.fade_pause_time = 300
        window.config = MagicMock()
        window.config.move_easing = "Linear"
        window.config.move_use_relative = True
        window.config.fade_easing = "Linear"
        window.move_loop_enabled = False
        window.move_position_only_enabled = False
        window.is_fading_enabled = False
        window.fade_in_only_loop_enabled = False
        window.fade_out_only_loop_enabled = False

        # UIウィジェットをMock
        for name in [
            "anim_dx",
            "anim_dy",
            "anim_base_status",
            "anim_move_speed",
            "anim_abs_move_speed",
            "anim_move_pause",
            "anim_abs_move_pause",
            "anim_move_easing_combo",
            "anim_abs_easing_combo",
            "anim_btn_pingpong",
            "anim_btn_oneway",
            "anim_btn_abs_pingpong",
            "anim_btn_abs_oneway",
            "anim_fade_speed",
            "anim_fade_pause",
            "anim_fade_easing_combo",
            "anim_btn_fade_in_out",
            "anim_btn_fade_in_only",
            "anim_btn_fade_out_only",
        ]:
            widget = MagicMock()
            widget.findText.return_value = 0
            setattr(mock_mw.animation_tab, name, widget)

        am.sync_from_selected(window)
        # クラッシュなく完了すればOK


class TestApplyOffset:
    def test_apply_offset_sets_relative(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 0
        mock_mw.animation_tab.anim_target_combo = combo
        anim_dx = MagicMock()
        anim_dx.value.return_value = 50
        anim_dy = MagicMock()
        anim_dy.value.return_value = 100
        mock_mw.animation_tab.anim_dx = anim_dx
        mock_mw.animation_tab.anim_dy = anim_dy

        window = MagicMock()
        window.config = MagicMock()
        mock_mw.last_selected_window = window

        am.apply_offset()
        assert window.config.move_use_relative is True
        window.set_move_offset.assert_called_once_with(QPoint(50, 100))


class TestClearOffset:
    def test_clear_offset_calls_clear(self, am, mock_mw):
        combo = MagicMock()
        combo.currentIndex.return_value = 0
        mock_mw.animation_tab.anim_target_combo = combo

        window = MagicMock()
        mock_mw.last_selected_window = window

        am.clear_offset()
        window.clear_relative_move_offset.assert_called_once()
