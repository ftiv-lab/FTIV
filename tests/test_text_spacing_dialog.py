# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QApplication

from models.window_config import TextWindowConfig
from ui.dialogs import TextSpacingDialog


def _qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_restore_defaults_horizontal_uses_horizontal_defaults():
    _qapp()
    defaults = TextWindowConfig()
    dialog = TextSpacingDialog(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, is_vertical=False)
    dialog.restore_defaults()

    assert dialog.h_spin.value() == defaults.char_spacing_h
    assert dialog.v_spin.value() == defaults.line_spacing_h
    assert dialog.top_spin.value() == defaults.margin_top
    assert dialog.bottom_spin.value() == defaults.margin_bottom
    assert dialog.left_spin.value() == defaults.margin_left
    assert dialog.right_spin.value() == defaults.margin_right
    dialog.close()


def test_restore_defaults_vertical_uses_vertical_defaults():
    _qapp()
    defaults = TextWindowConfig()
    dialog = TextSpacingDialog(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, is_vertical=True)
    dialog.restore_defaults()

    assert dialog.h_spin.value() == defaults.char_spacing_v
    assert dialog.v_spin.value() == defaults.line_spacing_v
    assert dialog.top_spin.value() == float(defaults.v_margin_top or 0.0)
    assert dialog.bottom_spin.value() == float(defaults.v_margin_bottom or 0.0)
    assert dialog.left_spin.value() == float(defaults.v_margin_left or 0.0)
    assert dialog.right_spin.value() == float(defaults.v_margin_right or 0.0)
    dialog.close()
