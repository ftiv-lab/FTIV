from ui.main_window import MainWindow


def test_mainwindow_minimum_size_hint_budget(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        size = mw.minimumSizeHint()
        assert size.width() <= 520
        assert size.height() <= 700
    finally:
        mw.close()


def test_heavy_tabs_support_compact_mode_contract(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        for tab in (mw.info_tab, mw.text_tab, mw.image_tab, mw.animation_tab):
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
        assert tab.minimumSizeHint().height() <= 360
    finally:
        mw.close()
