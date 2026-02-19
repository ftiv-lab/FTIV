"""PropertyPanel orchestration helpers.

Keep section composition and editing-target summary sync out of PropertyPanel
main body so the parent class remains focused on orchestration.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from ui.property_panel_sections import build_text_content_section, build_text_header_controls, build_text_style_section
from utils.translator import tr


def format_editing_target_text(target: Any) -> str:
    return tr("label_anim_selected_fmt").format(name=type(target).__name__)


def extract_editing_target_preview_text(target: Any) -> str:
    text = str(getattr(target, "text", "") or "").strip()
    if not text:
        return ""
    first_line = text.split("\n")[0].strip()
    return first_line


def elide_label_text(panel: Any, label: QLabel, text: str) -> str:
    if not text:
        return text
    available = label.contentsRect().width()
    if available <= 0:
        available = label.width()
    if available <= 0:
        available = max(1, panel.width() - 36)
    return label.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, max(1, available))


def ensure_editing_target_labels(panel: Any) -> None:
    if panel.lbl_editing_target is None:
        panel.lbl_editing_target = QLabel("")
        panel.lbl_editing_target.setProperty("class", "info-label")
        panel.lbl_editing_target.setWordWrap(False)
        panel.lbl_editing_target.setMinimumWidth(0)
        panel.lbl_editing_target.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        panel.scroll_layout.addWidget(panel.lbl_editing_target)

    if panel.lbl_editing_target_preview is None:
        panel.lbl_editing_target_preview = QLabel("")
        panel.lbl_editing_target_preview.setProperty("class", "info-label")
        panel.lbl_editing_target_preview.setWordWrap(False)
        panel.lbl_editing_target_preview.setMinimumWidth(0)
        panel.lbl_editing_target_preview.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        panel.scroll_layout.addWidget(panel.lbl_editing_target_preview)


def update_editing_target_labels(panel: Any, target: Any) -> None:
    ensure_editing_target_labels(panel)
    target_label = panel.lbl_editing_target
    preview_label = panel.lbl_editing_target_preview
    if target_label is None or preview_label is None:
        return

    full_target_text = format_editing_target_text(target)
    target_label.setToolTip(full_target_text)
    target_label.setText(elide_label_text(panel, target_label, full_target_text))

    preview_text = extract_editing_target_preview_text(target)
    if not preview_text:
        preview_label.setHidden(True)
        preview_label.setText("")
        preview_label.setToolTip("")
        return

    prefixed_full_text = f"{tr('label_selected_preview_prefix')} {preview_text}"
    preview_label.setHidden(False)
    preview_label.setToolTip(prefixed_full_text)
    preview_label.setText(elide_label_text(panel, preview_label, prefixed_full_text))


def build_text_window_primary_sections(panel: Any, target: Any) -> None:
    from windows.connector import ConnectorLabel
    from windows.text_window import TextWindow

    if isinstance(target, TextWindow):
        update_editing_target_labels(panel, target)
        build_text_header_controls(panel, target)

    if not isinstance(target, ConnectorLabel):
        panel.build_common_ui(target)
    else:
        layout = panel.create_collapsible_group(tr("prop_grp_transform"), expanded=False)
        layout.addRow(QLabel(tr("prop_pos_auto_linked")))
        panel.add_action_button(layout, tr("btn_toggle_front"), target.toggle_frontmost, "secondary-button")

    if isinstance(target, TextWindow):
        build_text_content_section(panel, target)

    build_text_style_section(panel, target)
