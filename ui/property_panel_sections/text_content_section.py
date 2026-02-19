import typing
from typing import Any

from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from ui.widgets import CollapsibleBox
from utils.due_date import display_due_iso
from utils.translator import tr


def build_text_header_controls(panel: Any, target: Any) -> None:
    """テキスト共通の上段コントロール（選択情報の直下）を構築する。"""
    mode_row = QWidget()
    mode_row_layout = QHBoxLayout(mode_row)
    mode_row_layout.setContentsMargins(0, 0, 0, 0)
    mode_row_layout.setSpacing(4)

    panel.btn_task_mode = panel.create_action_button(
        tr("menu_toggle_task_mode"),
        lambda checked: target.set_content_mode("task" if checked else "note"),
        "toggle",
    )
    panel.btn_task_mode.setCheckable(True)
    panel.btn_task_mode.setChecked(target.is_task_mode())

    panel.btn_text_orientation = panel.create_action_button(
        tr("btn_toggle_orientation"),
        lambda checked: panel._on_text_orientation_toggled(checked, target),
        "toggle",
    )
    panel.btn_text_orientation.setCheckable(True)
    panel.btn_text_orientation.setChecked(bool(getattr(target, "is_vertical", False)))
    panel.btn_text_orientation.setToolTip(tr("msg_task_mode_horizontal_only") if target.is_task_mode() else "")

    mode_row_layout.addWidget(panel.btn_task_mode, 1)
    mode_row_layout.addWidget(panel.btn_text_orientation, 1)
    panel.scroll_layout.addWidget(mode_row)


