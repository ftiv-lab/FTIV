# -*- coding: utf-8 -*-
"""Font dialog helper tests."""

from unittest.mock import MagicMock, patch

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QGroupBox, QLabel, QLineEdit, QListView

from utils.font_dialog import (
    _apply_dialog_layout_policy,
    _hide_effect_controls,
    _hide_style_controls,
    _stabilize_sample_preview,
    choose_font,
)


@patch("utils.font_dialog.QFontDialog")
def test_choose_font_rejected_returns_none(mock_qfont_dialog, qapp):
    mock_dlg = MagicMock()
    mock_dlg.exec.return_value = 0
    mock_dlg.findChildren.return_value = []
    mock_dlg.findChild.return_value = None
    mock_dlg.layout.return_value = None
    mock_qfont_dialog.Accepted = 1
    mock_qfont_dialog.FontDialogOption.DontUseNativeDialog = object()
    mock_qfont_dialog.return_value = mock_dlg

    font = choose_font(None, QFont("Arial", 12))
    assert font is None


@patch("utils.font_dialog.QFontDialog")
def test_choose_font_sanitizes_effect_flags(mock_qfont_dialog, qapp):
    selected = QFont("Arial", 12)
    selected.setUnderline(True)
    selected.setStrikeOut(True)

    mock_dlg = MagicMock()
    mock_dlg.exec.return_value = 1
    mock_dlg.selectedFont.return_value = selected
    mock_dlg.findChildren.return_value = []
    mock_dlg.findChild.return_value = None
    mock_dlg.layout.return_value = None
    mock_qfont_dialog.Accepted = 1
    mock_qfont_dialog.FontDialogOption.DontUseNativeDialog = object()
    mock_qfont_dialog.return_value = mock_dlg

    result = choose_font(None, QFont("Arial", 12))
    assert isinstance(result, QFont)
    assert result.underline() is False
    assert result.strikeOut() is False


def test_choose_font_hides_effect_checkboxes(qapp):
    # Qtの実ダイアログ構造に対して helper が適用できることを確認する
    from PySide6.QtWidgets import QFontDialog

    dialog = QFontDialog()
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)

    _hide_effect_controls(dialog)

    effect_boxes = dialog.findChildren(QCheckBox)
    assert effect_boxes  # Qt側仕様が変わっていないことの検知
    assert all(not cb.isVisible() for cb in effect_boxes)
    dialog.done(QDialog.Rejected)


def test_stabilize_sample_preview_keeps_sample_area_usable(qapp):
    from PySide6.QtWidgets import QFontDialog

    dialog = QFontDialog()
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    _hide_effect_controls(dialog)
    _stabilize_sample_preview(dialog)

    sample_edit = dialog.findChild(QLineEdit, "qt_fontDialog_sampleEdit")
    assert sample_edit is not None
    assert sample_edit.minimumHeight() >= 24

    sample_group = None
    parent_group = sample_edit.parentWidget()
    if isinstance(parent_group, QGroupBox):
        sample_group = parent_group
    assert sample_group is not None
    assert sample_group.minimumHeight() >= 90

    dialog.show()
    qapp.processEvents()
    assert sample_edit.height() > 0
    dialog.done(QDialog.Rejected)


def test_hide_style_controls_hides_middle_style_column(qapp):
    from PySide6.QtWidgets import QFontDialog

    dialog = QFontDialog()
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    dialog.show()
    qapp.processEvents()

    visible_lists_before = [v for v in dialog.findChildren(QListView) if v.isVisible()]
    assert len(visible_lists_before) >= 3

    _hide_style_controls(dialog)
    qapp.processEvents()

    visible_lists_after = [v for v in dialog.findChildren(QListView) if v.isVisible()]
    assert len(visible_lists_after) <= len(visible_lists_before) - 1
    assert len(visible_lists_after) == 2

    dialog.done(QDialog.Rejected)


def test_apply_layout_policy_moves_writing_system_to_top_middle(qapp):
    from PySide6.QtWidgets import QFontDialog

    dialog = QFontDialog()
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    dialog.show()
    qapp.processEvents()

    ws_label = None
    ws_combo = None
    for label in dialog.findChildren(QLabel):
        buddy = label.buddy()
        if isinstance(buddy, QComboBox):
            ws_label = label
            ws_combo = buddy
            break

    assert ws_label is not None
    assert ws_combo is not None
    before_y = ws_label.geometry().y()
    assert before_y > 200

    _apply_dialog_layout_policy(dialog)
    qapp.processEvents()

    after_y = ws_label.geometry().y()
    assert after_y < 80
    assert ws_combo.geometry().y() < 80

    visible_lists_after = [v for v in dialog.findChildren(QListView) if v.isVisible()]
    assert len(visible_lists_after) == 2
    dialog.done(QDialog.Rejected)


def test_apply_layout_policy_expands_font_list_area(qapp):
    from PySide6.QtWidgets import QFontDialog

    dialog = QFontDialog()
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    dialog.show()
    qapp.processEvents()

    _apply_dialog_layout_policy(dialog)
    qapp.processEvents()

    visible_lists = [v for v in dialog.findChildren(QListView) if v.isVisible()]
    assert len(visible_lists) == 2
    visible_lists.sort(key=lambda view: view.geometry().x())
    font_list, size_list = visible_lists

    assert font_list.geometry().height() > size_list.geometry().height()
    assert size_list.geometry().height() >= 180

    sample_edit = dialog.findChild(QLineEdit, "qt_fontDialog_sampleEdit")
    assert sample_edit is not None
    assert sample_edit.isVisible()
    assert sample_edit.height() >= 24

    dialog.done(QDialog.Rejected)
