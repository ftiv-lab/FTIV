# -*- coding: utf-8 -*-
"""PropertyPanel closeEvent の同期挙動テスト。"""

from unittest.mock import MagicMock

from PySide6.QtWidgets import QWidget

from ui.property_panel import PropertyPanel


def test_close_event_syncs_mainwindow_toggle_off(qapp):
    parent = QWidget()
    parent.is_property_panel_active = True
    parent.general_tab = MagicMock()
    parent.text_tab = MagicMock()
    parent.image_tab = MagicMock()
    parent.update_prop_button_style = MagicMock()

    panel = PropertyPanel(parent=parent)
    panel.show()
    qapp.processEvents()

    panel.close()
    qapp.processEvents()

    assert parent.is_property_panel_active is False
    parent.general_tab.update_prop_button_state.assert_called_with(False)
    parent.text_tab.update_prop_button_state.assert_called_with(False)
    parent.image_tab.update_prop_button_state.assert_called_with(False)
    parent.update_prop_button_style.assert_called()


def test_close_event_syncs_with_main_window_reference_when_detached(qapp):
    mw = QWidget()
    mw.is_property_panel_active = True
    mw.general_tab = MagicMock()
    mw.text_tab = MagicMock()
    mw.image_tab = MagicMock()
    mw.update_prop_button_style = MagicMock()

    panel = PropertyPanel(parent=None, main_window=mw)
    panel.show()
    qapp.processEvents()

    panel.close()
    qapp.processEvents()

    assert mw.is_property_panel_active is False
    mw.general_tab.update_prop_button_state.assert_called_with(False)
    mw.text_tab.update_prop_button_state.assert_called_with(False)
    mw.image_tab.update_prop_button_state.assert_called_with(False)
    mw.update_prop_button_style.assert_called()


def test_close_event_without_parent_is_safe(qapp):
    panel = PropertyPanel(parent=None)
    panel.show()
    qapp.processEvents()

    panel.close()
    qapp.processEvents()
