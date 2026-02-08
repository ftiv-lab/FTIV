# -*- coding: utf-8 -*-
"""WindowManager の拡張テスト (Sprint 2).

ウィンドウ生成/削除の実コードはQtに深く結合しているため、
初期化、プロパティ、prune、基本的なデータ操作に集中。
"""

from unittest.mock import MagicMock, patch

import pytest

from managers.window_manager import WindowManager


@pytest.fixture
def mock_mw(qapp):
    """軽量MainWindow Mock."""
    mw = MagicMock()
    mw.base_directory = "/tmp"
    mw.json_directory = "/tmp/json"
    return mw


@pytest.fixture
def wm(mock_mw):
    return WindowManager(mock_mw)


class TestWindowManagerInit:
    def test_init_empty_lists(self, wm):
        assert wm.text_windows == []
        assert wm.image_windows == []
        assert wm.connectors == []

    def test_init_no_selection(self, wm):
        assert wm.last_selected_window is None


class TestAllWindows:
    def test_empty(self, wm):
        assert wm.all_windows == []

    def test_combined(self, wm):
        tw = MagicMock()
        iw = MagicMock()
        wm.text_windows = [tw]
        wm.image_windows = [iw]
        result = wm.all_windows
        assert tw in result
        assert iw in result
        assert len(result) == 2


class TestPruneInvalidRefs:
    """_prune_invalid_refsのテスト。

    shiboken6はメソッド内でローカルimportされるため、
    builtins.__import__ をパッチして制御する。
    """

    def test_prune_removes_none(self, wm):
        valid_mock = MagicMock()
        wm.text_windows = [None, valid_mock]

        mock_shib = MagicMock()
        mock_shib.isValid.return_value = True
        with patch.dict("sys.modules", {"shiboken6": mock_shib}):
            wm._prune_invalid_refs()
        assert len(wm.text_windows) == 1
        assert None not in wm.text_windows

    def test_prune_removes_invalid_objects(self, wm):
        valid = MagicMock()
        invalid = MagicMock()
        wm.text_windows = [valid, invalid]

        mock_shib = MagicMock()
        mock_shib.isValid.side_effect = lambda w: w is valid
        with patch.dict("sys.modules", {"shiboken6": mock_shib}):
            wm._prune_invalid_refs()
        assert wm.text_windows == [valid]

    def test_prune_image_windows(self, wm):
        valid = MagicMock()
        wm.image_windows = [valid, None]

        mock_shib = MagicMock()
        mock_shib.isValid.return_value = True
        with patch.dict("sys.modules", {"shiboken6": mock_shib}):
            wm._prune_invalid_refs()
        assert len(wm.image_windows) == 1

    def test_prune_connectors_with_dead_endpoints(self, wm):
        conn = MagicMock()
        conn.start_window = None
        conn.end_window = MagicMock()
        wm.connectors = [conn]

        mock_shib = MagicMock()
        mock_shib.isValid.return_value = True
        with patch.dict("sys.modules", {"shiboken6": mock_shib}):
            wm._prune_invalid_refs()
        assert len(wm.connectors) == 0

    def test_prune_keeps_valid_connectors(self, wm):
        conn = MagicMock()
        conn.start_window = MagicMock()
        conn.end_window = MagicMock()
        wm.connectors = [conn]

        mock_shib = MagicMock()
        mock_shib.isValid.return_value = True
        with patch.dict("sys.modules", {"shiboken6": mock_shib}):
            wm._prune_invalid_refs()
        assert len(wm.connectors) == 1


class TestSignals:
    def test_selection_changed_signal_exists(self, wm):
        assert hasattr(wm, "sig_selection_changed")

    def test_status_message_signal_exists(self, wm):
        assert hasattr(wm, "sig_status_message")

    def test_undo_command_signal_exists(self, wm):
        assert hasattr(wm, "sig_undo_command_requested")
