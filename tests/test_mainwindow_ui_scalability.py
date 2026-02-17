from unittest.mock import patch

from ui.main_window import MainWindow


def test_mainwindow_minimum_size_hint_budget(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        size = mw.minimumSizeHint()
        assert size.width() <= 560
        assert size.height() <= 640
    finally:
        mw.close()


def test_heavy_tabs_support_compact_mode_contract(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        for tab in (
            mw.general_tab,
            mw.text_tab,
            mw.image_tab,
            mw.scene_tab,
            mw.connections_tab,
            mw.info_tab,
            mw.animation_tab,
            mw.about_tab,
        ):
            tab.set_compact_mode(True)
            tab.set_compact_mode(False)
    finally:
        mw.close()


def test_info_tab_minimum_height_budget_on_320_width(qapp) -> None:
    mw = MainWindow()
    try:
        tab = mw.info_tab
        tab.resize(320, 600)
        tab.advanced_filters_box.toggle_button.setChecked(False)
        qapp.processEvents()
        assert tab.minimumSizeHint().height() <= 400
    finally:
        mw.close()


def test_about_tab_minimum_height_budget(qapp) -> None:
    mw = MainWindow()
    try:
        mw.set_main_ui_density_mode("comfortable")
        qapp.processEvents()
        assert mw.about_tab.minimumSizeHint().height() <= 420

        mw.set_main_ui_density_mode("compact")
        qapp.processEvents()
        assert mw.about_tab.minimumSizeHint().height() <= 320
    finally:
        mw.close()


def test_mainwindow_ui_density_auto_breakpoints(qapp) -> None:
    mw = MainWindow()
    try:
        if mw.app_settings is not None:
            mw.app_settings.tab_ui_compact_overrides = {}
        mw._tab_compact_overrides = {}
        mw.set_main_ui_density_mode("auto")

        with patch.object(mw, "width", return_value=320):
            mw._apply_mainwindow_compact_mode(force=True)
            assert mw.get_effective_main_ui_density_mode() == "compact"
            assert mw._tab_compact_state.get("about") is True

        with patch.object(mw, "width", return_value=420):
            mw._apply_mainwindow_compact_mode(force=True)
            assert mw.get_effective_main_ui_density_mode() == "regular"
            assert mw._tab_compact_state.get("about") is True

        with patch.object(mw, "width", return_value=480):
            mw._apply_mainwindow_compact_mode(force=True)
            assert mw.get_effective_main_ui_density_mode() == "comfortable"
            assert mw._tab_compact_state.get("about") is False
    finally:
        mw.close()


def test_mainwindow_ui_density_override_per_tab(qapp) -> None:
    mw = MainWindow()
    try:
        if mw.app_settings is not None:
            mw.app_settings.tab_ui_compact_overrides = {}
        mw._tab_compact_overrides = {}
        mw.set_main_ui_density_mode("comfortable")
        qapp.processEvents()
        assert mw._tab_compact_state.get("image") is False
        assert mw._tab_compact_state.get("animation") is False

        mw.set_tab_compact_override("image", True)
        qapp.processEvents()
        assert mw._tab_compact_state.get("image") is True
        assert mw._tab_compact_state.get("animation") is False
    finally:
        mw.close()
