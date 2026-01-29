from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from ui.controllers.main_controller import MainController


class TestMainController:
    @pytest.fixture
    def main_controller(self):
        mw = MagicMock()
        wm = MagicMock()
        # Mock attributes accessed by controller
        mw.is_property_panel_active = False
        mw.property_panel = MagicMock()

        # Tabs
        mw.animation_tab = MagicMock()
        mw.image_tab = MagicMock()
        mw.text_tab = MagicMock()
        mw.connections_tab = MagicMock()
        mw.general_tab = MagicMock()

        controller = MainController(mw, wm)
        return controller

    def test_setup_connections(self, main_controller):
        main_controller.setup_connections()
        # Verify signal connected
        main_controller.model.sig_selection_changed.connect.assert_called_with(main_controller._on_selection_changed)

    def test_on_selection_changed_with_window(self, main_controller):
        window = MagicMock()
        main_controller.view.is_property_panel_active = True

        main_controller._on_selection_changed(window)

        # Check Property Panel update
        main_controller.view.property_panel.set_target.assert_called_with(window)
        main_controller.view.property_panel.show.assert_called()

        # Check Tabs update
        main_controller.view.animation_tab.on_selection_changed.assert_called_with(window)
        main_controller.view.image_tab.on_selection_changed.assert_called_with(window)
        main_controller.view.text_tab.on_selection_changed.assert_called_with(window)
        main_controller.view.connections_tab.on_selection_changed.assert_called_with(window)

    def test_on_selection_changed_none(self, main_controller):
        main_controller.view.is_property_panel_active = False

        main_controller._on_selection_changed(None)

        # Check Property Panel hide
        main_controller.view.property_panel.set_target.assert_called_with(None)
        main_controller.view.property_panel.hide.assert_called()

        # Check Tabs update (None)
        main_controller.view.text_tab.on_selection_changed.assert_called_with(None)

    def test_handle_app_state_change_inactive(self, main_controller):
        main_controller.model.last_selected_window = MagicMock()

        main_controller.handle_app_state_change(Qt.ApplicationInactive)

        main_controller.model.set_selected_window.assert_called_with(None)

    def test_request_property_panel(self, main_controller):
        window = MagicMock()
        main_controller.view.is_property_panel_active = False

        main_controller.request_property_panel(window)

        # Check state active
        assert main_controller.view.is_property_panel_active is True

        # Check button state update
        main_controller.view.general_tab.update_prop_button_state.assert_called_with(True)
        main_controller.view.text_tab.update_prop_button_state.assert_called_with(True)
        main_controller.view.image_tab.update_prop_button_state.assert_called_with(True)

        # Check style update
        main_controller.view.update_prop_button_style.assert_called()

        # Check model selection
        main_controller.model.set_selected_window.assert_called_with(window)

        # Check panel show
        main_controller.view.property_panel.show.assert_called()
