import logging
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs import DatePickerDialog
from utils.due_date import display_due_iso, normalize_due_input_allow_empty
from utils.translator import tr

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ui.main_window import MainWindow


def from_qt_type(flag_enum_value):
    """Qt.WindowType.xxx -> int helper (if needed)"""
    return flag_enum_value


class TextTab(QWidget):
    """テキスト管理タブ。MainWindowから分離・クラス化。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window

        self._setup_ui()

        # 互換性: MainWindowから参照される属性を注入

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # =========================
        # Header（上部固定）
        # =========================
        self.btn_add_text_main = QPushButton("+ " + tr("menu_add_text"))
        self.btn_add_text_main.setMinimumHeight(50)
        self.btn_add_text_main.setProperty("class", "large-button")
        self.btn_add_text_main.clicked.connect(self.mw.main_controller.txt_actions.add_new_text_window)
        layout.addWidget(self.btn_add_text_main)

        self.btn_toggle_prop_text = QPushButton(tr("btn_toggle_prop_panel"))
        self.btn_toggle_prop_text.setProperty("class", "toggle")
        self.btn_toggle_prop_text.setCheckable(True)
        self.btn_toggle_prop_text.clicked.connect(self.mw.toggle_property_panel)
        layout.addWidget(self.btn_toggle_prop_text)

        self.txt_selected_label = QLabel("")
        self.txt_selected_label.setWordWrap(True)
        self.txt_selected_label.setProperty("class", "dim small")
        # Use simple classes
        self.txt_selected_label.setProperty("class", "info-label")
        layout.addWidget(self.txt_selected_label)

        # =========================
        # Sub Tabs
        # =========================
        self.txt_subtabs = QTabWidget()

        # --- Manage ---
        self.manage_tab = self._build_manage_subtab()
        self.txt_subtabs.addTab(
            self.manage_tab, tr("tab_img_manage") if tr("tab_img_manage") != "tab_img_manage" else tr("grp_file_ops")
        )

        # --- Visibility ---
        self.visibility_tab = self._build_visibility_subtab()
        self.txt_subtabs.addTab(self.visibility_tab, tr("tab_img_visibility"))

        # --- Layout / Vertical ---
        self.layout_tab = self._build_layout_subtab()
        self.txt_subtabs.addTab(self.layout_tab, tr("grp_orientation_spacing"))

        # --- Bulk（Style専用）---
        self.bulk_tab = QWidget()
        bulk_layout = QVBoxLayout(self.bulk_tab)

        self.style_group = QGroupBox(tr("grp_bulk_style"))
        style_grid = QGridLayout(self.style_group)

        self.btn_font = QPushButton(tr("btn_change_all_fonts"))
        self.btn_font.setObjectName("ActionBtn")
        self.btn_font.clicked.connect(self.mw.main_controller.bulk_manager.change_all_fonts)

        self.btn_apply_preset_all = QPushButton(tr("btn_apply_preset_all"))
        self.btn_apply_preset_all.setObjectName("ActionBtn")
        self.btn_apply_preset_all.clicked.connect(self.mw.apply_preset_to_all_text_windows)

        self.btn_front = QPushButton(tr("btn_toggle_front"))
        self.btn_front.setObjectName("ActionBtn")
        self.btn_front.clicked.connect(self.mw.main_controller.bulk_manager.toggle_all_frontmost_text_windows)

        style_grid.addWidget(self.btn_font, 0, 0)
        style_grid.addWidget(self.btn_apply_preset_all, 0, 1)
        style_grid.addWidget(self.btn_front, 1, 0, 1, 2)

        bulk_layout.addWidget(self.style_group)
        bulk_layout.addStretch()
        self.txt_subtabs.addTab(self.bulk_tab, tr("grp_bulk_actions"))

        self.txt_scroll_area = QScrollArea()
        self.txt_scroll_area.setWidgetResizable(True)
        self.txt_scroll_area.setObjectName("TextTabScrollArea")
        self.txt_scroll_content = QWidget()
        scroll_layout = QVBoxLayout(self.txt_scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(4)
        scroll_layout.addWidget(self.txt_subtabs)
        self.txt_scroll_area.setWidget(self.txt_scroll_content)
        layout.addWidget(self.txt_scroll_area, 1)

        self.set_compact_mode(False)

        # 初期反映（Selected表示 + Selected系ボタン有効無効）
        # まだ attributes を注入していないが、self メソッド内なら self.* を見に行けばよい
        if hasattr(self.mw, "last_selected_window"):
            self.on_selection_changed(getattr(self.mw, "last_selected_window", None))

    def _build_manage_subtab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- Create ---
        self.txt_manage_grp_create = QGroupBox(tr("grp_img_manage_create"))
        grid_create = QGridLayout(self.txt_manage_grp_create)

        self.txt_btn_manage_add = QPushButton("+ " + tr("menu_add_text"))
        self.txt_btn_manage_add.setMinimumHeight(40)
        self.txt_btn_manage_add.setProperty("class", "emphasized")
        self.txt_btn_manage_add.clicked.connect(self.mw.main_controller.txt_actions.add_new_text_window)

        self.txt_btn_manage_show_list = QPushButton(tr("btn_show_list"))
        self.txt_btn_manage_show_list.setObjectName("ActionBtn")
        self.txt_btn_manage_show_list.clicked.connect(self.mw.main_controller.bulk_manager.show_text_window_list)

        grid_create.addWidget(self.txt_btn_manage_add, 0, 0, 1, 2)
        grid_create.addWidget(self.txt_btn_manage_show_list, 1, 0, 1, 2)

        layout.addWidget(self.txt_manage_grp_create)

        # --- Selected Window Operations ---
        self.txt_manage_grp_selected = QGroupBox(tr("grp_img_manage_selected"))
        grid_sel = QGridLayout(self.txt_manage_grp_selected)

        self.txt_btn_manage_clone_selected = QPushButton(tr("menu_clone_text"))
        self.txt_btn_manage_clone_selected.setObjectName("ActionBtn")
        self.txt_btn_manage_clone_selected.clicked.connect(self.mw.main_controller.txt_actions.clone_selected)

        self.txt_btn_manage_save_png_selected = QPushButton(tr("menu_save_png"))
        self.txt_btn_manage_save_png_selected.setObjectName("ActionBtn")
        self.txt_btn_manage_save_png_selected.clicked.connect(self.mw.main_controller.txt_actions.save_png_selected)

        self.txt_btn_manage_save_selected_json = QPushButton(tr("menu_save_json"))
        self.txt_btn_manage_save_selected_json.setObjectName("ActionBtn")
        self.txt_btn_manage_save_selected_json.clicked.connect(
            self.mw.main_controller.txt_actions.save_selected_to_json
        )

        # 読込はシーン読込に寄せる方針
        self.txt_btn_manage_load_scene_json = QPushButton(tr("menu_load_json"))
        self.txt_btn_manage_load_scene_json.setObjectName("ActionBtn")
        self.txt_btn_manage_load_scene_json.clicked.connect(self.mw.file_manager.load_scene_from_json)

        self.txt_btn_manage_style_gallery = QPushButton(tr("menu_open_style_gallery"))
        self.txt_btn_manage_style_gallery.setObjectName("ActionBtn")
        self.txt_btn_manage_style_gallery.clicked.connect(self.mw._txt_open_style_gallery_selected)

        grid_sel.addWidget(self.txt_btn_manage_clone_selected, 0, 0)
        grid_sel.addWidget(self.txt_btn_manage_save_png_selected, 0, 1)
        grid_sel.addWidget(self.txt_btn_manage_save_selected_json, 1, 0)
        grid_sel.addWidget(self.txt_btn_manage_load_scene_json, 1, 1)
        grid_sel.addWidget(self.txt_btn_manage_style_gallery, 2, 0, 1, 2)

        layout.addWidget(self.txt_manage_grp_selected)
        layout.addStretch()
        return tab

    def _build_visibility_subtab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- Selected ---
        grp_sel = QGroupBox(tr("anim_target_selected"))
        grid_sel = QGridLayout(grp_sel)

        self.txt_btn_sel_show = QPushButton(tr("menu_show_text"))
        self.txt_btn_sel_show.setObjectName("ActionBtn")
        self.txt_btn_sel_show.clicked.connect(
            lambda: self.mw.main_controller.txt_actions.run_selected_visibility_action("show")
        )

        self.txt_btn_sel_hide = QPushButton(tr("menu_hide_text"))
        self.txt_btn_sel_hide.setObjectName("ActionBtn")
        self.txt_btn_sel_hide.clicked.connect(
            lambda: self.mw.main_controller.txt_actions.run_selected_visibility_action("hide")
        )

        self.txt_btn_sel_frontmost = QPushButton(tr("menu_toggle_frontmost"))
        self.txt_btn_sel_frontmost.setProperty("class", "toggle")
        self.txt_btn_sel_frontmost.setCheckable(True)
        self.txt_btn_sel_frontmost.toggled.connect(
            lambda checked: self.mw.main_controller.txt_actions.run_selected_visibility_action("frontmost", checked)
        )

        self.txt_btn_sel_click_through = QPushButton(tr("menu_toggle_click_through"))
        self.txt_btn_sel_click_through.setProperty("class", "toggle")
        self.txt_btn_sel_click_through.setCheckable(True)
        self.txt_btn_sel_click_through.toggled.connect(
            lambda checked: self.mw.main_controller.txt_actions.run_selected_visibility_action("click_through", checked)
        )

        self.txt_btn_sel_hide_others = QPushButton(tr("menu_hide_others"))
        self.txt_btn_sel_hide_others.setObjectName("ActionBtn")
        self.txt_btn_sel_hide_others.clicked.connect(self.mw.main_controller.txt_actions.hide_other_text_windows)

        self.txt_btn_sel_show_others = QPushButton(tr("menu_show_others"))
        self.txt_btn_sel_show_others.setObjectName("ActionBtn")
        self.txt_btn_sel_show_others.clicked.connect(self.mw.main_controller.txt_actions.show_other_text_windows)

        self.txt_btn_sel_close_others = QPushButton(tr("menu_close_others"))
        self.txt_btn_sel_close_others.setObjectName("DangerBtn")
        self.txt_btn_sel_close_others.clicked.connect(self.mw.main_controller.txt_actions.close_other_text_windows)

        self.txt_btn_sel_close = QPushButton(tr("menu_close_text"))
        self.txt_btn_sel_close.setObjectName("DangerBtn")
        self.txt_btn_sel_close.clicked.connect(
            lambda: self.mw.main_controller.txt_actions.run_selected_visibility_action("close")
        )

        grid_sel.addWidget(self.txt_btn_sel_show, 0, 0)
        grid_sel.addWidget(self.txt_btn_sel_hide, 0, 1)
        grid_sel.addWidget(self.txt_btn_sel_frontmost, 1, 0)
        grid_sel.addWidget(self.txt_btn_sel_click_through, 1, 1)
        grid_sel.addWidget(self.txt_btn_sel_hide_others, 2, 0)
        grid_sel.addWidget(self.txt_btn_sel_show_others, 2, 1)
        grid_sel.addWidget(self.txt_btn_sel_close_others, 3, 0, 1, 2)
        grid_sel.addWidget(self.txt_btn_sel_close, 4, 0, 1, 2)

        layout.addWidget(grp_sel)

        # --- All ---
        self.txt_vis_grp_all = QGroupBox(tr("anim_target_all_text"))
        grid_all = QGridLayout(self.txt_vis_grp_all)

        self.txt_btn_all_show = QPushButton(tr("btn_show_all_text"))
        self.txt_btn_all_show.setObjectName("ActionBtn")
        self.txt_btn_all_show.clicked.connect(self.mw.main_controller.bulk_manager.show_all_text_windows)

        self.txt_btn_all_hide = QPushButton(tr("btn_hide_all_text"))
        self.txt_btn_all_hide.setObjectName("ActionBtn")
        self.txt_btn_all_hide.clicked.connect(self.mw.main_controller.bulk_manager.hide_all_text_windows)

        self.txt_btn_all_frontmost = QPushButton(tr("menu_switch_all_front_text"))
        self.txt_btn_all_frontmost.setObjectName("ActionBtn")
        self.txt_btn_all_frontmost.clicked.connect(
            self.mw.main_controller.bulk_manager.toggle_all_frontmost_text_windows
        )

        self.txt_btn_all_click_through = QPushButton(tr("menu_toggle_click_through_text"))
        self.txt_btn_all_click_through.setObjectName("ActionBtn")
        self.txt_btn_all_click_through.clicked.connect(self.mw.main_controller.bulk_manager.toggle_text_click_through)

        self.txt_btn_all_close = QPushButton(tr("menu_close_all_text"))
        self.txt_btn_all_close.setObjectName("DangerBtn")
        self.txt_btn_all_close.clicked.connect(self.mw.main_controller.bulk_manager.close_all_text_windows)

        grid_all.addWidget(self.txt_btn_all_show, 0, 0)
        grid_all.addWidget(self.txt_btn_all_hide, 0, 1)
        grid_all.addWidget(self.txt_btn_all_frontmost, 1, 0)
        grid_all.addWidget(self.txt_btn_all_click_through, 1, 1)
        grid_all.addWidget(self.txt_btn_all_close, 2, 0, 1, 2)

        layout.addWidget(self.txt_vis_grp_all)
        layout.addStretch()
        return tab

    def _build_layout_subtab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- Selected ---
        self.txt_layout_grp_selected = QGroupBox(tr("anim_target_selected"))
        grid_sel = QGridLayout(self.txt_layout_grp_selected)

        self.txt_btn_sel_toggle_vertical = QPushButton(tr("btn_toggle_orientation"))
        self.txt_btn_sel_toggle_vertical.setProperty("class", "toggle")
        self.txt_btn_sel_toggle_vertical.setCheckable(True)
        self.txt_btn_sel_toggle_vertical.toggled.connect(
            lambda checked: self.mw.main_controller.txt_actions.run_selected_layout_action("set_vertical", checked)
        )

        self.txt_btn_sel_spacing_settings = QPushButton(tr("menu_margin_settings"))
        self.txt_btn_sel_spacing_settings.setObjectName("ActionBtn")
        self.txt_btn_sel_spacing_settings.clicked.connect(
            lambda: self.mw.main_controller.txt_actions.run_selected_layout_action("open_spacing_settings")
        )

        # Content Mode (Note / Task)
        self.btn_content_mode_note = QPushButton(tr("label_content_mode_note"))
        self.btn_content_mode_note.setProperty("class", "toggle")
        self.btn_content_mode_note.setCheckable(True)
        self.btn_content_mode_note.setChecked(True)
        self.btn_content_mode_note.clicked.connect(lambda: self._set_content_mode("note"))

        self.btn_content_mode_task = QPushButton(tr("label_content_mode_task"))
        self.btn_content_mode_task.setProperty("class", "toggle")
        self.btn_content_mode_task.setCheckable(True)
        self.btn_content_mode_task.clicked.connect(lambda: self._set_content_mode("task"))

        self.lbl_note_title = QLabel(tr("label_note_title"))
        self.edit_note_title = QLineEdit()
        self.edit_note_title.setPlaceholderText(tr("placeholder_note_title"))
        self.edit_note_title.returnPressed.connect(self._apply_note_metadata)

        self.lbl_note_tags = QLabel(tr("label_note_tags"))
        self.edit_note_tags = QLineEdit()
        self.edit_note_tags.setPlaceholderText(tr("placeholder_note_tags"))
        self.edit_note_tags.returnPressed.connect(self._apply_note_metadata)

        self.lbl_note_due_at = QLabel(tr("label_note_due_at"))
        self.edit_note_due_at = QLineEdit()
        self.edit_note_due_at.setPlaceholderText(tr("placeholder_note_due_at"))
        self.edit_note_due_at.returnPressed.connect(self._apply_note_metadata)
        self.btn_pick_note_due_at = QPushButton(tr("btn_pick_due_date"))
        self.btn_pick_note_due_at.setObjectName("ActionBtn")
        self.btn_pick_note_due_at.clicked.connect(self._pick_due_date_for_note)

        due_row = QWidget()
        due_row_layout = QHBoxLayout(due_row)
        due_row_layout.setContentsMargins(0, 0, 0, 0)
        due_row_layout.setSpacing(4)
        due_row_layout.addWidget(self.edit_note_due_at, 1)
        due_row_layout.addWidget(self.btn_pick_note_due_at)

        self.chk_note_star = QCheckBox(tr("label_note_star"))
        self.chk_note_archived = QCheckBox(tr("label_note_archived"))
        self.btn_apply_note_meta = QPushButton(tr("btn_apply_note_meta"))
        self.btn_apply_note_meta.setObjectName("ActionBtn")
        self.btn_apply_note_meta.clicked.connect(self._apply_note_metadata)

        grid_sel.addWidget(self.btn_content_mode_note, 0, 0)
        grid_sel.addWidget(self.btn_content_mode_task, 0, 1)
        grid_sel.addWidget(self.lbl_note_title, 1, 0)
        grid_sel.addWidget(self.edit_note_title, 1, 1)
        grid_sel.addWidget(self.lbl_note_tags, 2, 0)
        grid_sel.addWidget(self.edit_note_tags, 2, 1)
        grid_sel.addWidget(self.lbl_note_due_at, 3, 0)
        grid_sel.addWidget(due_row, 3, 1)
        grid_sel.addWidget(self.chk_note_star, 4, 0)
        grid_sel.addWidget(self.chk_note_archived, 4, 1)
        grid_sel.addWidget(self.btn_apply_note_meta, 5, 0, 1, 2)
        grid_sel.addWidget(self.txt_btn_sel_toggle_vertical, 6, 0, 1, 2)
        grid_sel.addWidget(self.txt_btn_sel_spacing_settings, 7, 0, 1, 2)

        # ✨ New: Save current as Default
        self.btn_save_default_selected = QPushButton("✨ " + tr("btn_save_as_default"))
        self.btn_save_default_selected.setObjectName("ActionBtn")
        self.btn_save_default_selected.setToolTip(tr("tip_save_as_default"))
        self.btn_save_default_selected.clicked.connect(self.mw.main_controller.txt_actions.save_as_default)
        grid_sel.addWidget(self.btn_save_default_selected, 8, 0, 1, 2)

        layout.addWidget(self.txt_layout_grp_selected)

        # --- Bulk ---
        self.txt_layout_grp_all = QGroupBox(tr("anim_target_all_text"))
        grid_bulk = QGridLayout(self.txt_layout_grp_all)

        self.btn_all_horizontal = QPushButton(tr("btn_set_all_horizontal"))
        self.btn_all_horizontal.setObjectName("ActionBtn")
        self.btn_all_horizontal.clicked.connect(self.mw.main_controller.bulk_manager.set_all_text_horizontal)

        self.btn_all_vertical = QPushButton(tr("btn_set_all_vertical"))
        self.btn_all_vertical.setObjectName("ActionBtn")
        self.btn_all_vertical.clicked.connect(self.mw.main_controller.bulk_manager.set_all_text_vertical)

        self.btn_def_spacing_h = QPushButton(tr("btn_set_def_spacing_h"))
        self.btn_def_spacing_h.setObjectName("ActionBtn")
        self.btn_def_spacing_h.clicked.connect(self.mw.main_controller.bulk_manager.set_default_text_spacing)

        self.btn_def_spacing_v = QPushButton(tr("btn_set_def_spacing_v"))
        self.btn_def_spacing_v.setObjectName("ActionBtn")
        self.btn_def_spacing_v.clicked.connect(self.mw.main_controller.bulk_manager.set_default_text_spacing_vertical)

        grid_bulk.addWidget(self.btn_all_horizontal, 0, 0)
        grid_bulk.addWidget(self.btn_all_vertical, 0, 1)
        grid_bulk.addWidget(self.btn_def_spacing_h, 1, 0)
        grid_bulk.addWidget(self.btn_def_spacing_v, 1, 1)

        layout.addWidget(self.txt_layout_grp_all)
        layout.addStretch()
        return tab

    def on_selection_changed(self, window: Optional[Any]) -> None:
        """テキストウィンドウ選択変更時のUI更新"""
        selected_obj = None

        if window is not None:
            # 型チェック（循環参照回避のため文字列判定で緩和）
            t_name = type(window).__name__
            if t_name in ("TextWindow", "ConnectorLabel"):
                selected_obj = window

        if selected_obj is None:
            self.txt_selected_label.setText(tr("label_anim_selected_none"))

            # 外部呼び出し（ボタン有効化状態のリセットなど）
            # 外部呼び出し（ボタン有効化状態のリセットなど）
            self.update_enabled_state(None)

            # チェックを落とす
            self._reset_toggle_buttons()
            return

        # 名前とテキストの表示
        name = type(selected_obj).__name__
        text = ""
        try:
            text = str(getattr(selected_obj, "text", "") or "")
        except Exception:
            logger.debug("Failed to retrieve text from selected object", exc_info=True)

        first_line = text.split("\n")[0].strip() if text else ""
        if len(first_line) > 30:
            first_line = first_line[:30] + "..."

        selected_text = tr("label_anim_selected_fmt").format(name=name)
        if first_line:
            self.txt_selected_label.setText(f"{selected_text} / {first_line}")
        else:
            self.txt_selected_label.setText(selected_text)

        # チェック状態の同期
        self._sync_check_states(selected_obj)

        self.update_enabled_state(selected_obj)

    def _reset_toggle_buttons(self) -> None:
        buttons = [
            self.txt_btn_sel_frontmost,
            self.txt_btn_sel_click_through,
            self.txt_btn_sel_toggle_vertical,
        ]
        for btn in buttons:
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
        self._sync_content_mode_buttons("note")
        self._sync_note_meta_controls(None)

    def _sync_check_states(self, obj: Any) -> None:
        # Frontmost
        is_top = obj.windowFlags() & from_qt_type(obj.windowFlags().__class__.WindowStaysOnTopHint)
        self.txt_btn_sel_frontmost.blockSignals(True)
        self.txt_btn_sel_frontmost.setChecked(bool(is_top))
        self.txt_btn_sel_frontmost.blockSignals(False)

        # ClickThrough
        is_ct = obj.windowFlags() & from_qt_type(obj.windowFlags().__class__.WindowTransparentForInput)
        self.txt_btn_sel_click_through.blockSignals(True)
        self.txt_btn_sel_click_through.setChecked(bool(is_ct))
        self.txt_btn_sel_click_through.blockSignals(False)

        # Vertical
        is_vert = getattr(obj, "is_vertical", False)
        mode = str(getattr(obj, "content_mode", "note") or "note").lower()
        is_task_mode = mode == "task"
        self.txt_btn_sel_toggle_vertical.blockSignals(True)
        self.txt_btn_sel_toggle_vertical.setChecked(bool(is_vert))
        self.txt_btn_sel_toggle_vertical.setEnabled(not is_task_mode)
        self.txt_btn_sel_toggle_vertical.setToolTip(tr("msg_task_mode_horizontal_only") if is_task_mode else "")
        self.txt_btn_sel_toggle_vertical.blockSignals(False)

        # Content Mode
        self._sync_content_mode_buttons(mode)
        self._sync_note_meta_controls(obj)

    def _set_content_mode(self, mode: str) -> None:
        """選択中のTextWindowのコンテンツモードを変更する。"""
        try:
            wm = getattr(self.mw, "window_manager", None)
            if wm is None:
                return
            sel = getattr(wm, "last_selected_window", None)
            if sel is not None and hasattr(sel, "set_content_mode"):
                sel.set_content_mode(mode)
                self._sync_check_states(sel)
            else:
                self._sync_content_mode_buttons(mode)
        except Exception:
            logger.debug("Failed to set content mode", exc_info=True)

    def _sync_content_mode_buttons(self, mode: str) -> None:
        """Note/Taskボタンの排他チェック状態を同期する。"""
        self.btn_content_mode_note.blockSignals(True)
        self.btn_content_mode_task.blockSignals(True)
        self.btn_content_mode_note.setChecked(mode == "note")
        self.btn_content_mode_task.setChecked(mode == "task")
        self.btn_content_mode_note.blockSignals(False)
        self.btn_content_mode_task.blockSignals(False)

    @staticmethod
    def _parse_tags_csv(raw: str) -> list[str]:
        tags: list[str] = []
        seen: set[str] = set()
        for token in str(raw or "").split(","):
            tag = token.strip()
            key = tag.lower()
            if not tag or key in seen:
                continue
            tags.append(tag)
            seen.add(key)
        return tags

    @staticmethod
    def _normalize_due_input(raw: str) -> str | None:
        return normalize_due_input_allow_empty(raw)

    @staticmethod
    def _display_due_input(raw_iso: str) -> str:
        return display_due_iso(raw_iso)

    def _pick_due_date_for_note(self) -> None:
        if self.edit_note_due_at is None:
            return
        initial_value = self.edit_note_due_at.text()
        selected = DatePickerDialog.pick_date(self, initial_value)
        if selected is None:
            return
        self.edit_note_due_at.setText(selected)

    def _apply_note_metadata(self) -> None:
        """選択中のTextWindowへ note metadata を適用する。"""
        try:
            wm = getattr(self.mw, "window_manager", None)
            if wm is None:
                return
            target = getattr(wm, "last_selected_window", None)
            if target is None:
                return

            t_name = type(target).__name__
            if t_name not in ("TextWindow", "ConnectorLabel"):
                return
            is_text_window = t_name == "TextWindow"

            title = self.edit_note_title.text().strip()
            tags = self._parse_tags_csv(self.edit_note_tags.text())
            is_starred = self.chk_note_star.isChecked()
            due_iso = self._normalize_due_input(self.edit_note_due_at.text() if self.edit_note_due_at else "")
            if due_iso is None:
                QMessageBox.warning(self, tr("msg_error"), tr("msg_invalid_due_date_format"))
                return
            is_archived = self.chk_note_archived.isChecked()

            if hasattr(target, "set_title_and_tags"):
                target.set_title_and_tags(title, tags)
            else:
                target.set_undoable_property("title", title, "update_text")
                target.set_undoable_property("tags", tags, "update_text")

            if hasattr(target, "set_starred"):
                target.set_starred(is_starred)
            else:
                target.set_undoable_property("is_starred", bool(is_starred), "update_text")

            if is_text_window:
                if due_iso:
                    if hasattr(target, "set_due_at"):
                        target.set_due_at(due_iso)
                    else:
                        target.set_undoable_property("due_at", due_iso, "update_text")
                else:
                    if hasattr(target, "clear_due_at"):
                        target.clear_due_at()
                    else:
                        target.set_undoable_property("due_at", "", "update_text")

                if hasattr(target, "set_archived"):
                    target.set_archived(bool(is_archived))
                else:
                    target.set_undoable_property("is_archived", bool(is_archived), "update_text")

            self._sync_note_meta_controls(target)
            if hasattr(self.mw, "info_tab"):
                self.mw.info_tab.refresh_data()
        except Exception:
            logger.debug("Failed to apply note metadata", exc_info=True)

    def _sync_note_meta_controls(self, obj: Optional[Any]) -> None:
        is_text_like = obj is not None and type(obj).__name__ in ("TextWindow", "ConnectorLabel")
        is_text_window = obj is not None and type(obj).__name__ == "TextWindow"

        for w in [self.edit_note_title, self.edit_note_tags, self.chk_note_star, self.btn_apply_note_meta]:
            if w is not None:
                w.setEnabled(is_text_like)

        for w in [self.edit_note_due_at, self.btn_pick_note_due_at, self.chk_note_archived]:
            if w is not None:
                w.setEnabled(is_text_window)

        if not is_text_like or obj is None:
            self.edit_note_title.setText("")
            self.edit_note_tags.setText("")
            self.chk_note_star.setChecked(False)
            self.edit_note_due_at.setText("")
            self.chk_note_archived.setChecked(False)
            return

        self.edit_note_title.setText(str(getattr(obj, "title", "") or ""))
        raw_tags = getattr(obj, "tags", [])
        if isinstance(raw_tags, list):
            tag_text = ", ".join(str(tag) for tag in raw_tags if str(tag).strip())
        else:
            tag_text = ""
        self.edit_note_tags.setText(tag_text)
        self.chk_note_star.setChecked(bool(getattr(obj, "is_starred", False)))
        if is_text_window:
            self.edit_note_due_at.setText(self._display_due_input(str(getattr(obj, "due_at", "") or "")))
            self.chk_note_archived.setChecked(bool(getattr(obj, "is_archived", False)))
        else:
            self.edit_note_due_at.setText("")
            self.chk_note_archived.setChecked(False)

    def refresh_ui(self) -> None:
        """UI文言更新"""
        self.btn_add_text_main.setText("+ " + tr("menu_add_text"))
        self.btn_toggle_prop_text.setText(tr("btn_toggle_prop_panel"))

        # SubTabs title
        self.txt_subtabs.setTabText(
            0, tr("tab_img_manage") if tr("tab_img_manage") != "tab_img_manage" else tr("grp_file_ops")
        )
        self.txt_subtabs.setTabText(1, tr("tab_img_visibility"))
        self.txt_subtabs.setTabText(2, tr("grp_orientation_spacing"))
        self.txt_subtabs.setTabText(3, tr("grp_bulk_actions"))

        # Manage
        self.txt_manage_grp_create.setTitle(tr("grp_img_manage_create"))
        self.txt_btn_manage_add.setText("+ " + tr("menu_add_text"))
        self.txt_btn_manage_show_list.setText(tr("btn_show_list"))

        self.txt_manage_grp_selected.setTitle(tr("grp_img_manage_selected"))
        self.txt_btn_manage_clone_selected.setText(tr("menu_clone_text"))
        self.txt_btn_manage_save_png_selected.setText(tr("menu_save_png"))
        self.txt_btn_manage_save_selected_json.setText(tr("menu_save_json"))
        self.txt_btn_manage_load_scene_json.setText(tr("menu_load_json"))
        self.txt_btn_manage_style_gallery.setText(tr("menu_open_style_gallery"))

        # Visibility
        self.txt_btn_sel_show.setText(tr("menu_show_text"))
        self.txt_btn_sel_hide.setText(tr("menu_hide_text"))
        self.txt_btn_sel_frontmost.setText(tr("menu_toggle_frontmost"))
        self.txt_btn_sel_click_through.setText(tr("menu_click_through"))
        self.txt_btn_sel_hide_others.setText(tr("menu_hide_others"))
        self.txt_btn_sel_show_others.setText(tr("menu_show_others"))
        self.txt_btn_sel_close_others.setText(tr("menu_close_others"))
        self.txt_btn_sel_close.setText(tr("menu_close_text"))

        self.txt_vis_grp_all.setTitle(tr("anim_target_all_text"))
        self.txt_btn_all_show.setText(tr("btn_show_all_text"))
        self.txt_btn_all_hide.setText(tr("btn_hide_all_text"))
        self.txt_btn_all_frontmost.setText(tr("menu_switch_all_front_text"))
        self.txt_btn_all_click_through.setText(tr("menu_toggle_click_through_text"))
        self.txt_btn_all_close.setText(tr("menu_close_all_text"))

        # Layout
        self.txt_layout_grp_selected.setTitle(tr("anim_target_selected"))
        self.txt_btn_sel_toggle_vertical.setText(tr("btn_toggle_orientation"))
        self.btn_save_default_selected.setText("✨ " + tr("btn_save_as_default"))
        self.btn_save_default_selected.setToolTip(tr("tip_save_as_default"))

        self.txt_btn_sel_spacing_settings.setText(tr("menu_margin_settings"))
        self.btn_content_mode_note.setText(tr("label_content_mode_note"))
        self.btn_content_mode_task.setText(tr("label_content_mode_task"))
        self.lbl_note_title.setText(tr("label_note_title"))
        self.lbl_note_tags.setText(tr("label_note_tags"))
        self.lbl_note_due_at.setText(tr("label_note_due_at"))
        self.chk_note_star.setText(tr("label_note_star"))
        self.chk_note_archived.setText(tr("label_note_archived"))
        self.btn_apply_note_meta.setText(tr("btn_apply_note_meta"))
        self.btn_pick_note_due_at.setText(tr("btn_pick_due_date"))
        self.edit_note_title.setPlaceholderText(tr("placeholder_note_title"))
        self.edit_note_tags.setPlaceholderText(tr("placeholder_note_tags"))
        self.edit_note_due_at.setPlaceholderText(tr("placeholder_note_due_at"))

        self.txt_layout_grp_all.setTitle(tr("anim_target_all_text"))
        self.btn_all_horizontal.setText(tr("btn_set_all_horizontal"))
        self.btn_all_vertical.setText(tr("btn_set_all_vertical"))
        self.btn_def_spacing_h.setText(tr("btn_set_def_spacing_h"))
        self.btn_def_spacing_v.setText(tr("btn_set_def_spacing_v"))

        # Style
        self.style_group.setTitle(tr("grp_bulk_style"))
        self.btn_font.setText(tr("btn_change_all_fonts"))
        self.btn_apply_preset_all.setText(tr("btn_apply_preset_all"))
        self.btn_front.setText(tr("btn_toggle_front"))

        # Update selected label if needed
        # (This is usually triggered by selection change, but we could re-trigger it)
        # self.on_selection_changed(getattr(self.mw, "last_selected_window", None))

    def set_compact_mode(self, enabled: bool) -> None:
        self.btn_add_text_main.setMinimumHeight(40 if enabled else 50)
        self.txt_btn_manage_add.setMinimumHeight(34 if enabled else 40)

    def update_prop_button_state(self, is_active: bool) -> None:
        """プロパティパネルボタンのトグル状態・スタイル更新。"""
        self.btn_toggle_prop_text.blockSignals(True)
        self.btn_toggle_prop_text.setChecked(is_active)
        self.btn_toggle_prop_text.blockSignals(False)
        # Style handled by QSS

    def update_enabled_state(self, selected_obj: Optional[Any]) -> None:
        """
        テキストタブの Selected系UIを、選択状態に応じて有効/無効を切り替える。
        """
        enabled_any = selected_obj is not None

        is_text_window = False
        is_label = False
        if selected_obj is not None:
            # 循環参照を避けるため型名で判定
            t_name = type(selected_obj).__name__
            is_text_window = t_name == "TextWindow"
            is_label = t_name == "ConnectorLabel"

        is_text_like = bool(enabled_any and (is_text_window or is_label))

        # -------------------------
        # 1) Text/Label 両方OK（選択がText系なら有効）
        # -------------------------
        attr_names_text_like = [
            # Visibility（Selected）
            "txt_btn_sel_show",
            "txt_btn_sel_hide",
            "txt_btn_sel_frontmost",
            "txt_btn_sel_click_through",
            "txt_btn_sel_close",
            # Manage（Selected）
            "txt_btn_manage_save_selected_json",
            "txt_btn_manage_load_scene_json",
            "txt_btn_manage_style_gallery",
            # Layout/Vertical（Selected）
            "txt_btn_sel_toggle_vertical",
            "txt_btn_sel_offset_mono",
            "txt_btn_sel_offset_prop",
            "txt_btn_sel_spacing_settings",
            # Content Mode
            "btn_content_mode_note",
            "btn_content_mode_task",
            "edit_note_title",
            "edit_note_tags",
            "chk_note_star",
            "btn_apply_note_meta",
        ]

        for attr in attr_names_text_like:
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setEnabled(is_text_like)
                except Exception:
                    logger.debug(f"Failed to set enabled state for {attr}", exc_info=True)

        # -------------------------
        # 2) TextWindow のみOK
        # -------------------------
        attr_names_only_textwindow = [
            # Visibility（Selected基準の「他」）
            "txt_btn_sel_hide_others",
            "txt_btn_sel_show_others",
            "txt_btn_sel_close_others",
            # Manage（Selected）
            "txt_btn_manage_clone_selected",
            "txt_btn_manage_save_png_selected",
            "edit_note_due_at",
            "btn_pick_note_due_at",
            "chk_note_archived",
        ]

        for attr in attr_names_only_textwindow:
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setEnabled(bool(is_text_like and is_text_window))
                except Exception:
                    logger.debug(f"Failed to set enabled state for (TextWindow only) {attr}", exc_info=True)
