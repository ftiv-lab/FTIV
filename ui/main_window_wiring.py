"""MainWindow UI wiring helpers.

This module keeps tab creation/title wiring out of MainWindow itself so that
MainWindow can focus on orchestration.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QTabWidget

from ui.tabs.about_tab import AboutTab
from ui.tabs.animation_tab import AnimationTab
from ui.tabs.general_tab import GeneralTab
from ui.tabs.image_tab import ImageTab
from ui.tabs.info_tab import InfoTab
from ui.tabs.scene_tab import ConnectionsTab, SceneTab
from ui.tabs.text_tab import TextTab
from utils.translator import tr


def build_main_tabs(main_window: Any, tabs: QTabWidget) -> None:
    """Build main tabs in a single, centralized order."""
    main_window.general_tab = GeneralTab(main_window)
    tabs.addTab(main_window.general_tab, tr("tab_general"))

    main_window.text_tab = TextTab(main_window)
    tabs.addTab(main_window.text_tab, tr("tab_text"))

    main_window.image_tab = ImageTab(main_window)
    tabs.addTab(main_window.image_tab, tr("tab_image"))

    main_window.scene_tab = SceneTab(main_window)
    tabs.addTab(main_window.scene_tab, tr("tab_scene"))

    main_window.connections_tab = ConnectionsTab(main_window)
    tabs.addTab(main_window.connections_tab, tr("tab_connections"))

    main_window.info_tab = InfoTab(main_window)
    tabs.addTab(main_window.info_tab, tr("tab_info"))

    main_window.animation_tab = AnimationTab(main_window)
    tabs.addTab(main_window.animation_tab, tr("tab_animation"))

    main_window.about_tab = AboutTab(main_window)
    tabs.addTab(main_window.about_tab, tr("tab_about"))


def refresh_main_tab_titles(tabs: QTabWidget) -> None:
    """Refresh localized titles for top-level tabs."""
    title_keys = (
        "tab_general",
        "tab_text",
        "tab_image",
        "tab_scene",
        "tab_connections",
        "tab_info",
        "tab_animation",
        "tab_about",
    )
    count = min(tabs.count(), len(title_keys))
    for index in range(count):
        tabs.setTabText(index, tr(title_keys[index]))


def create_connections_subtab(main_window: Any) -> Any:
    """Build connections widget via centralized tab wiring module."""
    return ConnectionsTab(main_window)
