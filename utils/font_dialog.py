from typing import Optional

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QFontDialog, QGroupBox, QLineEdit, QWidget


def _hide_effect_controls(dialog: QFontDialog) -> None:
    """QFontDialog の Effects (Underline/StrikeOut) UI を非表示にする。"""
    # Effects グループはQCheckBoxを含む唯一のQGroupBoxとして現れるため、
    # タイトル文言に依存せず構造ベースで判定する。
    for group in dialog.findChildren(QGroupBox):
        if group.findChildren(QCheckBox):
            group.hide()

    # 念のためチェックボックス自体も隠す。
    for checkbox in dialog.findChildren(QCheckBox):
        checkbox.hide()


def _stabilize_sample_preview(dialog: QFontDialog) -> None:
    """Effects非表示後に Sample プレビュー領域の高さが潰れる現象を補正する。"""
    sample_edit = dialog.findChild(QLineEdit, "qt_fontDialog_sampleEdit")
    if sample_edit is None:
        return

    # Sample文字表示欄が0pxにならないよう最小高を確保。
    sample_edit.setMinimumHeight(max(sample_edit.sizeHint().height(), 24))

    # 親のQGroupBox（Sample）側にも最低高さを与えてレイアウト圧縮を防ぐ。
    parent_group = sample_edit.parentWidget()
    if isinstance(parent_group, QGroupBox):
        parent_group.setMinimumHeight(max(parent_group.minimumHeight(), 90))
        parent_group.updateGeometry()

    layout = dialog.layout()
    if layout is not None:
        layout.activate()
    dialog.adjustSize()


def choose_font(parent: Optional[QWidget], initial_font: QFont) -> Optional[QFont]:
    """Effects を非表示にしたフォントダイアログを表示し、選択フォントを返す。"""
    dialog = QFontDialog(parent)
    dialog.setCurrentFont(initial_font)
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    _hide_effect_controls(dialog)
    _stabilize_sample_preview(dialog)
    dialog.resize(540, dialog.height())

    if dialog.exec() != QFontDialog.Accepted:
        return None

    selected = dialog.selectedFont()
    if not isinstance(selected, QFont):
        return None

    # FTIVでは現時点で未対応のため、誤ってONでも常に無効化する。
    selected.setUnderline(False)
    selected.setStrikeOut(False)
    return selected
