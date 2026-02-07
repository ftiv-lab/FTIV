from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QLabel, QVBoxLayout

from managers.style_manager import StyleManager
from utils.translator import tr


class ResetConfirmDialog(QDialog):
    """
    Dialog to confirm Factory Reset.
    Shows a warning and requires explicit confirmation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("title_reset_confirm"))  # Add translation key later or use fallback
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setModal(True)
        # self.setFixedSize(400, 250) # Let layout decide

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Icon/Title
        title_label = QLabel(tr("msg_reset_warning_title"))
        title_label.setObjectName("h2")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Message
        msg = tr("msg_reset_warning_body")
        msg_label = QLabel(msg)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        # Buttons
        options_group = QGroupBox(tr("grp_reset_options"))
        op_layout = QVBoxLayout(options_group)

        self.chk_settings = QCheckBox(tr("lbl_reset_settings"))
        self.chk_settings.setChecked(True)
        op_layout.addWidget(self.chk_settings)

        self.chk_presets = QCheckBox(tr("lbl_reset_presets"))
        self.chk_presets.setProperty("class", "danger-text")
        self.chk_presets.setChecked(False)
        self.chk_presets.setToolTip(tr("tooltip_reset_presets"))
        layout.addWidget(self.chk_presets)

        layout.addWidget(options_group)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(tr("btn_factory_reset"))
        self.button_box.button(QDialogButtonBox.Ok).setProperty("class", "danger-button")  # Red Button)
        self.button_box.button(QDialogButtonBox.Cancel).setText(tr("btn_cancel"))

        # Style the OK button as Danger
        # We need to rely on StyleManager or set object name
        btn_ok = self.button_box.button(QDialogButtonBox.Ok)
        btn_ok.setObjectName("btn_danger")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

        # Apply Theme
        StyleManager.apply_theme_to_dialog(self)

    def get_options(self) -> tuple[bool, bool]:
        """
        Returns the selected options.
        (reset_settings, reset_user_data)
        """
        return self.chk_settings.isChecked(), self.chk_presets.isChecked()
