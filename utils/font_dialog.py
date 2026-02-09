from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFontDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListView,
    QWidget,
)


def _safe_height(widget: object) -> int:
    """height() を安全に int 化する。モックオブジェクト対策を含む。"""
    try:
        value = widget.height()
    except Exception:
        return 0
    try:
        return int(value)
    except Exception:
        return 0


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


def _detect_top_columns(dialog: QFontDialog) -> list[tuple[int, QLabel, QWidget]]:
    """QFontDialog上段の列候補を x 座標順で返す。"""
    # ラベル文言に依存せず、上段の「ラベル + buddy」列の中央列を Style とみなす。
    dialog_height = max(
        _safe_height(dialog), _safe_height(dialog.sizeHint()), _safe_height(dialog.minimumSizeHint()), 1
    )
    top_row_limit = int(dialog_height * 0.45)

    top_columns: list[tuple[int, QLabel, QWidget]] = []
    for label in dialog.findChildren(QLabel):
        buddy = label.buddy()
        if buddy is None:
            continue
        if not isinstance(buddy, (QLineEdit, QAbstractItemView)):
            continue
        lg = label.geometry()
        if lg.isNull():
            continue
        if lg.y() > top_row_limit:
            continue
        top_columns.append((lg.x(), label, buddy))

    top_columns.sort(key=lambda col: col[0])
    if len(top_columns) < 3:
        return []

    # 近接重複を除いた上で、左から3列（Family/Style/Size）を採用する。
    unique_columns: list[tuple[int, QLabel, QWidget]] = []
    for x, label, buddy in top_columns:
        if unique_columns and abs(x - unique_columns[-1][0]) < 20:
            continue
        unique_columns.append((x, label, buddy))
        if len(unique_columns) == 3:
            break

    return unique_columns


def _hide_style_controls(dialog: QFontDialog) -> Optional[tuple[int, int]]:
    """QFontDialog の Style 列をロケール非依存で非表示にする。"""
    dialog_height = max(
        _safe_height(dialog), _safe_height(dialog.sizeHint()), _safe_height(dialog.minimumSizeHint()), 1
    )
    top_row_limit = int(dialog_height * 0.45)

    unique_columns = _detect_top_columns(dialog)
    if len(unique_columns) < 3:
        return None

    x0, _, _ = unique_columns[0]
    x1, style_label, style_buddy = unique_columns[1]
    x2, size_label, _ = unique_columns[2]
    if not (x0 + 20 <= x1 and x1 + 20 <= x2):
        return None

    style_x = style_label.geometry().x()
    style_right = size_label.geometry().x() - 6
    if style_right <= style_x:
        bg = style_buddy.geometry()
        style_right = bg.x() + bg.width() + 6

    style_label.hide()
    style_buddy.hide()

    # 同一カラムにあるスタイル入力欄/リストを追加で隠す。
    for editor in dialog.findChildren(QLineEdit):
        if editor.objectName() == "qt_fontDialog_sampleEdit":
            continue
        eg = editor.geometry()
        if eg.isNull():
            continue
        if eg.y() > top_row_limit:
            continue
        if eg.x() < style_x - 6:
            continue
        if eg.x() > style_right + 8:
            continue
        editor.hide()

    return style_x, style_right


def _relocate_writing_system_controls(dialog: QFontDialog, style_bounds: Optional[tuple[int, int]]) -> None:
    """Writing System を Style 列の空き領域へ移動する。"""
    if style_bounds is None:
        return

    layout = dialog.layout()
    if not isinstance(layout, QGridLayout):
        return

    ws_label: Optional[QLabel] = None
    ws_combo: Optional[QComboBox] = None
    for label in dialog.findChildren(QLabel):
        buddy = label.buddy()
        if isinstance(buddy, QComboBox):
            ws_label = label
            ws_combo = buddy
            break

    if ws_label is None or ws_combo is None:
        return

    # Style列の幅を基準に Writing System の横幅を決める。
    style_x, style_right = style_bounds
    target_width = max(120, min(220, style_right - style_x))

    # 既存行から外して、Style列上段へ再配置する。
    layout.removeWidget(ws_label)
    layout.removeWidget(ws_combo)
    layout.addWidget(ws_label, 0, 2, 1, 1)
    layout.addWidget(ws_combo, 1, 2, 1, 1)

    ws_label.setFixedWidth(target_width)
    ws_combo.setFixedWidth(target_width)
    layout.setColumnMinimumWidth(2, target_width)


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


def _expand_font_selection_area(dialog: QFontDialog) -> None:
    """Style列の空きに合わせ、Font一覧だけを縦方向に拡張する。"""
    layout = dialog.layout()
    if not isinstance(layout, QGridLayout):
        return

    visible_lists = [view for view in dialog.findChildren(QListView) if view.isVisible()]
    if len(visible_lists) < 2:
        return

    visible_lists.sort(key=lambda view: view.geometry().x())
    font_list = visible_lists[0]
    size_list = visible_lists[-1]

    # Size一覧は従来高さを維持して、Font一覧だけを拡張する。
    size_list.setFixedHeight(max(size_list.height(), size_list.minimumSizeHint().height()))

    # Sample欄が連動して伸びないよう、高さを固定する。
    sample_edit = dialog.findChild(QLineEdit, "qt_fontDialog_sampleEdit")
    if sample_edit is not None:
        sample_group = sample_edit.parentWidget()
        if isinstance(sample_group, QGroupBox):
            sample_group.setFixedHeight(max(sample_group.minimumHeight(), 90))

    # Font一覧を下段空き行まで広げる（rows 2-7）。
    layout.removeWidget(font_list)
    layout.addWidget(font_list, 2, 0, 6, 1)
    font_list.setMinimumHeight(max(font_list.minimumHeight(), font_list.sizeHint().height() + 60))

    # Size一覧は元の位置・行スパンに戻しておく（反復適用でも崩れない）。
    layout.removeWidget(size_list)
    layout.addWidget(size_list, 2, 4, 1, 1)

    # Font一覧側に余白伸長を寄せる。
    layout.setRowStretch(2, 1)
    layout.setRowStretch(5, 1)
    layout.setRowStretch(7, 1)

    layout.activate()


def _apply_dialog_layout_policy(dialog: QFontDialog) -> None:
    """FTIV方針に合わせてフォントダイアログの表示要素とサイズを整える。"""
    _hide_effect_controls(dialog)
    style_bounds = _hide_style_controls(dialog)
    _relocate_writing_system_controls(dialog, style_bounds)
    _stabilize_sample_preview(dialog)
    _expand_font_selection_area(dialog)
    dialog.resize(540, dialog.height())


def choose_font(parent: Optional[QWidget], initial_font: QFont) -> Optional[QFont]:
    """Effects を非表示にしたフォントダイアログを表示し、選択フォントを返す。"""
    dialog = QFontDialog(parent)
    dialog.setCurrentFont(initial_font)
    dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
    _hide_effect_controls(dialog)
    _stabilize_sample_preview(dialog)
    dialog.resize(540, dialog.height())
    QTimer.singleShot(0, lambda: _apply_dialog_layout_policy(dialog))

    if dialog.exec() != QFontDialog.Accepted:
        return None

    selected = dialog.selectedFont()
    if not isinstance(selected, QFont):
        return None

    # FTIVでは現時点で未対応のため、誤ってONでも常に無効化する。
    selected.setUnderline(False)
    selected.setStrikeOut(False)
    return selected