def build_text_content_section(panel: Any, target: Any) -> None:
    text_content_layout = panel.create_collapsible_group(
        tr("prop_grp_text_content"),
        expanded=False,
        state_key="text_content",
    )

    if target.is_task_mode():
        done, total = target.get_task_progress()
        progress_text = tr("label_task_progress_fmt").format(done=done, total=total)
        panel.lbl_task_progress = QLabel(progress_text)
        panel.lbl_task_progress.setProperty("class", "info-label")
        text_content_layout.addRow("", typing.cast(QWidget, panel.lbl_task_progress))

        btn_row = QWidget()
        btn_h = QHBoxLayout(btn_row)
        btn_h.setContentsMargins(0, 0, 0, 0)
        btn_h.setSpacing(4)

        panel.btn_complete_all = QPushButton(tr("btn_complete_all_tasks"))
        panel.btn_complete_all.setProperty("class", "secondary-button")
        panel.btn_complete_all.clicked.connect(lambda: target.complete_all_tasks() or panel.update_property_values())

        panel.btn_uncomplete_all = QPushButton(tr("btn_uncomplete_all_tasks"))
        panel.btn_uncomplete_all.setProperty("class", "secondary-button")
        panel.btn_uncomplete_all.clicked.connect(
            lambda: target.uncomplete_all_tasks() or panel.update_property_values()
        )

        btn_h.addWidget(panel.btn_complete_all)
        btn_h.addWidget(panel.btn_uncomplete_all)
        text_content_layout.addRow("", btn_row)

    panel.edit_note_title = QLineEdit(str(getattr(target, "title", "") or ""))
    panel.edit_note_title.setPlaceholderText(tr("placeholder_note_title"))
    text_content_layout.addRow(tr("label_note_title"), typing.cast(QWidget, panel.edit_note_title))

    raw_tags = getattr(target, "tags", [])
    tag_text = ", ".join(str(tag) for tag in raw_tags if str(tag).strip()) if isinstance(raw_tags, list) else ""
    panel.edit_note_tags = QLineEdit(tag_text)
    panel.edit_note_tags.setPlaceholderText(tr("placeholder_note_tags"))
    text_content_layout.addRow(tr("label_note_tags"), typing.cast(QWidget, panel.edit_note_tags))

    due_text = display_due_iso(str(getattr(target, "due_at", "") or ""))
    panel.edit_note_due_at = QLineEdit(due_text)
    panel.edit_note_due_at.setPlaceholderText(tr("placeholder_note_due_at"))
    panel.btn_pick_note_due_at = QPushButton(tr("btn_pick_due_date"))
    panel.btn_pick_note_due_at.setProperty("class", "secondary-button")
    panel.btn_pick_note_due_at.clicked.connect(panel._pick_note_due_date)

    due_row = QWidget()
    due_row_layout = QHBoxLayout(due_row)
    due_row_layout.setContentsMargins(0, 0, 0, 0)
    due_row_layout.setSpacing(4)
    due_row_layout.addWidget(panel.edit_note_due_at, 1)
    due_row_layout.addWidget(panel.btn_pick_note_due_at)
    text_content_layout.addRow(tr("label_note_due_at"), due_row)

    quick_due_row = QWidget()
    quick_due_layout = QHBoxLayout(quick_due_row)
    quick_due_layout.setContentsMargins(0, 0, 0, 0)
    quick_due_layout.setSpacing(4)
    panel.btn_due_today = QPushButton(tr("btn_today"))
    panel.btn_due_today.setProperty("class", "secondary-button")
    panel.btn_due_today.clicked.connect(lambda: panel._set_quick_due_offset(0))
    quick_due_layout.addWidget(panel.btn_due_today)
    panel.btn_due_tomorrow = QPushButton(tr("due_quick_tomorrow"))
    panel.btn_due_tomorrow.setProperty("class", "secondary-button")
    panel.btn_due_tomorrow.clicked.connect(lambda: panel._set_quick_due_offset(1))
    quick_due_layout.addWidget(panel.btn_due_tomorrow)
    panel.btn_due_next_week = QPushButton(tr("due_quick_next_week"))
    panel.btn_due_next_week.setProperty("class", "secondary-button")
    panel.btn_due_next_week.clicked.connect(lambda: panel._set_quick_due_offset(7))
    quick_due_layout.addWidget(panel.btn_due_next_week)
    panel.btn_due_clear = QPushButton(tr("btn_clear"))
    panel.btn_due_clear.setProperty("class", "secondary-button")
    panel.btn_due_clear.clicked.connect(panel._clear_quick_due)
    quick_due_layout.addWidget(panel.btn_due_clear)
    text_content_layout.addRow("", quick_due_row)

    due_details_box = CollapsibleBox(tr("label_due_details"))
    due_details_widget = QWidget()
    due_details_layout = QFormLayout(due_details_widget)
    due_details_layout.setContentsMargins(4, 4, 4, 4)
    due_details_layout.setSpacing(4)

    panel.cmb_note_due_precision = QComboBox()
    panel.cmb_note_due_precision.addItem(tr("label_due_precision_date"), "date")
    panel.cmb_note_due_precision.addItem(tr("label_due_precision_datetime"), "datetime")
    due_precision = panel._sanitize_due_precision(getattr(target, "due_precision", "date"))
    due_precision_idx = panel.cmb_note_due_precision.findData(due_precision)
    panel.cmb_note_due_precision.setCurrentIndex(due_precision_idx if due_precision_idx >= 0 else 0)
    panel.cmb_note_due_precision.currentIndexChanged.connect(panel._on_due_precision_changed)

    panel.edit_note_due_time = QLineEdit(str(getattr(target, "due_time", "") or ""))
    panel.edit_note_due_time.setPlaceholderText(tr("placeholder_due_time"))
    panel.edit_note_due_timezone = QLineEdit(str(getattr(target, "due_timezone", "") or ""))
    panel.edit_note_due_timezone.setPlaceholderText(tr("placeholder_due_timezone"))

    due_details_layout.addRow(tr("label_due_precision"), typing.cast(QWidget, panel.cmb_note_due_precision))
    due_details_layout.addRow(tr("label_due_time"), typing.cast(QWidget, panel.edit_note_due_time))
    due_details_layout.addRow(tr("label_due_timezone"), typing.cast(QWidget, panel.edit_note_due_timezone))

    due_details_box.setContentLayout(due_details_layout)
    due_details_box.toggle_button.setChecked(False)
    due_details_box.on_toggled(False)
    text_content_layout.addRow("", due_details_box)
    panel._sync_due_detail_enabled_state()

    panel.btn_note_star = panel.create_action_button(tr("label_note_star"), lambda: None, "toggle")
    panel.btn_note_star.setCheckable(True)
    panel.btn_note_star.setChecked(bool(getattr(target, "is_starred", False)))

    panel.btn_note_archived = panel.create_action_button(tr("label_note_archived"), lambda: None, "toggle")
    panel.btn_note_archived.setCheckable(True)
    panel.btn_note_archived.setChecked(bool(getattr(target, "is_archived", False)))

    panel.btn_apply_note_meta = QPushButton(tr("btn_apply_note_meta"))
    panel.btn_apply_note_meta.setProperty("class", "secondary-button")
    panel.edit_note_title.editingFinished.connect(lambda: panel._apply_note_metadata_to_target(target, "auto"))
    panel.edit_note_tags.editingFinished.connect(lambda: panel._apply_note_metadata_to_target(target, "auto"))
    panel.edit_note_due_at.editingFinished.connect(lambda: panel._apply_note_metadata_to_target(target, "auto"))
    if panel.edit_note_due_time is not None:
        panel.edit_note_due_time.returnPressed.connect(lambda: panel._apply_note_metadata_to_target(target, "enter"))
    if panel.edit_note_due_timezone is not None:
        panel.edit_note_due_timezone.returnPressed.connect(
            lambda: panel._apply_note_metadata_to_target(target, "enter")
        )
    panel.btn_apply_note_meta.clicked.connect(lambda: panel._apply_note_metadata_to_target(target, "button"))

    meta_btn_row = QWidget()
    meta_btn_layout = QHBoxLayout(meta_btn_row)
    meta_btn_layout.setContentsMargins(0, 0, 0, 0)
    meta_btn_layout.setSpacing(4)
    meta_btn_layout.addWidget(panel.btn_note_star)
    meta_btn_layout.addWidget(panel.btn_note_archived)
    meta_btn_layout.addWidget(panel.btn_apply_note_meta)
    text_content_layout.addRow("", meta_btn_row)
