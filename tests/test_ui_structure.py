import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def app():
    """Session-wide QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="class")
def main_window(app):
    """Headless MainWindow fixture."""
    # Mocking config or heavy dependencies if needed,
    # but strictly for structure test, we want real instantiation
    # to see what attributes are created.
    # Note: Logic/Managers might start threads or timers,
    # so we rely on their safe init.
    mw = MainWindow()
    yield mw
    try:
        mw.close()
        mw.deleteLater()
    except RuntimeError:
        pass


class TestUIStructure:
    """
    UIコンポーネントの構造的整合性を検証するテスト。
    Manager/Controllerが想定する 'self.mw.tab_name.widget_name' が
    実際に存在することを保証する。
    """

    def test_mainwindow_has_main_tabs(self, main_window):
        """MainWindowが主要なタブ属性を保持しているか。"""
        required_tabs = [
            "general_tab",
            "text_tab",
            "image_tab",
            "animation_tab",
            "scene_tab",
            # "connections_tab" # ConnectionsTab might be named differently or instantiated later?
            # Check initialization in MainWindow._build_main_tabs or similar
        ]

        for tab_name in required_tabs:
            assert hasattr(main_window, tab_name), f"MainWindow is missing required tab: {tab_name}"
            tab_obj = getattr(main_window, tab_name)
            assert isinstance(tab_obj, QWidget), f"{tab_name} is not a QWidget instance"

    def test_animation_tab_structure(self, main_window):
        """AnimationManagerが依存する AnimationTab のUI部品が存在するか。"""
        tab = getattr(main_window, "animation_tab", None)
        assert tab is not None, "AnimationTab not found"

        # AnimationManager accesses these:
        required_widgets = [
            "anim_move_speed",
            "anim_move_pause",
            "anim_move_easing_combo",
            "anim_fade_speed",
            "anim_fade_pause",
            "anim_fade_easing_combo",
            "anim_btn_pingpong",
            "anim_btn_oneway",
        ]

        for widget in required_widgets:
            assert hasattr(tab, widget), f"AnimationTab missing widget: {widget}"

    def test_text_tab_structure(self, main_window):
        """TextActionsが依存する TextTab のUI部品が存在するか。"""
        tab = getattr(main_window, "text_tab", None)
        assert tab is not None, "TextTab not found"

        required_widgets = [
            "btn_add_text_main",
            "txt_btn_manage_add",
            "txt_btn_manage_clone_selected",
            "txt_btn_sel_toggle_vertical",
            "btn_font",
        ]

        for widget in required_widgets:
            assert hasattr(tab, widget), f"TextTab missing widget: {widget}"

    def test_image_tab_structure(self, main_window):
        """ImageActionsが依存する ImageTab のUI部品が存在するか。"""
        tab = getattr(main_window, "image_tab", None)
        assert tab is not None, "ImageTab not found"

        required_widgets = [
            "btn_add_image_main",
            "btn_add_image_manage",
            "img_btn_sel_reselect",
            "img_btn_sel_clone",
            "img_btn_sel_show",
            "img_btn_sel_hide",
        ]

        for widget in required_widgets:
            assert hasattr(tab, widget), f"ImageTab missing widget: {widget}"
