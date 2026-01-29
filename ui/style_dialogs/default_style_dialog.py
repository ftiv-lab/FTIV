# ui/dialogs/default_style_dialog.py
"""
デフォルトノードスタイル設定ダイアログ。

新規ノード作成時に適用されるフォント、色、影、縁取りなどを設定する。
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from utils.translator import tr

if TYPE_CHECKING:
    from models.default_node_style import DefaultNodeStyle

logger = logging.getLogger(__name__)


class DefaultStyleDialog(QDialog):
    """デフォルトノードスタイル設定ダイアログ"""

    def __init__(self, style: "DefaultNodeStyle", parent=None):
        super().__init__(parent)
        self._style = style.model_copy()
        self._init_ui()

    def _init_ui(self) -> None:
        """UIを構築する。"""
        self.setWindowTitle(tr("mm_dialog_default_style"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # フォント設定
        font_group = QGroupBox(tr("prop_grp_font"))
        font_layout = QFormLayout()

        self._cmb_font = QFontComboBox()
        self._cmb_font.setCurrentFont(QFont(self._style.font_family))
        font_layout.addRow(tr("label_font"), self._cmb_font)

        self._spin_size = QSpinBox()
        self._spin_size.setRange(8, 72)
        self._spin_size.setValue(self._style.font_size)
        font_layout.addRow(tr("label_size"), self._spin_size)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # 色設定
        color_group = QGroupBox(tr("prop_grp_colors"))
        color_layout = QFormLayout()

        self._btn_text_color = QPushButton()
        self._btn_text_color.setFixedSize(60, 24)
        self._update_color_button(self._btn_text_color, QColor(self._style.font_color))
        self._btn_text_color.clicked.connect(self._pick_text_color)
        color_layout.addRow(tr("prop_text_color"), self._btn_text_color)

        self._btn_bg_color = QPushButton()
        self._btn_bg_color.setFixedSize(60, 24)
        self._update_color_button(self._btn_bg_color, QColor(self._style.background_color))
        self._btn_bg_color.clicked.connect(self._pick_bg_color)
        color_layout.addRow(tr("prop_bg_color"), self._btn_bg_color)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 透明度
        opacity_group = QGroupBox(tr("label_opacity"))
        opacity_layout = QFormLayout()

        self._spin_text_opacity = QSpinBox()
        self._spin_text_opacity.setRange(0, 100)
        self._spin_text_opacity.setValue(self._style.text_opacity)
        self._spin_text_opacity.setSuffix("%")
        opacity_layout.addRow(tr("prop_text_color"), self._spin_text_opacity)

        self._spin_bg_opacity = QSpinBox()
        self._spin_bg_opacity.setRange(0, 100)
        self._spin_bg_opacity.setValue(self._style.background_opacity)
        self._spin_bg_opacity.setSuffix("%")
        opacity_layout.addRow(tr("prop_bg_color"), self._spin_bg_opacity)

        opacity_group.setLayout(opacity_layout)
        layout.addWidget(opacity_group)

        # オプション
        opt_group = QGroupBox(tr("prop_grp_options"))
        opt_layout = QVBoxLayout()

        self._chk_shadow = QCheckBox(tr("menu_toggle_shadow"))
        self._chk_shadow.setChecked(self._style.shadow_enabled)
        opt_layout.addWidget(self._chk_shadow)

        self._chk_outline = QCheckBox(tr("menu_toggle_outline"))
        self._chk_outline.setChecked(self._style.outline_enabled)
        opt_layout.addWidget(self._chk_outline)

        self._chk_text_gradient = QCheckBox(tr("menu_toggle_text_gradient"))
        self._chk_text_gradient.setChecked(self._style.text_gradient_enabled)
        opt_layout.addWidget(self._chk_text_gradient)

        self._chk_bg_gradient = QCheckBox(tr("menu_toggle_bg_gradient"))
        self._chk_bg_gradient.setChecked(self._style.background_gradient_enabled)
        opt_layout.addWidget(self._chk_bg_gradient)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # ボタン
        btn_layout = QHBoxLayout()

        btn_reset = QPushButton(tr("btn_reset"))
        btn_reset.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(btn_reset)

        btn_layout.addStretch()

        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton(tr("btn_ok"))
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

    def _update_color_button(self, btn: QPushButton, color: QColor) -> None:
        """色ボタンの背景色を更新する。"""
        btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555;")
        btn.setProperty("color", color)

    def _pick_text_color(self) -> None:
        """テキスト色選択ダイアログを表示する。"""
        current = self._btn_text_color.property("color")
        color = QColorDialog.getColor(current, self, tr("prop_text_color"))
        if color.isValid():
            self._update_color_button(self._btn_text_color, color)

    def _pick_bg_color(self) -> None:
        """背景色選択ダイアログを表示する。"""
        current = self._btn_bg_color.property("color")
        color = QColorDialog.getColor(current, self, tr("prop_bg_color"))
        if color.isValid():
            self._update_color_button(self._btn_bg_color, color)

    def _reset_to_default(self) -> None:
        """デフォルト値にリセットする。"""
        from models.default_node_style import DefaultNodeStyle

        self._style = DefaultNodeStyle()
        self._update_ui()

    def _update_ui(self) -> None:
        """UIをスタイルオブジェクトの値で更新する。"""
        self._cmb_font.setCurrentFont(QFont(self._style.font_family))
        self._spin_size.setValue(self._style.font_size)
        self._update_color_button(self._btn_text_color, QColor(self._style.font_color))
        self._update_color_button(self._btn_bg_color, QColor(self._style.background_color))
        self._spin_text_opacity.setValue(self._style.text_opacity)
        self._spin_bg_opacity.setValue(self._style.background_opacity)
        self._chk_shadow.setChecked(self._style.shadow_enabled)
        self._chk_outline.setChecked(self._style.outline_enabled)
        self._chk_text_gradient.setChecked(self._style.text_gradient_enabled)
        self._chk_bg_gradient.setChecked(self._style.background_gradient_enabled)

    def get_style(self) -> "DefaultNodeStyle":
        """編集後のスタイルを返す。"""
        self._style.font_family = self._cmb_font.currentFont().family()
        self._style.font_size = self._spin_size.value()
        self._style.font_color = self._btn_text_color.property("color").name()
        self._style.background_color = self._btn_bg_color.property("color").name()
        self._style.text_opacity = self._spin_text_opacity.value()
        self._style.background_opacity = self._spin_bg_opacity.value()
        self._style.shadow_enabled = self._chk_shadow.isChecked()
        self._style.outline_enabled = self._chk_outline.isChecked()
        self._style.text_gradient_enabled = self._chk_text_gradient.isChecked()
        self._style.background_gradient_enabled = self._chk_bg_gradient.isChecked()
        return self._style
