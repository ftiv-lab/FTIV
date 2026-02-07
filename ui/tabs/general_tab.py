from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from utils.overlay_settings import save_overlay_settings
from utils.translator import get_lang, tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class GeneralTab(QWidget):
    """一般設定（ホーム）タブ。MainWindowから分離・クラス化。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window

        # 将来的な完全分離を見据えて self.mw への依存を整理しつつ、
        # Phase 1 では互換性のため mw の属性にもセットする。
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. 言語設定
        self.lang_group = QGroupBox(tr("grp_language"))
        lang_layout = QHBoxLayout(self.lang_group)
        lang_layout.setContentsMargins(10, 10, 10, 10)
        lang_layout.setSpacing(15)

        self.btn_lang_en = QRadioButton(tr("label_lang_en"))
        self.btn_lang_jp = QRadioButton(tr("label_lang_jp"))

        if get_lang() == "jp":
            self.btn_lang_jp.setChecked(True)
        else:
            self.btn_lang_en.setChecked(True)

        self.lang_button_group = QButtonGroup(self)
        self.lang_button_group.addButton(self.btn_lang_en, 0)
        self.lang_button_group.addButton(self.btn_lang_jp, 1)
        self.lang_button_group.idClicked.connect(self.mw.change_language)

        lang_layout.addStretch()
        lang_layout.addWidget(self.btn_lang_en)
        lang_layout.addWidget(self.btn_lang_jp)
        lang_layout.addStretch()
        layout.addWidget(self.lang_group)

        # --- メインウィンドウ最前面切替ボタン ---
        self.btn_main_frontmost = QPushButton(tr("btn_main_frontmost"))
        self.btn_main_frontmost.setProperty("class", "toggle")
        self.btn_main_frontmost.setCheckable(True)

        # 現在の最前面状態を反映
        is_top = bool(self.mw.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        self.btn_main_frontmost.setChecked(is_top)
        self.btn_main_frontmost.clicked.connect(self._on_toggle_frontmost)
        layout.addWidget(self.btn_main_frontmost)

        # スタイルを初期適用
        self.update_frontmost_button_state(is_top)

        # 2. クイックアクセス
        self.quick_group = QGroupBox(tr("grp_quick_access"))
        quick_layout = QGridLayout(self.quick_group)
        quick_layout.setSpacing(10)

        self.btn_toggle_prop = QPushButton(tr("btn_toggle_prop_panel"))
        self.btn_toggle_prop.setProperty("class", "toggle")
        self.btn_toggle_prop.setCheckable(True)
        self.btn_toggle_prop.setChecked(self.mw.is_property_panel_active)
        self.btn_toggle_prop.clicked.connect(self.mw.toggle_property_panel)
        # 初期スタイル適用
        self.update_prop_button_state(self.mw.is_property_panel_active)

        self.btn_show_all = QPushButton(tr("btn_show_all"))
        self.btn_show_all.setObjectName("ActionBtn")
        self.btn_show_all.clicked.connect(self.mw.main_controller.bulk_manager.show_all_everything)

        self.btn_hide_all = QPushButton(tr("btn_hide_all"))
        self.btn_hide_all.setObjectName("ActionBtn")
        self.btn_hide_all.clicked.connect(self.mw.main_controller.bulk_manager.hide_all_everything)

        quick_layout.addWidget(self.btn_toggle_prop, 0, 0, 1, 2)
        quick_layout.addWidget(self.btn_show_all, 1, 0)
        quick_layout.addWidget(self.btn_hide_all, 1, 1)
        layout.addWidget(self.quick_group)

        # 3. クリック透過救出エリア
        self.ct_group = QGroupBox(tr("grp_click_through"))
        ct_layout = QGridLayout(self.ct_group)

        self.btn_ct_text_gen = QPushButton(tr("btn_ct_text"))
        self.btn_ct_text_gen.setObjectName("ActionBtn")
        self.btn_ct_text_gen.clicked.connect(self.mw.main_controller.bulk_manager.toggle_text_click_through)

        self.btn_ct_image_gen = QPushButton(tr("menu_toggle_click_through_image"))
        self.btn_ct_image_gen.setObjectName("ActionBtn")
        self.btn_ct_image_gen.clicked.connect(self.mw.main_controller.bulk_manager.toggle_image_click_through)

        self.btn_disable_all_ct = QPushButton(tr("menu_disable_all_click_through"))
        self.btn_disable_all_ct.setObjectName("DangerBtn")
        self.btn_disable_all_ct.clicked.connect(self.mw.main_controller.bulk_manager.disable_all_click_through)

        ct_layout.addWidget(self.btn_ct_text_gen, 0, 0)
        ct_layout.addWidget(self.btn_ct_image_gen, 0, 1)
        ct_layout.addWidget(self.btn_disable_all_ct, 1, 0, 1, 2)
        layout.addWidget(self.ct_group)

        # 3.5 選択枠（オーバーレイ）設定
        self.overlay_group = QGroupBox(tr("grp_overlay_settings"))
        overlay_layout = QGridLayout(self.overlay_group)

        self.btn_toggle_selection_frame = QPushButton(tr("btn_toggle_selection_frame"))
        self.btn_toggle_selection_frame.setProperty("class", "toggle")
        self.btn_toggle_selection_frame.setCheckable(True)
        self.btn_toggle_selection_frame.setChecked(
            bool(getattr(self.mw.overlay_settings, "selection_frame_enabled", True))
        )

        self.btn_toggle_selection_frame.toggled.connect(self._on_toggle_overlay)

        self.btn_change_selection_frame_color = QPushButton(tr("btn_change_selection_frame_color"))
        self.btn_change_selection_frame_color.setObjectName("ActionBtn")
        self.btn_change_selection_frame_color.clicked.connect(self._on_change_overlay_color)

        self.btn_change_selection_frame_width = QPushButton(tr("btn_change_selection_frame_width"))
        self.btn_change_selection_frame_width.setObjectName("ActionBtn")
        self.btn_change_selection_frame_width.clicked.connect(self._on_change_overlay_width)

        overlay_layout.addWidget(self.btn_toggle_selection_frame, 0, 0, 1, 2)
        overlay_layout.addWidget(self.btn_change_selection_frame_color, 1, 0)
        overlay_layout.addWidget(self.btn_change_selection_frame_width, 1, 1)

        layout.addWidget(self.overlay_group)

        if hasattr(self.mw, "overlay_settings"):
            self._update_overlay_button_style(bool(getattr(self.mw.overlay_settings, "selection_frame_enabled", True)))

        # 4. ファイル操作
        self.file_group = QGroupBox(tr("grp_file_ops"))
        file_layout = QHBoxLayout(self.file_group)
        file_layout.setSpacing(10)

        self.btn_save_project = QPushButton(tr("menu_save_project"))
        self.btn_save_project.clicked.connect(self.mw.file_manager.save_project_as_json)

        self.btn_load_project = QPushButton(tr("menu_load_project"))
        self.btn_load_project.clicked.connect(self.mw.file_manager.load_project_from_json)

        file_layout.addWidget(self.btn_save_project)
        file_layout.addWidget(self.btn_load_project)
        layout.addWidget(self.file_group)

        # 6. リセットと初期化 (Danger Zone)
        self.danger_group = QGroupBox(tr("grp_danger_zone"))
        danger_layout = QHBoxLayout(self.danger_group)
        danger_layout.setSpacing(10)

        self.btn_close_all_everything = QPushButton(tr("btn_close_all_everything"))
        self.btn_close_all_everything.setObjectName(
            "ActionBtn"
        )  # Keep as Action or change to ActionBtn to differentiate
        self.btn_close_all_everything.clicked.connect(self.mw.main_controller.bulk_manager.close_all_everything)

        self.btn_factory_reset = QPushButton(tr("btn_factory_reset"))
        self.btn_factory_reset.setObjectName("DangerBtn")  # Red button
        self.btn_factory_reset.clicked.connect(self._on_factory_reset)

        danger_layout.addWidget(self.btn_close_all_everything, 2)
        danger_layout.addWidget(self.btn_factory_reset, 1)

        layout.addWidget(self.danger_group)
        layout.addStretch()

    def _on_factory_reset(self) -> None:
        """工場出荷状態リセットの呼び出し。"""
        from PySide6.QtWidgets import QMessageBox

        from ui.reset_confirm_dialog import ResetConfirmDialog
        from utils.reset_manager import ResetManager

        dialog = ResetConfirmDialog(self)
        if dialog.exec():
            # User Confirmed
            manager = ResetManager(self.mw.base_directory)
            if manager.perform_factory_reset():
                QMessageBox.information(self, tr("msg_reset_complete_title"), tr("msg_reset_complete_body"))
                from PySide6.QtWidgets import QApplication

                QApplication.quit()
            else:
                QMessageBox.critical(self, tr("msg_error"), tr("msg_reset_failed"))

    def _on_toggle_frontmost(self) -> None:
        """メインウィンドウの最前面表示を切り替える（内部処理）。"""
        is_checked = self.btn_main_frontmost.isChecked()
        self.mw.settings_manager.set_main_frontmost(is_checked)
        self.update_frontmost_button_state(is_checked)

    def _on_toggle_overlay(self, checked: bool) -> None:
        self.mw.overlay_settings.selection_frame_enabled = bool(checked)
        save_overlay_settings(self.mw, self.mw.base_directory, self.mw.overlay_settings)
        self.mw.apply_overlay_settings_to_all_windows()

        self._update_overlay_button_style(bool(checked))

    def _on_change_overlay_color(self) -> None:
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QColorDialog

        current = QColor(str(getattr(self.mw.overlay_settings, "selection_frame_color", "#C800FFFF")))
        color = QColorDialog.getColor(current, self, tr("btn_change_selection_frame_color"))
        if not color.isValid():
            return

        self.mw.overlay_settings.selection_frame_color = color.name(QColor.NameFormat.HexArgb)
        save_overlay_settings(self.mw, self.mw.base_directory, self.mw.overlay_settings)
        self.mw.apply_overlay_settings_to_all_windows()

    def _on_change_overlay_width(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        cur = int(getattr(self.mw.overlay_settings, "selection_frame_width", 4))
        val, ok = QInputDialog.getInt(
            self,
            tr("title_selection_frame_width"),
            tr("label_selection_frame_width"),
            cur,
            1,
            20,
        )
        if not ok:
            return

        self.mw.overlay_settings.selection_frame_width = int(val)
        save_overlay_settings(self.mw, self.mw.base_directory, self.mw.overlay_settings)
        self.mw.apply_overlay_settings_to_all_windows()

    def refresh_ui(self) -> None:
        """UIの文言を言語設定に合わせて更新する。"""
        # 言語
        self.lang_group.setTitle(tr("grp_language"))
        self.btn_lang_en.setText(tr("label_lang_en"))
        self.btn_lang_jp.setText(tr("label_lang_jp"))

        # 最前面
        self.btn_main_frontmost.setText(tr("btn_main_frontmost"))

        # クイックアクセス
        self.quick_group.setTitle(tr("grp_quick_access"))
        self.btn_toggle_prop.setText(tr("btn_toggle_prop_panel"))
        self.btn_show_all.setText(tr("btn_show_all"))
        self.btn_hide_all.setText(tr("btn_hide_all"))

        # 透過
        self.ct_group.setTitle(tr("grp_click_through"))
        self.btn_ct_text_gen.setText(tr("btn_ct_text"))
        self.btn_ct_image_gen.setText(tr("menu_toggle_click_through_image"))
        self.btn_disable_all_ct.setText(tr("menu_disable_all_click_through"))

        # ファイル
        self.file_group.setTitle(tr("grp_file_ops"))
        self.btn_save_project.setText(tr("menu_save_project"))
        self.btn_load_project.setText(tr("menu_load_project"))

        # オーバーレイ
        self.overlay_group.setTitle(tr("grp_overlay_settings"))
        self.btn_toggle_selection_frame.setText(tr("btn_toggle_selection_frame"))
        self.btn_change_selection_frame_color.setText(tr("btn_change_selection_frame_color"))
        self.btn_change_selection_frame_width.setText(tr("btn_change_selection_frame_width"))

        # 危険
        self.danger_group.setTitle(tr("grp_danger_zone"))
        self.btn_close_all_everything.setText(tr("btn_close_all_everything"))
        self.btn_factory_reset.setText(tr("btn_factory_reset"))

    def update_prop_button_state(self, is_active: bool) -> None:
        """プロパティパネルボタンのトグル状態・スタイル更新。"""
        self.btn_toggle_prop.blockSignals(True)
        self.btn_toggle_prop.setChecked(is_active)
        self.btn_toggle_prop.blockSignals(False)
        # Style handled by QSS

    def update_frontmost_button_state(self, is_top: bool) -> None:
        """最前面ボタンの状態更新。"""
        self.btn_main_frontmost.blockSignals(True)
        self.btn_main_frontmost.setChecked(is_top)
        self.btn_main_frontmost.blockSignals(False)
        # Style handled by QSS

    def _update_overlay_button_style(self, enabled: bool) -> None:
        """オーバーレイボタンのスタイル更新。"""
        # 内部用: _on_toggle_overlay から呼ばれる
        # QSS handles checked state
        pass

    def update_overlay_button_state(self, enabled: bool) -> None:
        """外部用: オーバーレイボタンの状態更新。"""
        self.btn_toggle_selection_frame.blockSignals(True)
        self.btn_toggle_selection_frame.setChecked(enabled)
        self.btn_toggle_selection_frame.blockSignals(False)
        self._update_overlay_button_style(enabled)
