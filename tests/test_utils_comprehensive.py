# -*- coding: utf-8 -*-
"""utils/ 層の網羅テスト。

Sprint 1: version, paths, edition, error_reporter, translator,
app_settings, overlay_settings, logger, theme_manager のカバレッジ底上げ。
"""

import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# utils/version.py
# ============================================================
class TestAppVersion:
    """AppVersion dataclass のテスト。"""

    def test_version_fields_exist(self) -> None:
        from utils.version import APP_VERSION

        assert isinstance(APP_VERSION.name, str)
        assert isinstance(APP_VERSION.version, str)
        assert isinstance(APP_VERSION.data_format_version, int)

    def test_version_values(self) -> None:
        from utils.version import APP_VERSION

        assert APP_VERSION.name == "FTIV"
        assert APP_VERSION.data_format_version >= 1

    def test_version_is_frozen(self) -> None:
        from utils.version import APP_VERSION

        with pytest.raises(AttributeError):
            APP_VERSION.name = "changed"  # type: ignore[misc]

    def test_version_format(self) -> None:
        from utils.version import APP_VERSION

        parts = APP_VERSION.version.split(".")
        assert len(parts) == 3, "バージョンは x.y.z 形式であること"


# ============================================================
# utils/paths.py
# ============================================================
class TestPaths:
    """paths.py のパス解決テスト。"""

    def test_is_compiled_returns_false_in_dev(self) -> None:
        from utils.paths import is_compiled

        assert is_compiled() is False

    def test_get_base_dir_returns_project_root(self) -> None:
        from utils.paths import get_base_dir

        base = get_base_dir()
        assert os.path.isdir(base)
        # utils/ が存在するはず
        assert os.path.isdir(os.path.join(base, "utils"))

    def test_get_resources_dir_returns_valid_dir(self) -> None:
        from utils.paths import get_resources_dir

        res_dir = get_resources_dir()
        assert os.path.isdir(res_dir)

    def test_resolve_path_joins_correctly(self) -> None:
        from utils.paths import get_resources_dir, resolve_path

        result = resolve_path("some_file.txt")
        expected = os.path.join(get_resources_dir(), "some_file.txt")
        assert result == expected

    def test_get_base_dir_compiled_with_bin(self) -> None:
        """コンパイル済みexeが bin/ 配下にある場合のテスト。"""
        from utils.paths import get_base_dir

        with (
            patch("utils.paths.is_compiled", return_value=True),
            patch("sys.argv", [r"C:\App\bin\FTIV_Core.exe"]),
        ):
            result = get_base_dir()
            assert result == r"C:\App"

    def test_get_base_dir_compiled_no_bin(self) -> None:
        """コンパイル済みexeが直下にある場合のテスト。"""
        from utils.paths import get_base_dir

        with (
            patch("utils.paths.is_compiled", return_value=True),
            patch("sys.argv", [r"C:\App\FTIV_Core.exe"]),
        ):
            result = get_base_dir()
            assert result == r"C:\App"

    def test_get_resources_dir_compiled(self) -> None:
        from utils.paths import get_resources_dir

        with (
            patch("utils.paths.is_compiled", return_value=True),
            patch("sys.argv", [r"C:\App\FTIV_Core.exe"]),
        ):
            result = get_resources_dir()
            assert result == r"C:\App"


