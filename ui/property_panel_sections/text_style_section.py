import logging
import traceback
import typing
from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from utils.font_dialog import choose_font
from utils.translator import tr

logger = logging.getLogger(__name__)


def build_text_style_section(panel: Any, target: Any) -> None:
    text_style_layout = panel.create_collapsible_group(
        tr("prop_grp_text_style"),
        expanded=False,
        state_key="text_style",
    )

    panel.btn_text_font = QPushButton(f"{target.font_family} ({target.font_size}pt)")
    panel.btn_text_font.setProperty("class", "secondary-button")

    def change_font() -> None:
        font = choose_font(panel, QFont(target.font_family, int(target.font_size)))
        if font is not None:
            try:
                target.set_undoable_property("font_family", font.family())
                target.set_undoable_property("font_size", font.pointSize())
                target.update_text()
            except Exception as e:
                logger.error(f"Failed to change font: {e}\n{traceback.format_exc()}")
                QMessageBox.warning(panel, tr("msg_error"), f"Font change failed: {e}")

    panel.btn_text_font.clicked.connect(change_font)
    text_style_layout.addRow(tr("prop_font_selector"), typing.cast(QWidget, panel.btn_text_font))

    commit, prev = panel._make_callbacks(target, "font_size", "update_text", True)
    panel.spin_text_font_size, panel.slider_text_font_size = panel.add_slider_spin(
        text_style_layout, tr("prop_size"), target.font_size, 1, 200, commit, prev
    )

    panel.btn_text_color = panel.add_color_button(
        text_style_layout,
        tr("prop_color"),
        target.font_color,
        lambda v: target.set_undoable_property("font_color", panel._normalize_color_to_hexargb(v), "update_text"),
    )

    commit, prev = panel._make_callbacks(target, "text_opacity", "update_text", True)
    panel.spin_text_opacity, panel.slider_text_opacity = panel.add_slider_spin(
        text_style_layout, tr("label_opacity"), target.text_opacity, 0, 100, commit, prev
    )

    panel.btn_text_gradient_toggle = QPushButton(tr("menu_toggle_text_gradient"))
    panel.btn_text_gradient_toggle.setProperty("class", "toggle")
    panel.btn_text_gradient_toggle.setCheckable(True)
    panel.btn_text_gradient_toggle.setChecked(target.text_gradient_enabled)
    panel.btn_text_gradient_toggle.clicked.connect(
        lambda c: target.set_undoable_property("text_gradient_enabled", c, "update_text")
    )
    text_style_layout.addRow("", typing.cast(QWidget, panel.btn_text_gradient_toggle))

    panel.btn_edit_text_gradient = QPushButton("🎨 " + tr("menu_edit_text_gradient"))
    panel.btn_edit_text_gradient.setProperty("class", "secondary-button")
    panel.btn_edit_text_gradient.clicked.connect(panel._open_text_gradient_dialog)
    text_style_layout.addRow("", typing.cast(QWidget, panel.btn_edit_text_gradient))

    commit, prev = panel._make_callbacks(target, "text_gradient_opacity", "update_text", True)
    panel.spin_text_gradient_opacity, panel.slider_text_gradient_opacity = panel.add_slider_spin(
        text_style_layout, tr("menu_set_text_gradient_opacity"), target.text_gradient_opacity, 0, 100, commit, prev
    )

    panel.btn_save_text_default = QPushButton("💾 " + tr("btn_save_as_default"))
    panel.btn_save_text_default.setProperty("class", "secondary-button")
    panel.btn_save_text_default.setToolTip(tr("tip_save_text_default"))
    if panel.mw and hasattr(panel.mw, "main_controller"):
        panel.btn_save_text_default.clicked.connect(panel.mw.main_controller.txt_actions.save_as_default)
    text_style_layout.addRow("", typing.cast(QWidget, panel.btn_save_text_default))
