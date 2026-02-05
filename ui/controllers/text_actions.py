# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Optional

from utils.error_reporter import ErrorNotifyState, report_unexpected_error
from utils.translator import tr

logger = logging.getLogger(__name__)


class TextActions:
    """
    TextWindow / ConnectorLabel に対する「操作」系ロジックを MainWindow から分離する。
    方針:
    - UI同期（Selectedラベル更新 / enabled切替 / チェック同期）は MainWindow 側に残す
    - ここは "実行" に専念（clone, save json, save png など）
    """

    def __init__(self, mw: Any) -> None:
        """TextActions を初期化する。

        Args:
            mw (Any): MainWindow 相当（状態・各manager・UI参照を保持）。
        """
        self.mw = mw
        self._err_state: ErrorNotifyState = ErrorNotifyState()

    def _get_selected_obj(self) -> Optional[Any]:
        return getattr(self.mw, "last_selected_window", None)

    def _is_text_window(self, obj: Any) -> bool:
        try:
            from windows.text_window import TextWindow

            return isinstance(obj, TextWindow)
        except Exception:
            return type(obj).__name__ == "TextWindow"

    def _is_text_like(self, obj: Any) -> bool:
        try:
            from windows.connector import ConnectorLabel
            from windows.text_window import TextWindow

            return isinstance(obj, (TextWindow, ConnectorLabel))
        except Exception:
            return type(obj).__name__ in ("TextWindow", "ConnectorLabel")

    def add_new_text_window(self) -> None:
        """テキストウィンドウを追加する（制限到達時は何もしない）。"""
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.add_text_window()

    def clone_selected(self) -> None:
        """
        選択中が TextWindow のときのみクローンする。
        ConnectorLabel は対象外（コネクタ付属要素のため）。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_window(w):
            return

        try:
            w.clone_text()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to clone TextWindow.", e, self._err_state)

    def save_selected_to_json(self) -> None:
        """
        選択中が TextWindow / ConnectorLabel のとき、個別設定を JSON に保存する。
        ※「シーン保存」ではなく「このウィンドウだけ保存」用途。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_like(w):
            return

        fm: Any = getattr(self.mw, "file_manager", None)
        if fm is None:
            return

        try:
            fm.save_window_to_json(w)
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to save selected text object as JSON.", e, self._err_state)

    def save_png_selected(self) -> None:
        """
        選択中が TextWindow のとき、描画結果を PNG 保存する。
        ConnectorLabel は対象外。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_window(w):
            return

        try:
            w.save_as_png()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to save TextWindow as PNG.", e, self._err_state)

    def hide_other_text_windows(self) -> None:
        """
        選択中（TextWindow）のみ残して、他のTextWindowを hide_action() する。
        注意: ConnectorLabel 選択時は何もしない。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_window(w):
            return

        try:
            windows: list[Any] = []
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "text_windows"):
                windows = list(getattr(self.mw.window_manager, "text_windows", []))
            elif hasattr(self.mw, "text_windows"):
                windows = list(getattr(self.mw, "text_windows", []))

            for tw in windows:
                if tw is None or tw is w:
                    continue
                try:
                    if hasattr(tw, "is_hidden") and not tw.is_hidden:
                        tw.hide_action()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to hide a TextWindow (others).", e, self._err_state)
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to hide other TextWindows.", e, self._err_state)

    def show_other_text_windows(self) -> None:
        """
        選択中（TextWindow）のみ基準にして、他のTextWindowを show_action() する。
        注意: ConnectorLabel 選択時は何もしない。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_window(w):
            return

        try:
            windows: list[Any] = []
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "text_windows"):
                windows = list(getattr(self.mw.window_manager, "text_windows", []))
            elif hasattr(self.mw, "text_windows"):
                windows = list(getattr(self.mw, "text_windows", []))

            for tw in windows:
                if tw is None or tw is w:
                    continue
                try:
                    if hasattr(tw, "is_hidden") and tw.is_hidden:
                        tw.show_action()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to show a TextWindow (others).", e, self._err_state)
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to show other TextWindows.", e, self._err_state)

    def close_other_text_windows(self) -> None:
        """
        選択中（TextWindow）のみ残して、他のTextWindowを close() する。
        注意: ConnectorLabel 選択時は何もしない。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_window(w):
            return

        try:
            windows: list[Any] = []
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "text_windows"):
                windows = list(getattr(self.mw.window_manager, "text_windows", []))
            elif hasattr(self.mw, "text_windows"):
                windows = list(getattr(self.mw, "text_windows", []))

            for tw in windows:
                if tw is None or tw is w:
                    continue
                try:
                    tw.close()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to close a TextWindow (others).", e, self._err_state)
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to close other TextWindows.", e, self._err_state)

    def run_selected_visibility_action(self, action: str, checked: Optional[bool] = None) -> None:
        """
        Textタブの Selected（last_selected_window）が TextWindow / ConnectorLabel のときに、
        Visibility系アクションを実行する。

        Args:
            action (str):
                - "show"
                - "hide"
                - "frontmost"
                - "click_through"
                - "close"
            checked (Optional[bool]): toggle系の明示状態（UIのチェック状態）を渡す。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_like(w):
            return

        is_label: bool = False
        try:
            from windows.connector import ConnectorLabel

            is_label = isinstance(w, ConnectorLabel)
        except Exception:
            is_label = type(w).__name__ == "ConnectorLabel"

        try:
            if action == "show":
                try:
                    if hasattr(w, "show_action"):
                        w.show_action()
                    else:
                        w.show()
                    if hasattr(w, "raise_"):
                        w.raise_()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to show selected text object.", e, self._err_state)

            elif action == "hide":
                try:
                    if hasattr(w, "hide_action"):
                        w.hide_action()
                    else:
                        w.hide()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to hide selected text object.", e, self._err_state)

            elif action == "frontmost":
                try:
                    if checked is not None:
                        setattr(w, "is_frontmost", bool(checked))
                    else:
                        if hasattr(w, "toggle_frontmost"):
                            w.toggle_frontmost()
                        else:
                            cur = bool(getattr(w, "is_frontmost", False))
                            setattr(w, "is_frontmost", not cur)
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to toggle frontmost for selected text object.", e, self._err_state
                    )

            elif action == "click_through":
                try:
                    if checked is not None:
                        setattr(w, "is_click_through", bool(checked))
                    else:
                        cur = bool(getattr(w, "is_click_through", False))
                        setattr(w, "is_click_through", not cur)
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to toggle click-through for selected text object.", e, self._err_state
                    )

            elif action == "close":
                try:
                    if is_label:
                        # ConnectorLabel はラベルのみ消す（text=""）＋ hide
                        if hasattr(w, "set_undoable_property"):
                            w.set_undoable_property("text", "", "update_text")
                        else:
                            try:
                                setattr(w, "text", "")
                            except Exception:
                                pass
                            if hasattr(w, "update_text"):
                                w.update_text()

                        if hasattr(w, "hide_action"):
                            w.hide_action()
                        else:
                            w.hide()
                    else:
                        w.close()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to close selected text object.", e, self._err_state)

            # UIのチェック状態を実状態に寄せる（MainWindow 側の既存ロジックを呼ぶ）
            try:
                if hasattr(self.mw, "text_tab"):
                    self.mw.text_tab.on_selection_changed(getattr(self.mw, "last_selected_window", None))
            except Exception as e:
                report_unexpected_error(
                    self.mw, "Failed to refresh Text tab UI after visibility action.", e, self._err_state
                )

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in text visibility action.", e, self._err_state)

    def save_as_default(self) -> None:
        """選択中のウィンドウのスタイル（外見設定）をグローバルデフォルト（Archetype）として保存する。"""
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_like(w):
            return

        try:
            # Pydanticモデルからシリアライズ
            # 除外リスト: インスタンス固有のデータ
            exclude = {
                "uuid",
                "parent_uuid",
                "position",
                "text",
                "text_visible",
                "is_hidden",
                "is_locked",
                "connected_lines",
            }

            # config からデータを抽出
            if hasattr(w, "config"):
                config_data = w.config.model_dump(mode="json", exclude=exclude)
            else:
                return

            # SettingsManager 経由で保存
            if hasattr(self.mw, "settings_manager"):
                success = self.mw.settings_manager.save_text_archetype(config_data)
                if success:
                    if hasattr(self.mw, "show_status_message"):
                        self.mw.show_status_message(tr("msg_settings_saved_applied"))
                    else:
                        # フォールバック
                        logger.info("Default archetype saved successfully.")
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to save style as default.", e, self._err_state)

    def run_selected_layout_action(self, action: str, checked: Optional[bool] = None) -> None:
        """
        Textタブの Selected（TextWindow / ConnectorLabel）に対して、
        縦書き・TypeA/B・余白ダイアログを適用する。

        Args:
            action (str):
                - "set_vertical"（checked必須）
                - "set_offset_mode_mono"
                - "set_offset_mode_prop"
                - "open_spacing_settings"
            checked (Optional[bool]): "set_vertical" のときに必須。
        """
        w: Optional[Any] = self._get_selected_obj()
        if w is None or not self._is_text_like(w):
            return

        try:
            if action == "set_vertical":
                if checked is None:
                    return
                try:
                    if hasattr(w, "set_undoable_property"):
                        w.set_undoable_property("is_vertical", bool(checked), "update_text")
                    else:
                        setattr(w, "is_vertical", bool(checked))
                        if hasattr(w, "update_text"):
                            w.update_text()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to set vertical mode.", e, self._err_state)

            elif action in ("set_offset_mode_mono", "set_offset_mode_prop"):
                try:
                    from models.enums import OffsetMode

                    target_mode = OffsetMode.MONO if action == "set_offset_mode_mono" else OffsetMode.PROP

                    # 既存の正式ルートがあるなら優先
                    if target_mode == OffsetMode.MONO and hasattr(w, "set_offset_mode_a"):
                        w.set_offset_mode_a()
                    elif target_mode == OffsetMode.PROP and hasattr(w, "set_offset_mode_b"):
                        w.set_offset_mode_b()
                    else:
                        if hasattr(w, "set_undoable_property"):
                            w.set_undoable_property("offset_mode", target_mode, "update_text")
                        else:
                            setattr(w, "offset_mode", target_mode)
                            if hasattr(w, "update_text"):
                                w.update_text()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to set offset mode.", e, self._err_state)

            elif action == "open_spacing_settings":
                try:
                    if hasattr(w, "open_spacing_settings"):
                        w.open_spacing_settings()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to open spacing settings.", e, self._err_state)

            # UIのチェック状態を実状態に寄せる
            try:
                if hasattr(self.mw, "text_tab"):
                    self.mw.text_tab.on_selection_changed(getattr(self.mw, "last_selected_window", None))
            except Exception as e:
                report_unexpected_error(
                    self.mw, "Failed to refresh Text tab UI after layout action.", e, self._err_state
                )

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in text layout action.", e, self._err_state)