# ============================================================
# utils/edition.py
# ============================================================
class TestEdition:
    """edition.py のテスト。"""

    def test_get_edition_returns_standard(self) -> None:
        from utils.edition import Edition, get_edition

        assert get_edition() == Edition.STANDARD

    def test_get_limits_returns_large_values(self) -> None:
        from utils.edition import get_limits

        limits = get_limits()
        assert limits.max_text_windows >= 10**9
        assert limits.max_image_windows >= 10**9
        assert limits.max_save_slots >= 10**9

    def test_is_over_limit_true(self) -> None:
        from utils.edition import is_over_limit

        assert is_over_limit(10, 10) is True
        assert is_over_limit(11, 10) is True

    def test_is_over_limit_false(self) -> None:
        from utils.edition import is_over_limit

        assert is_over_limit(9, 10) is False

    def test_edition_enum_value(self) -> None:
        from utils.edition import Edition

        assert Edition.STANDARD.value == "standard"

    def test_limits_is_frozen(self) -> None:
        from utils.edition import Limits

        limits = Limits(max_text_windows=1, max_image_windows=1, max_save_slots=1)
        with pytest.raises(AttributeError):
            limits.max_text_windows = 2  # type: ignore[misc]

    def test_show_limit_message_suppressed(self) -> None:
        from utils.edition import show_limit_message

        # suppress=True の場合は QMessageBox を呼ばない
        show_limit_message(None, "msg_info", suppress=True)


# ============================================================
# utils/error_reporter.py
# ============================================================
class TestErrorReporter:
    """error_reporter.py のテスト。"""

    def test_error_notify_state_defaults(self) -> None:
        from utils.error_reporter import ErrorNotifyState

        state = ErrorNotifyState()
        assert state.last_signature == ""
        assert state.last_shown_ts_ms == 0

    def test_signature_generation(self) -> None:
        from utils.error_reporter import _signature

        exc = ValueError("test error")
        sig = _signature("save", exc)
        assert "save" in sig
        assert "ValueError" in sig
        assert "test error" in sig

    def test_report_logs_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        from utils.error_reporter import report_unexpected_error

        exc = RuntimeError("boom")
        with (
            caplog.at_level(logging.ERROR),
            patch("utils.error_reporter.QMessageBox"),
        ):
            report_unexpected_error(None, "test_op", exc)
        assert "boom" in caplog.text

    def test_report_with_cooldown_suppresses_duplicate(self) -> None:
        from utils.error_reporter import ErrorNotifyState, report_unexpected_error

        state = ErrorNotifyState()
        exc = RuntimeError("dup")

        with patch("utils.error_reporter.QMessageBox") as mock_box:
            # 1回目: 表示される
            report_unexpected_error(None, "op", exc, state=state)
            assert mock_box.critical.call_count == 1

            # 2回目: cooldown内なので抑制される
            report_unexpected_error(None, "op", exc, state=state)
            assert mock_box.critical.call_count == 1

    def test_report_without_state_always_shows(self) -> None:
        from utils.error_reporter import report_unexpected_error

        exc = RuntimeError("always")

        with patch("utils.error_reporter.QMessageBox") as mock_box:
            report_unexpected_error(None, "op", exc, state=None)
            report_unexpected_error(None, "op", exc, state=None)
            assert mock_box.critical.call_count == 2


# ============================================================
# utils/translator.py
# ============================================================
class TestTranslator:
    """translator.py のテスト。"""

    def test_tr_returns_string(self) -> None:
        from utils.translator import tr

        result = tr("msg_error")
        assert isinstance(result, str)

    def test_tr_missing_key_returns_key(self) -> None:
        from utils.translator import tr

        result = tr("__nonexistent_key_for_test__")
        assert result == "__nonexistent_key_for_test__"

    def test_set_lang_and_get_lang(self) -> None:
        from utils.translator import get_lang, set_lang

        original = get_lang()
        try:
            set_lang("en")
            assert get_lang() == "en"
            set_lang("jp")
            assert get_lang() == "jp"
        finally:
            set_lang(original)

    def test_set_lang_same_language_no_change(self) -> None:
        from utils.translator import _translator

        original = _translator.current_lang
        # 同じ言語を設定しても変化なし
        _translator.set_language(original)
        assert _translator.current_lang == original

    def test_translator_init_with_default(self) -> None:
        from utils.translator import Translator

        t = Translator(default_lang="en")
        assert t.current_lang == "en"

    def test_translator_loads_translations(self) -> None:
        from utils.translator import _translator

        # 少なくとも jp と en のエントリがあるはず
        assert "jp" in _translator.translations
        assert "en" in _translator.translations


