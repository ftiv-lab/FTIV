# -*- coding: utf-8 -*-
"""SettingsManager の未カバーパス拡張テスト (Sprint 2)."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QRect

from managers.settings_manager import SettingsManager
from utils.app_settings import AppSettings
from utils.overlay_settings import OverlaySettings


@pytest.fixture
def mock_mw(tmp_path):
    """軽量MainWindow Mock with temp base directory."""
    mw = MagicMock()
    mw.base_directory = str(tmp_path)
    mw.json_directory = str(tmp_path / "json")
    mw.text_windows = []
    mw.image_windows = []
    mw.connectors = []
    mw.windowFlags.return_value = 0
    mw.width.return_value = 420
    mw.height.return_value = 640
    mw.x.return_value = 12
    mw.y.return_value = 24
    return mw


@pytest.fixture
def manager(mock_mw):
    return SettingsManager(mock_mw)


class TestSettingsManagerInit:
    def test_init_stores_main_window(self, manager, mock_mw):
        assert manager.mw is mock_mw

    def test_init_settings_are_none(self, manager):
        assert manager.app_settings is None
        assert manager.overlay_settings is None


class TestLoadSettings:
    def test_load_settings_populates_both(self, manager):
        with (
            patch("managers.settings_manager.load_app_settings") as mock_app,
            patch("managers.settings_manager.load_overlay_settings") as mock_overlay,
        ):
            mock_app.return_value = AppSettings()
            mock_overlay.return_value = OverlaySettings()
            manager.load_settings()
        assert manager.app_settings is not None
        assert manager.overlay_settings is not None


class TestSaveSettings:
    def test_save_app_settings_calls_util(self, manager):
        manager.app_settings = AppSettings()
        with patch("managers.settings_manager.save_app_settings") as mock_save:
            manager.save_app_settings()
            mock_save.assert_called_once()

    def test_save_app_settings_noop_when_none(self, manager):
        manager.app_settings = None
        with patch("managers.settings_manager.save_app_settings") as mock_save:
            manager.save_app_settings()
            mock_save.assert_not_called()

    def test_save_overlay_settings_calls_util(self, manager):
        manager.overlay_settings = OverlaySettings()
        with patch("managers.settings_manager.save_overlay_settings") as mock_save:
            manager.save_overlay_settings()
            mock_save.assert_called_once()

    def test_save_overlay_settings_noop_when_none(self, manager):
        manager.overlay_settings = None
        with patch("managers.settings_manager.save_overlay_settings") as mock_save:
            manager.save_overlay_settings()
            mock_save.assert_not_called()


class TestTextArchetype:
    def test_load_archetype_returns_empty_when_no_file(self, manager):
        result = manager.load_text_archetype()
        assert result == {}

    def test_save_and_load_archetype_roundtrip(self, manager):
        data = {"font": "Arial", "font_size": 24}
        assert manager.save_text_archetype(data) is True
        loaded = manager.load_text_archetype()
        assert loaded["font"] == "Arial"
        assert loaded["font_size"] == 24

    def test_load_archetype_corrupted_returns_empty(self, manager, tmp_path):
        json_dir = tmp_path / "json"
        json_dir.mkdir(exist_ok=True)
        (json_dir / "text_archetype.json").write_text("{broken")
        result = manager.load_text_archetype()
        assert result == {}


class TestInitWindowSettings:
    def test_applies_title_and_size(self, manager, mock_mw):
        manager.app_settings = AppSettings(main_window_frontmost=False)
        mock_mw.icon_path = "/nonexistent/icon.png"
        manager.init_window_settings()
        mock_mw.setWindowTitle.assert_called_once()
        mock_mw.resize.assert_called_once()
        width, height = mock_mw.resize.call_args.args
        assert int(width) >= 320
        assert int(height) >= 600

    def test_applies_frontmost_flag(self, manager, mock_mw):
        manager.app_settings = AppSettings(main_window_frontmost=True)
        mock_mw.icon_path = "/nonexistent/icon.png"
        manager.init_window_settings()
        mock_mw.setWindowFlags.assert_called()
        mock_mw.show.assert_called()

    def test_applies_saved_geometry_when_available(self, manager, mock_mw):
        manager.app_settings = AppSettings(
            main_window_frontmost=False,
            main_window_width=480,
            main_window_height=700,
            main_window_pos_x=100,
            main_window_pos_y=120,
        )
        mock_mw.icon_path = "/nonexistent/icon.png"
        with patch.object(manager, "_safe_available_geometry", return_value=QRect(0, 0, 1920, 1080)):
            manager.init_window_settings()
        mock_mw.resize.assert_called_once_with(480, 700)
        mock_mw.move.assert_called_once_with(100, 120)

    def test_save_main_window_geometry_updates_app_settings(self, manager, mock_mw):
        manager.app_settings = AppSettings()
        with patch.object(manager, "save_app_settings") as mock_save:
            manager.save_main_window_geometry()
        assert manager.app_settings.main_window_width == 420
        assert manager.app_settings.main_window_height == 640
        assert manager.app_settings.main_window_pos_x == 12
        assert manager.app_settings.main_window_pos_y == 24
        mock_save.assert_called_once()


class TestSetMainFrontmost:
    def test_set_frontmost_true(self, manager, mock_mw):
        manager.app_settings = AppSettings()
        with patch("managers.settings_manager.save_app_settings"):
            manager.set_main_frontmost(True)
        mock_mw.setWindowFlags.assert_called()
        mock_mw.show.assert_called()

    def test_set_frontmost_saves_setting(self, manager, mock_mw):
        manager.app_settings = AppSettings()
        with patch("managers.settings_manager.save_app_settings") as mock_save:
            manager.set_main_frontmost(False)
        assert manager.app_settings.main_window_frontmost is False
        mock_save.assert_called_once()


class TestApplyPerformanceSettings:
    def test_applies_to_app_settings(self, manager, mock_mw):
        manager.app_settings = AppSettings()
        mock_mw.text_windows = []
        mock_mw.connectors = []
        with patch("managers.settings_manager.save_app_settings"):
            manager.apply_performance_settings(50, 100, 256)
        assert manager.app_settings.render_debounce_ms == 50
        assert manager.app_settings.wheel_debounce_ms == 100
        assert manager.app_settings.glyph_cache_size == 256

    def test_applies_to_text_windows(self, manager, mock_mw):
        tw = MagicMock()
        tw._render_debounce_ms = 25
        tw._wheel_debounce_setting = 50
        tw.renderer._glyph_cache_size = 512
        mock_mw.text_windows = [tw]
        mock_mw.connectors = []
        manager.app_settings = AppSettings()
        with patch("managers.settings_manager.save_app_settings"):
            manager.apply_performance_settings(100, 200, 1024)
        assert tw._render_debounce_ms == 100
        assert tw._wheel_debounce_setting == 200

    def test_noop_when_no_app_settings(self, manager, mock_mw):
        manager.app_settings = None
        mock_mw.text_windows = []
        mock_mw.connectors = []
        # Should not crash
        manager.apply_performance_settings(50, 100, 256)


class TestApplyOverlaySettings:
    def test_noop_when_no_overlay_settings(self, manager):
        manager.overlay_settings = None
        manager.apply_overlay_settings_to_all_windows()

    def test_applies_to_all_windows(self, manager, mock_mw):
        tw = MagicMock()
        iw = MagicMock()
        mock_mw.text_windows = [tw]
        mock_mw.image_windows = [iw]
        manager.overlay_settings = OverlaySettings()
        manager.apply_overlay_settings_to_all_windows()
        # update should be called on both
        tw.update.assert_called()
        iw.update.assert_called()

    def test_skips_none_windows(self, manager, mock_mw):
        mock_mw.text_windows = [None]
        mock_mw.image_windows = []
        manager.overlay_settings = OverlaySettings()
        # Should not crash on None
        manager.apply_overlay_settings_to_all_windows()
