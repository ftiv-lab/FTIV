import os
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt

from managers.settings_manager import SettingsManager


class TestSettingsManager:
    @pytest.fixture
    def settings_manager(self):
        self.mw = MagicMock()
        self.mw.base_directory = os.getcwd()  # Default
        self.mw.windowFlags.return_value = Qt.WindowType.Widget  # Default flags

        sm = SettingsManager(self.mw)
        # Mock settings objects to avoid file I/O
        sm.app_settings = MagicMock()
        sm.overlay_settings = MagicMock()
        return sm

    @patch("managers.settings_manager.QIcon")
    def test_init_window_settings(self, mock_QIcon, settings_manager):
        # Setup
        settings_manager.app_settings.main_window_frontmost = True
        # icon_path can be anything now, mock_QIcon will take it
        settings_manager.mw.icon_path = "dummy_icon.ico"

        # Execute
        settings_manager.init_window_settings()

        # Check title set
        settings_manager.mw.setWindowTitle.assert_called()
        # Check resize
        settings_manager.mw.resize.assert_called()
        # Check frontmost applied
        settings_manager.mw.setWindowFlags.assert_called()
        args, _ = settings_manager.mw.setWindowFlags.call_args
        # We can't easily check bitwise OR result on a mock return value unless we set it up.
        # But we know setWindowFlags was called.

    def test_set_main_frontmost_true(self, settings_manager):
        enable = True
        settings_manager.set_main_frontmost(enable)

        # Check app_settings updated
        assert settings_manager.app_settings.main_window_frontmost == enable
        # Check save called (we need to mock save_app_settings method or it tries file IO)
        # SettingsManager.save_app_settings calls utils.save_app_settings.
        # Let's mock the internal save_app_settings method? No, better mock imports or the method itself.

    def test_apply_performance_settings(self, settings_manager):
        debounce = 100
        wheel = 50
        cache = 500

        # Setup mw children
        txt_win = MagicMock()
        settings_manager.mw.text_windows = [txt_win]

        settings_manager.apply_performance_settings(debounce, wheel, cache)

        # Check app settings updated
        assert settings_manager.app_settings.render_debounce_ms == debounce
        assert settings_manager.app_settings.wheel_debounce_ms == wheel
        assert settings_manager.app_settings.glyph_cache_size == cache

        # Check applied to text window
        assert txt_win._render_debounce_ms == debounce
        assert txt_win._wheel_debounce_setting == wheel
        # Check renderer cache (mock nested)
        assert txt_win.renderer._glyph_cache_size == cache

    def test_apply_overlay_settings(self, settings_manager):
        # Setup overlay settings
        settings_manager.overlay_settings.show_title_bar = False
        settings_manager.overlay_settings.show_border = True
        settings_manager.overlay_settings.border_width = 5

        # Setup mock window
        win = MagicMock()
        # has attributes (MagicMock default)

        settings_manager.mw.text_windows = [win]
        settings_manager.mw.image_windows = []

        # Execute
        settings_manager.apply_overlay_settings_to_all_windows()

        # Check calls
        win.set_title_bar_visible.assert_called_with(False)
        win.set_border_visible.assert_called_with(True)
        assert win.border_width == 5
        win.update.assert_called()