# ============================================================
# utils/app_settings.py
# ============================================================
class TestAppSettings:
    """app_settings.py のテスト。"""

    def test_default_values(self) -> None:
        from utils.app_settings import AppSettings

        s = AppSettings()
        assert s.main_window_frontmost is True
        assert s.render_debounce_ms == 25
        assert s.wheel_debounce_ms == 50
        assert s.glyph_cache_size == 512
        assert s.info_view_presets == []
        assert s.info_last_view_preset_id == "builtin:all"

    def test_save_and_load_roundtrip(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.app_settings import AppSettings, load_app_settings, save_app_settings

        settings = AppSettings(
            main_window_frontmost=False,
            render_debounce_ms=100,
            wheel_debounce_ms=200,
            glyph_cache_size=1024,
            info_view_presets=[
                {
                    "id": "user:1",
                    "name": "My View",
                    "filters": {
                        "text": "abc",
                        "tag": "tag",
                        "starred_only": True,
                        "open_tasks_only": False,
                        "due_filter": "today",
                        "mode_filter": "task",
                        "sort_by": "due",
                        "sort_desc": False,
                    },
                }
            ],
            info_last_view_preset_id="user:1",
        )
        result = save_app_settings(None, str(tmp_path), settings)
        assert result is True

        loaded = load_app_settings(None, str(tmp_path))
        assert loaded.main_window_frontmost is False
        assert loaded.render_debounce_ms == 100
        assert loaded.wheel_debounce_ms == 200
        assert loaded.glyph_cache_size == 1024
        assert loaded.info_last_view_preset_id == "user:1"
        assert len(loaded.info_view_presets) == 1
        assert loaded.info_view_presets[0]["id"] == "user:1"

    def test_load_nonexistent_returns_default(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.app_settings import AppSettings, load_app_settings

        loaded = load_app_settings(None, str(tmp_path))
        default = AppSettings()
        assert loaded.main_window_frontmost == default.main_window_frontmost

    def test_load_corrupted_json_returns_default(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.app_settings import load_app_settings

        json_dir = os.path.join(str(tmp_path), "json")
        os.makedirs(json_dir)
        with open(os.path.join(json_dir, "app_settings.json"), "w") as f:
            f.write("{invalid json")

        with patch("utils.app_settings.QMessageBox"):
            loaded = load_app_settings(None, str(tmp_path))
        assert loaded.main_window_frontmost is True  # デフォルト

    def test_load_invalid_info_presets_skips_bad_entries(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.app_settings import load_app_settings

        json_dir = os.path.join(str(tmp_path), "json")
        os.makedirs(json_dir)
        data = {
            "info_view_presets": [
                {"id": "builtin:all", "name": "bad", "filters": {}},
                {"id": "user:1", "name": "ok", "filters": {"due_filter": "today"}},
                {"id": "user:1", "name": "dup", "filters": {"due_filter": "overdue"}},
                {"id": "", "name": "empty", "filters": {}},
                "invalid",
            ],
            "info_last_view_preset_id": "user:1",
        }
        with open(os.path.join(json_dir, "app_settings.json"), "w", encoding="utf-8") as f:
            json.dump(data, f)

        loaded = load_app_settings(None, str(tmp_path))
        assert loaded.info_last_view_preset_id == "user:1"
        assert len(loaded.info_view_presets) == 1
        assert loaded.info_view_presets[0]["id"] == "user:1"

    def test_get_settings_path_empty_base(self) -> None:
        from utils.app_settings import _get_settings_path

        path = _get_settings_path("")
        assert path.endswith("app_settings.json")


# ============================================================
# utils/overlay_settings.py
# ============================================================
class TestOverlaySettings:
    """overlay_settings.py のテスト。"""

    def test_default_values(self) -> None:
        from utils.overlay_settings import OverlaySettings

        s = OverlaySettings()
        assert s.selection_frame_enabled is True
        assert isinstance(s.selection_frame_color, str)
        assert s.selection_frame_width == 4

    def test_save_and_load_roundtrip(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.overlay_settings import (
            OverlaySettings,
            load_overlay_settings,
            save_overlay_settings,
        )

        settings = OverlaySettings(
            selection_frame_enabled=False,
            selection_frame_color="#FF0000FF",
            selection_frame_width=8,
        )
        result = save_overlay_settings(None, str(tmp_path), settings)
        assert result is True

        loaded = load_overlay_settings(None, str(tmp_path))
        assert loaded.selection_frame_enabled is False
        assert loaded.selection_frame_color == "#FF0000FF"
        assert loaded.selection_frame_width == 8

    def test_load_nonexistent_returns_default(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.overlay_settings import OverlaySettings, load_overlay_settings

        loaded = load_overlay_settings(None, str(tmp_path))
        default = OverlaySettings()
        assert loaded.selection_frame_enabled == default.selection_frame_enabled

    def test_load_corrupted_json_returns_default(self, tmp_path: pytest.TempPathFactory) -> None:
        from utils.overlay_settings import load_overlay_settings

        json_dir = os.path.join(str(tmp_path), "json")
        os.makedirs(json_dir)
        with open(os.path.join(json_dir, "overlay_settings.json"), "w") as f:
            f.write("not valid json!")

        with patch("utils.overlay_settings.QMessageBox"):
            loaded = load_overlay_settings(None, str(tmp_path))
        assert loaded.selection_frame_enabled is True  # デフォルト

    def test_get_settings_path_empty_base(self) -> None:
        from utils.overlay_settings import _get_settings_path

        path = _get_settings_path("")
        assert path.endswith("overlay_settings.json")


# ============================================================
# utils/logger.py
# ============================================================
class TestLogger:
    """logger.py のテスト。"""

    def test_get_logger_returns_logger(self) -> None:
        from utils.logger import get_logger

        lg = get_logger("test_module")
        assert isinstance(lg, logging.Logger)
        assert lg.name == "test_module"

    def test_log_diagnostics_runs(self, caplog: pytest.LogCaptureFixture) -> None:
        from utils.logger import log_diagnostics

        with caplog.at_level(logging.INFO):
            log_diagnostics()
        assert "Python:" in caplog.text
        assert "OS:" in caplog.text

    def test_handle_exception_keyboard_interrupt(self) -> None:
        """KeyboardInterruptは通常のexcepthookに委譲される。"""
        from utils.logger import handle_exception

        with patch("sys.__excepthook__") as mock_hook:
            handle_exception(KeyboardInterrupt, KeyboardInterrupt(), None)
            mock_hook.assert_called_once()

    def test_handle_exception_logs_critical(self, caplog: pytest.LogCaptureFixture) -> None:
        from utils.logger import handle_exception

        try:
            raise ValueError("test crash")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        with (
            caplog.at_level(logging.CRITICAL),
            patch("utils.logger.QMessageBox"),
        ):
            handle_exception(exc_info[0], exc_info[1], exc_info[2])
        assert "test crash" in caplog.text


# ============================================================
# utils/theme_manager.py (utils/)
# ============================================================
class TestUtilsThemeManager:
    """utils/theme_manager.py のテスト。"""

    def test_default_palette_has_keys(self) -> None:
        from utils.theme_manager import ThemeManager

        assert "@bg_primary" in ThemeManager.DEFAULT_PALETTE
        assert "@accent_primary" in ThemeManager.DEFAULT_PALETTE
        assert "@danger" in ThemeManager.DEFAULT_PALETTE

    def test_process_template_replaces_variables(self) -> None:
        from utils.theme_manager import ThemeManager

        template = "background: @bg_primary; color: @text_primary;"
        result = ThemeManager._process_template(template)
        assert "@bg_primary" not in result
        assert "@text_primary" not in result
        assert "#f0f0f0" in result
        assert "#333333" in result

    def test_process_template_preserves_non_variables(self) -> None:
        from utils.theme_manager import ThemeManager

        template = "border: 1px solid black;"
        result = ThemeManager._process_template(template)
        assert result == template

    def test_load_theme_missing_template(self, qapp: MagicMock) -> None:
        from utils.theme_manager import ThemeManager

        with patch("utils.theme_manager.get_base_dir", return_value="/nonexistent"):
            ThemeManager.load_theme(MagicMock())
            # テンプレートが見つからなくてもクラッシュしない


# ============================================================
# utils/commands.py
# ============================================================
class TestPropertyChangeCommand:
    """PropertyChangeCommand の undo/redo テスト。"""

    def test_redo_sets_new_value(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        target.my_prop = "old"
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = True
            cmd = PropertyChangeCommand(target, "my_prop", "old", "new")
            cmd.redo()
        assert target.my_prop == "new"

    def test_undo_restores_old_value(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        target.my_prop = "new"
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = True
            cmd = PropertyChangeCommand(target, "my_prop", "old", "new")
            cmd.undo()
        assert target.my_prop == "old"

    def test_redo_with_invalid_target_is_noop(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = False
            cmd = PropertyChangeCommand(target, "my_prop", "old", "new")
            cmd.redo()
        # setattr は呼ばれないので元のmock状態のまま

    def test_undo_with_invalid_target_is_noop(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = False
            cmd = PropertyChangeCommand(target, "my_prop", "old", "new")
            cmd.undo()

    def test_update_calls_custom_method(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        target.custom_update = MagicMock()
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = True
            cmd = PropertyChangeCommand(target, "x", 1, 2, update_method_name="custom_update")
            cmd.redo()
        target.custom_update.assert_called_once()

    def test_text_description(self) -> None:
        from utils.commands import PropertyChangeCommand

        target = MagicMock()
        with patch("utils.commands.shiboken6"):
            cmd = PropertyChangeCommand(target, "scale", 1.0, 2.0)
        assert cmd.text() == "Change scale"


class TestMoveWindowCommand:
    """MoveWindowCommand の undo/redo テスト。"""

    def test_redo_moves_to_new_pos(self) -> None:
        from PySide6.QtCore import QPoint

        from utils.commands import MoveWindowCommand

        target = MagicMock()
        target.uuid = "test-uuid"
        old_pos = QPoint(0, 0)
        new_pos = QPoint(100, 200)
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = True
            cmd = MoveWindowCommand(target, old_pos, new_pos)
            cmd.redo()
        target.move.assert_called_with(new_pos)

    def test_undo_moves_to_old_pos(self) -> None:
        from PySide6.QtCore import QPoint

        from utils.commands import MoveWindowCommand

        target = MagicMock()
        target.uuid = "test-uuid"
        old_pos = QPoint(0, 0)
        new_pos = QPoint(100, 200)
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = True
            cmd = MoveWindowCommand(target, old_pos, new_pos)
            cmd.undo()
        target.move.assert_called_with(old_pos)

    def test_redo_with_invalid_target(self) -> None:
        from PySide6.QtCore import QPoint

        from utils.commands import MoveWindowCommand

        target = MagicMock()
        with patch("utils.commands.shiboken6") as mock_shib:
            mock_shib.isValid.return_value = False
            cmd = MoveWindowCommand(target, QPoint(0, 0), QPoint(1, 1))
            cmd.redo()
        target.move.assert_not_called()

    def test_text_with_uuid(self) -> None:
        from PySide6.QtCore import QPoint

        from utils.commands import MoveWindowCommand

        target = MagicMock()
        target.uuid = "abc-123"
        with patch("utils.commands.shiboken6"):
            cmd = MoveWindowCommand(target, QPoint(0, 0), QPoint(1, 1))
        assert "abc-123" in cmd.text()

    def test_text_without_uuid(self) -> None:
        from PySide6.QtCore import QPoint

        from utils.commands import MoveWindowCommand

        target = MagicMock(spec=[])  # uuid属性なし
        with patch("utils.commands.shiboken6"):
            cmd = MoveWindowCommand(target, QPoint(0, 0), QPoint(1, 1))
        assert "Window" in cmd.text()
