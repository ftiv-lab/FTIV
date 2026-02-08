# -*- coding: utf-8 -*-
"""MainController の拡張テスト (Sprint 3).

全プロパティアクセサ・イベントハンドリング・タブ更新ロジックをカバー。
"""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from ui.controllers.main_controller import MainController


@pytest.fixture
def mock_mw():
    mw = MagicMock()
    mw.is_property_panel_active = True
    mw.property_panel = MagicMock()
    mw.animation_tab = MagicMock()
    mw.image_tab = MagicMock()
    mw.text_tab = MagicMock()
    mw.connections_tab = MagicMock()
    mw.general_tab = MagicMock()
    mw.layout_actions = MagicMock()
    mw.scene_actions = MagicMock()
    mw.img_actions = MagicMock()
    mw.conn_actions = MagicMock()
    mw.txt_actions = MagicMock()
    mw.bulk_manager = MagicMock()
    return mw


@pytest.fixture
def mock_wm():
    wm = MagicMock()
    wm.last_selected_window = None
    return wm


@pytest.fixture
def mc(mock_mw, mock_wm):
    return MainController(mock_mw, mock_wm)


class TestInit:
    def test_stores_references(self, mc, mock_mw, mock_wm):
        assert mc.view is mock_mw
        assert mc.model is mock_wm


class TestPropertyAccessors:
    def test_layout_actions(self, mc, mock_mw):
        assert mc.layout_actions is mock_mw.layout_actions

    def test_scene_actions(self, mc, mock_mw):
        assert mc.scene_actions is mock_mw.scene_actions

    def test_image_actions(self, mc, mock_mw):
        assert mc.image_actions is mock_mw.img_actions

    def test_connector_actions(self, mc, mock_mw):
        assert mc.connector_actions is mock_mw.conn_actions

    def test_txt_actions(self, mc, mock_mw):
        assert mc.txt_actions is mock_mw.txt_actions

    def test_bulk_manager(self, mc, mock_mw):
        assert mc.bulk_manager is mock_mw.bulk_manager

    def test_missing_attribute_returns_none(self):
        mw = MagicMock(spec=["property_panel"])
        wm = MagicMock()
        mc = MainController(mw, wm)
        assert mc.layout_actions is None
        assert mc.scene_actions is None
        assert mc.image_actions is None
        assert mc.connector_actions is None
        assert mc.txt_actions is None
        assert mc.bulk_manager is None


class TestSetupConnections:
    def test_connects_signal(self, mc, mock_wm):
        mc.setup_connections()
        mock_wm.sig_selection_changed.connect.assert_called_once_with(mc._on_selection_changed)


class TestOnSelectionChanged:
    def test_with_window_active_panel(self, mc, mock_mw):
        w = MagicMock()
        mock_mw.is_property_panel_active = True
        mc._on_selection_changed(w)
        mock_mw.property_panel.set_target.assert_called_with(w)
        mock_mw.property_panel.show.assert_called()
        mock_mw.property_panel.raise_.assert_called()

    def test_none_hides_panel(self, mc, mock_mw):
        mock_mw.is_property_panel_active = False
        mc._on_selection_changed(None)
        mock_mw.property_panel.set_target.assert_called_with(None)
        mock_mw.property_panel.hide.assert_called()

    def test_none_with_active_panel_no_hide(self, mc, mock_mw):
        mock_mw.is_property_panel_active = True
        mc._on_selection_changed(None)
        mock_mw.property_panel.set_target.assert_called_with(None)

    def test_updates_all_tabs(self, mc, mock_mw):
        w = MagicMock()
        mc._on_selection_changed(w)
        mock_mw.animation_tab.on_selection_changed.assert_called_with(w)
        mock_mw.image_tab.on_selection_changed.assert_called_with(w)
        mock_mw.text_tab.on_selection_changed.assert_called_with(w)
        mock_mw.connections_tab.on_selection_changed.assert_called_with(w)

    def test_no_property_panel(self):
        mw = MagicMock(spec=["animation_tab", "image_tab", "text_tab", "connections_tab"])
        mw.animation_tab = MagicMock()
        mw.image_tab = MagicMock()
        mw.text_tab = MagicMock()
        mw.connections_tab = MagicMock()
        wm = MagicMock()
        mc = MainController(mw, wm)
        mc._on_selection_changed(MagicMock())  # Should not crash


class TestUpdateTabState:
    def test_calls_on_selection_changed(self, mc, mock_mw):
        w = MagicMock()
        mc._update_tab_state("animation_tab", w)
        mock_mw.animation_tab.on_selection_changed.assert_called_with(w)

    def test_noop_if_no_tab(self, mc):
        mw = MagicMock(spec=[])
        wm = MagicMock()
        mc_limited = MainController(mw, wm)
        mc_limited._update_tab_state("nonexistent_tab", MagicMock())

    def test_noop_if_tab_lacks_method(self, mc, mock_mw):
        mock_mw.some_tab = MagicMock(spec=[])
        mc._update_tab_state("some_tab", MagicMock())  # No crash


class TestHandleAppStateChange:
    def test_inactive_deselects(self, mc, mock_wm):
        mock_wm.last_selected_window = MagicMock()
        mc.handle_app_state_change(Qt.ApplicationState.ApplicationInactive)
        mock_wm.set_selected_window.assert_called_once_with(None)

    def test_active_does_nothing(self, mc, mock_wm):
        mc.handle_app_state_change(Qt.ApplicationState.ApplicationActive)
        mock_wm.set_selected_window.assert_not_called()

    def test_inactive_no_selection_is_noop(self, mc, mock_wm):
        mock_wm.last_selected_window = None
        mc.handle_app_state_change(Qt.ApplicationState.ApplicationInactive)
        mock_wm.set_selected_window.assert_not_called()


class TestRequestPropertyPanel:
    def test_activates_panel(self, mc, mock_mw, mock_wm):
        mock_mw.is_property_panel_active = False
        w = MagicMock()
        mc.request_property_panel(w)
        assert mock_mw.is_property_panel_active is True
        mock_wm.set_selected_window.assert_called_once_with(w)

    def test_updates_tab_buttons(self, mc, mock_mw, mock_wm):
        mock_mw.is_property_panel_active = False
        mc.request_property_panel(MagicMock())
        mock_mw.general_tab.update_prop_button_state.assert_called_with(True)
        mock_mw.text_tab.update_prop_button_state.assert_called_with(True)
        mock_mw.image_tab.update_prop_button_state.assert_called_with(True)

    def test_shows_and_raises_panel(self, mc, mock_mw, mock_wm):
        w = MagicMock()
        mc.request_property_panel(w)
        mock_mw.property_panel.show.assert_called()
        mock_mw.property_panel.raise_.assert_called()
        mock_mw.property_panel.activateWindow.assert_called()

    def test_raises_window(self, mc, mock_mw, mock_wm):
        w = MagicMock()
        mc.request_property_panel(w)
        w.raise_.assert_called()

    def test_already_active_skips_tab_update(self, mc, mock_mw, mock_wm):
        mock_mw.is_property_panel_active = True
        mc.request_property_panel(MagicMock())
        mock_mw.update_prop_button_style.assert_called()
