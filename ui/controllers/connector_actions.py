# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog

from utils.error_reporter import ErrorNotifyState, report_unexpected_error
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from windows.connector import ConnectorLine

from models.constants import AppDefaults


class ConnectorActions:
    """
    Connections（ConnectorLine/ConnectorLabel）関連の操作ロジックを MainWindow から分離する。
    UI部品（ボタン等）には触らず、主に「選択中に対する操作」を担当する。
    """

    def __init__(self, mw: MainWindow) -> None:
        """ConnectorActions を初期化する。

        Args:
            mw (Any): MainWindow 相当（親・状態・UI参照を保持）。
        """
        self.mw = mw
        self._err_state: ErrorNotifyState = ErrorNotifyState()

    def _get_selected_line(self) -> Optional[ConnectorLine]:
        line = getattr(self.mw, "last_selected_connector", None)
        if line is not None:
            return line

        obj = getattr(self.mw, "last_selected_window", None)
        if obj is None:
            return None

        # ConnectorLine 判定（循環import耐性のため名前でも判定）
        try:
            from windows.connector import ConnectorLine

            if isinstance(obj, ConnectorLine):
                return obj
        except Exception:
            if type(obj).__name__ == "ConnectorLine":
                return obj

        return None

    def delete_selected(self) -> None:
        """選択中の ConnectorLine を削除する。"""
        line = self._get_selected_line()
        if line is None:
            return

        try:
            if hasattr(line, "delete_line"):
                line.delete_line()
            else:
                line.close()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to delete connector.", e, self._err_state)

        # UI/状態のリセット（MainWindow側の変数は維持しているのでここで落とす）
        try:
            if hasattr(self.mw, "connections_tab"):
                self.mw.connections_tab.on_selection_changed(None)
            else:
                self.mw.last_selected_connector = None
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to reset connector UI state.", e, self._err_state)

    def change_color_selected(self) -> None:
        """選択中 ConnectorLine の線色を変更する。"""
        line = self._get_selected_line()
        if line is None:
            return

        try:
            current = getattr(line, "line_color", None)
            color = QColorDialog.getColor(current, self.mw)
            if not color.isValid():
                return

            line.line_color = color
            if hasattr(line, "update"):
                line.update()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to change connector color.", e, self._err_state)

    def open_width_dialog_selected(self) -> None:
        """選択中 ConnectorLine の線幅を変更する（プレビュー中Undoなし、OKで1回Undo）。"""
        line = self._get_selected_line()
        if line is None:
            return

        try:
            from ui.dialogs import PreviewCommitDialog

            # Default width fallback
            old_val: int = int(getattr(line, "line_width", AppDefaults.CONNECTOR_WIDTH))

            def on_preview(val: float) -> None:
                try:
                    line.line_width = int(val)
                    if hasattr(line, "update_position"):
                        line.update_position()
                    else:
                        line.update()
                except Exception:
                    pass

            def on_commit(val: float) -> None:
                try:
                    new_val: int = int(val)
                    if new_val == old_val:
                        return

                    if hasattr(self.mw, "undo_stack"):
                        try:
                            self.mw.undo_stack.beginMacro("Change Connector Width")
                        except Exception:
                            pass

                    try:
                        from utils.commands import PropertyChangeCommand

                        # 確定値を適用
                        line.line_width = new_val
                        if hasattr(line, "update_position"):
                            line.update_position()
                        else:
                            line.update()

                        # Undo登録（lineに set_undoable_property が無いので Command を直接積む）
                        if hasattr(self.mw, "undo_stack"):
                            self.mw.undo_stack.push(
                                PropertyChangeCommand(line, "line_width", old_val, new_val, "update_position")
                            )
                    finally:
                        if hasattr(self.mw, "undo_stack"):
                            try:
                                self.mw.undo_stack.endMacro()
                            except Exception:
                                pass
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to commit connector width.", e, self._err_state)

            dialog = PreviewCommitDialog(
                tr("title_line_width"),
                tr("label_line_width"),
                1,
                50,
                old_val,
                on_preview,
                on_commit,
                self.mw,
            )
            dialog.exec()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open connector width dialog.", e, self._err_state)

    def open_opacity_dialog_selected(self) -> None:
        """選択中 ConnectorLine の不透明度（alpha）を変更（プレビュー中Undoなし、OKで1回Undo）。"""
        line = self._get_selected_line()
        if line is None:
            return

        try:
            from ui.dialogs import PreviewCommitDialog
            from utils.commands import PropertyChangeCommand

            base: Any = getattr(line, "line_color", None)
            if base is None:
                return

            old_qc: QColor = QColor(base)
            old_pct: int = int(old_qc.alpha() / 255 * 100)

            def _apply_pct(pct: int) -> None:
                try:
                    qc = QColor(old_qc)
                    qc.setAlpha(int(pct / 100 * 255))
                    if hasattr(line, "set_line_color"):
                        line.set_line_color(qc)
                    else:
                        line.line_color = qc
                        line.update()
                except Exception:
                    pass

            def on_preview(val: float) -> None:
                _apply_pct(int(val))

            def on_commit(val: float) -> None:
                try:
                    new_pct: int = int(val)
                    if new_pct == old_pct:
                        return

                    new_qc = QColor(old_qc)
                    new_qc.setAlpha(int(new_pct / 100 * 255))

                    if hasattr(self.mw, "undo_stack"):
                        try:
                            self.mw.undo_stack.beginMacro("Change Connector Opacity")
                        except Exception:
                            pass

                    try:
                        # 確定値を適用
                        if hasattr(line, "set_line_color"):
                            line.set_line_color(new_qc)
                        else:
                            line.line_color = new_qc
                            line.update()

                        # Undo登録
                        if hasattr(self.mw, "undo_stack"):
                            self.mw.undo_stack.push(PropertyChangeCommand(line, "line_color", old_qc, new_qc, "update"))
                    finally:
                        if hasattr(self.mw, "undo_stack"):
                            try:
                                self.mw.undo_stack.endMacro()
                            except Exception:
                                pass

                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to commit connector opacity.", e, self._err_state)

            dialog = PreviewCommitDialog(
                tr("title_line_opacity"),
                tr("label_opacity"),
                0,
                100,
                old_pct,
                on_preview,
                on_commit,
                self.mw,
                "%",
                decimals=0,
            )
            dialog.exec()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open connector opacity dialog.", e, self._err_state)

    def label_action_selected(self, action: str) -> None:
        """
        選択中コネクタのラベル操作。

        Args:
            action (str):
                - "edit": ラベルを表示して編集
                - "toggle": ラベル表示/非表示（textを""にして非表示化）
        """
        line = self._get_selected_line()
        if line is None:
            return

        label = getattr(line, "label_window", None)
        if label is None:
            return

        if action == "edit":
            try:
                if label.isHidden():
                    label.show()
                if hasattr(label, "raise_"):
                    label.raise_()
                if hasattr(label, "edit_text_realtime"):
                    label.edit_text_realtime()
            except Exception as e:
                report_unexpected_error(self.mw, "Failed to edit connector label.", e, self._err_state)
            return

        if action == "toggle":
            try:
                current_text = ""
                try:
                    current_text = str(getattr(label, "text", "") or "")
                except Exception:
                    current_text = ""

                if current_text.strip():
                    # OFF（消す）
                    try:
                        if hasattr(label, "set_undoable_property"):
                            label.set_undoable_property("text", "", "update_text")
                        else:
                            try:
                                label.text = ""
                            except Exception:
                                pass
                            if hasattr(label, "update_text"):
                                label.update_text()
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to clear connector label text.", e, self._err_state)

                    try:
                        if hasattr(label, "hide_action"):
                            label.hide_action()
                        else:
                            label.hide()
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to hide connector label.", e, self._err_state)

                else:
                    # ON（空だと何も出ないので編集へ）
                    try:
                        if label.isHidden():
                            label.show()
                        if hasattr(label, "raise_"):
                            label.raise_()
                        if hasattr(label, "edit_text_realtime"):
                            label.edit_text_realtime()
                    except Exception as e:
                        report_unexpected_error(
                            self.mw, "Failed to show connector label for editing.", e, self._err_state
                        )

                # 位置と表示の再評価
                try:
                    if hasattr(line, "update_position"):
                        line.update_position()
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to update connector position after label toggle.", e, self._err_state
                    )

            except Exception as e:
                report_unexpected_error(self.mw, "Failed to toggle connector label.", e, self._err_state)

    def set_arrow_style_selected(self, style_key: str) -> None:
        """選択中コネクタの ArrowStyle を変更する。

        Args:
            style_key (str): none|start|end|both
        """
        line = self._get_selected_line()
        if line is None:
            return

        try:
            from models.enums import ArrowStyle

            mapping = {
                "none": ArrowStyle.NONE,
                "start": ArrowStyle.START,
                "end": ArrowStyle.END,
                "both": ArrowStyle.BOTH,
            }
            if style_key not in mapping:
                return

            if hasattr(line, "set_arrow_style"):
                line.set_arrow_style(mapping[style_key])
            else:
                line.arrow_style = mapping[style_key]

            if hasattr(line, "update_position"):
                line.update_position()
            else:
                line.update()

        except Exception as e:
            # enum import できない場合でも落ちないようにフォールバック
            try:
                line.arrow_style = style_key
                if hasattr(line, "update_position"):
                    line.update_position()
                else:
                    line.update()
            except Exception as e2:
                report_unexpected_error(self.mw, "Failed to set arrow style (fallback).", e2, self._err_state)

            report_unexpected_error(self.mw, "Failed to set arrow style.", e, self._err_state)

        # UIのチェック同期は MainWindow の既存ロジックに寄せる（安全）
        try:
            if hasattr(self.mw, "connections_tab"):
                self.mw.connections_tab.on_selection_changed(getattr(self.mw, "last_selected_window", None))
            elif hasattr(self.mw, "_conn_on_selection_changed"):
                self.mw._conn_on_selection_changed(getattr(self.mw, "last_selected_window", None))
        except Exception as e:
            report_unexpected_error(
                self.mw, "Failed to refresh connector UI after arrow style change.", e, self._err_state
            )

    def _get_all_lines(self) -> list[ConnectorLine]:
        """全コネクタから ConnectorLine のみを抽出して返す。

        Returns:
            list[ConnectorLine]: ConnectorLine のリスト。
        """
        try:
            connectors: list[Any] = []
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "connectors"):
                connectors = list(getattr(self.mw.window_manager, "connectors", []))
            elif hasattr(self.mw, "connectors"):
                connectors = list(getattr(self.mw, "connectors", []))

            lines: list[ConnectorLine] = []
            for c in connectors:
                if c is None:
                    continue
                try:
                    from windows.connector import ConnectorLine

                    if isinstance(c, ConnectorLine):
                        lines.append(c)
                except Exception:
                    if type(c).__name__ == "ConnectorLine":
                        lines.append(c)

            return lines
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to collect connectors.", e, self._err_state)
            return []

    def bulk_change_color(self) -> None:
        """全コネクタの線色を一括変更する（alpha込みで統一）。"""
        lines = self._get_all_lines()
        if not lines:
            return

        try:
            current = getattr(lines[0], "line_color", None)
            color = QColorDialog.getColor(current, self.mw, options=QColorDialog.ShowAlphaChannel)
            if not color.isValid():
                return

            for line in lines:
                try:
                    # QColor はコピーして渡す（参照共有を避ける）
                    c = QColor(color)

                    if hasattr(line, "set_line_color"):
                        line.set_line_color(c)
                    else:
                        line.line_color = c
                        if hasattr(line, "update"):
                            line.update()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to apply bulk connector color.", e, self._err_state)

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk connector color dialog.", e, self._err_state)

    def bulk_open_width_dialog(self) -> None:
        """全コネクタの線幅を一括変更する。"""
        lines = self._get_all_lines()
        if not lines:
            return

        try:
            from ui.dialogs import SliderSpinDialog

            def cb(val: int) -> None:
                for line in lines:
                    try:
                        line.line_width = int(val)
                        if hasattr(line, "update_position"):
                            line.update_position()
                        else:
                            line.update()
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to apply bulk connector width.", e, self._err_state)

            current = int(getattr(lines[0], "line_width", AppDefaults.CONNECTOR_WIDTH))
            dialog = SliderSpinDialog(
                tr("title_line_width"),
                tr("label_line_width"),
                1,
                50,
                current,
                cb,
                self.mw,
            )
            dialog.exec()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk connector width dialog.", e, self._err_state)

    def bulk_open_opacity_dialog(self) -> None:
        """全コネクタの不透明度（alpha）を一括変更する。"""
        lines = self._get_all_lines()
        if not lines:
            return

        try:
            from ui.dialogs import SliderSpinDialog

            c0 = getattr(lines[0], "line_color", None)
            if c0 is None:
                return
            current = int(c0.alpha() / 255 * 100)

            def cb(val: int) -> None:
                for line in lines:
                    try:
                        base = getattr(line, "line_color", None)
                        if base is None:
                            continue

                        c = QColor(base)
                        c.setAlpha(int(val / 100 * 255))

                        if hasattr(line, "set_line_color"):
                            line.set_line_color(c)
                        else:
                            line.line_color = c
                            if hasattr(line, "update_position"):
                                line.update_position()
                            else:
                                line.update()
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to apply bulk connector opacity.", e, self._err_state)

            dialog = SliderSpinDialog(
                tr("title_line_opacity"),
                tr("label_opacity"),
                0,
                100,
                current,
                cb,
                self.mw,
            )
            dialog.exec()

        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk connector opacity dialog.", e, self._err_state)
