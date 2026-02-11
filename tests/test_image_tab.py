from ui.main_window import MainWindow
from utils.translator import tr


def test_image_tab_priority_menu_actions_exist(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        tab = mw.image_tab
        action_texts = [a.text() for a in tab.menu_priority_actions.actions() if not a.isSeparator()]
        assert tr("btn_close_selected_image") in action_texts
        assert tr("btn_close_all_images") in action_texts
        assert tr("btn_align_images") in action_texts
    finally:
        mw.close()


def test_image_tab_compact_labels_switch(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        tab = mw.image_tab
        tab.set_compact_mode(True)
        assert tab.btn_close_all_img.text() == tr("btn_close_all_images_short")
        assert tab.btn_close_all_img.toolTip() == tr("btn_close_all_images")

        tab.set_compact_mode(False)
        assert tab.btn_close_all_img.text() == tr("btn_close_all_images")
    finally:
        mw.close()
