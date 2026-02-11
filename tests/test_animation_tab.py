from ui.main_window import MainWindow
from utils.translator import tr


def test_animation_tab_priority_menu_actions_exist(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        tab = mw.animation_tab
        action_texts = [a.text() for a in tab.menu_priority_actions.actions() if not a.isSeparator()]
        assert tr("btn_stop_all_anim") in action_texts
        assert tr("btn_anim_stop_move") in action_texts
        assert tr("btn_anim_stop_fade") in action_texts
    finally:
        mw.close()


def test_animation_tab_compact_labels_switch(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        tab = mw.animation_tab
        tab.set_compact_mode(True)
        assert tab.anim_btn_apply_move_params.text() == tr("btn_anim_apply_move_params_short")
        assert tab.anim_btn_apply_move_params.toolTip() == tr("btn_anim_apply_move_params")

        tab.set_compact_mode(False)
        assert tab.anim_btn_apply_move_params.text() == tr("btn_anim_apply_move_params")
    finally:
        mw.close()
