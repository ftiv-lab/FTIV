# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from utils.error_reporter import ErrorNotifyState, report_unexpected_error
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from windows.image_window import ImageWindow


class ImageActions:
    """
    ImageWindow に対する「操作」ロジックを MainWindow から分離する。
    UI同期（Selectedラベル更新/チェック同期/enabled切替）は MainWindow 側に残す。
    """

    def __init__(self, mw: MainWindow) -> None:
        """ImageActions を初期化する。

        Args:
            mw (MainWindow): MainWindow 相当（状態・各manager・UI参照を保持）。
        """
        self.mw = mw
        self._err_state: ErrorNotifyState = ErrorNotifyState()

    def _get_selected_image(self) -> Optional[ImageWindow]:
        w = getattr(self.mw, "last_selected_window", None)
        if w is None:
            return None
        try:
            from windows.image_window import ImageWindow

            return w if isinstance(w, ImageWindow) else None
        except Exception:
            return w if type(w).__name__ == "ImageWindow" else None

    def add_new_image(self) -> None:
        """ファイル選択ダイアログを開いて画像を追加。"""
        try:
            from PySide6.QtWidgets import QFileDialog

            # last_directory アクセス
            last_dir = getattr(self.mw, "last_directory", "")

            path, _ = QFileDialog.getOpenFileName(
                self.mw,
                tr("title_select_new_image"),
                last_dir,
                "Images (*.png *.jpg *.jpeg *.png *.bmp *.webp *.tif *.gif *.ico *.tga)",
            )
            if path:
                self.add_image_from_path(path)

        except Exception as e:
            report_unexpected_error(self.mw, "Error adding image", e, self._err_state)

    def add_image_from_path(self, image_path: str) -> None:
        """画像追加の一元入口。"""
        import os

        if hasattr(self.mw, "last_directory"):
            self.mw.last_directory = os.path.dirname(image_path)

        try:
            if hasattr(self.mw, "window_manager"):
                self.mw.window_manager.add_image_window(image_path)
        except Exception as e:
            report_unexpected_error(self.mw, "Error adding image from path", e, self._err_state)

    def run_selected_transform_action(self, action: str) -> None:
        """
        Selected（最後にクリックした ImageWindow）に対して Transform を実行する。

        Args:
            action (str): "size" | "opacity" | "rotation"
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if action == "size" and hasattr(w, "open_size_dialog"):
                w.open_size_dialog()
            elif action == "opacity" and hasattr(w, "open_opacity_dialog"):
                w.open_opacity_dialog()
            elif action == "rotation" and hasattr(w, "open_rotation_dialog"):
                w.open_rotation_dialog()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to run selected image transform action.", e, self._err_state)

    def run_selected_visibility_action(self, action: str, checked: Optional[bool] = None) -> None:
        """
        Selected（最後にクリックした ImageWindow）に対して Visibility を実行する。

        Args:
            action (str): "show" | "hide" | "frontmost" | "click_through"
            checked (Optional[bool]): トグルUIから渡されるチェック状態（あれば）。
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

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
                    report_unexpected_error(self.mw, "Failed to show selected image.", e, self._err_state)

            elif action == "hide":
                try:
                    if hasattr(w, "hide_action"):
                        w.hide_action()
                    else:
                        w.hide()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to hide selected image.", e, self._err_state)

            elif action == "frontmost":
                try:
                    if checked is not None:
                        if hasattr(w, "set_frontmost"):
                            w.set_frontmost(bool(checked))
                        else:
                            cur = bool(getattr(w, "is_frontmost", False))
                            if cur != bool(checked) and hasattr(w, "toggle_frontmost"):
                                w.toggle_frontmost()
                    else:
                        for method_name in ["toggle_frontmost", "toggle_always_on_top", "toggle_topmost"]:
                            if hasattr(w, method_name):
                                getattr(w, method_name)()
                                break
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to toggle frontmost for selected image.", e, self._err_state
                    )

            elif action == "click_through":
                try:
                    if checked is not None:
                        if hasattr(w, "set_click_through"):
                            w.set_click_through(bool(checked))
                        else:
                            cur = bool(getattr(w, "is_click_through", False))
                            if cur != bool(checked) and hasattr(w, "toggle_click_through"):
                                w.toggle_click_through()
                    else:
                        for method_name in ["toggle_click_through", "toggle_click_through_mode"]:
                            if hasattr(w, method_name):
                                getattr(w, method_name)()
                                break
                        else:
                            if hasattr(w, "set_click_through"):
                                cur = bool(getattr(w, "is_click_through", False))
                                w.set_click_through(not cur)
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to toggle click-through for selected image.", e, self._err_state
                    )

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in image visibility action.", e, self._err_state)

        # UIのチェック表示を実状態に寄せる（保険）
        try:
            if hasattr(self.mw, "image_tab"):
                self.mw.image_tab.on_selection_changed(getattr(self.mw, "last_selected_window", None))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to refresh Image tab UI.", e, self._err_state)

    def close_selected_image(self) -> None:
        """画像タブの「Selectedを閉じる」。last_selected_window が ImageWindow のときだけ閉じる。"""
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if hasattr(w, "close_action"):
                w.close_action()
            else:
                w.close()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to close selected image.", e, self._err_state)

        # 選択表示が残らないようにする（保険）
        try:
            if getattr(self.mw, "last_selected_window", None) == w and hasattr(self.mw, "set_last_selected_window"):
                self.mw.set_last_selected_window(None)
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to reset selection after closing image.", e, self._err_state)

    def run_selected_playback_action(self, action: str) -> None:
        """
        Selected（最後にクリックした ImageWindow）に対して Playback 系アクションを実行する。

        Args:
            action (str):
                - "toggle": 再生/停止トグル
                - "speed":  再生速度ダイアログ
                - "reset":  再生速度リセット
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if action == "toggle":
                try:
                    if hasattr(w, "toggle_image_animation_speed"):
                        w.toggle_image_animation_speed()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to toggle selected image playback.", e, self._err_state)
                return

            if action == "speed":
                try:
                    if hasattr(w, "open_anim_speed_dialog"):
                        w.open_anim_speed_dialog()
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to open selected image playback speed dialog.", e, self._err_state
                    )
                return

            if action == "reset":
                try:
                    if hasattr(w, "reset_animation_speed"):
                        w.reset_animation_speed()
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to reset selected image playback speed.", e, self._err_state
                    )
                return

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in selected image playback action.", e, self._err_state)

    def run_selected_other_images_action(self, action: str) -> None:
        """
        Selected（最後にクリックした ImageWindow）を基準に、
        「他の画像を隠す/表示/閉じる」を実行する（右クリック準拠 + 復帰導線）。

        Args:
            action (str):
                - "hide_others": hide_all_other_windows()
                - "show_others": 選択中以外を表示（show_action() 優先）
                - "close_others": close_all_other_images()
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if action == "hide_others":
                try:
                    if hasattr(w, "hide_all_other_windows"):
                        w.hide_all_other_windows()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to hide other images.", e, self._err_state)
                return

            if action == "show_others":
                windows: list[Any] = []
                try:
                    if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "image_windows"):
                        windows = list(getattr(self.mw.window_manager, "image_windows", []))
                    elif hasattr(self.mw, "image_windows"):
                        windows = list(getattr(self.mw, "image_windows", []))
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to collect image windows.", e, self._err_state)
                    windows = []

                for win in windows:
                    if win is None or win is w:
                        continue
                    try:
                        if hasattr(win, "show_action"):
                            win.show_action()
                        else:
                            win.show()
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to show an image window (others).", e, self._err_state)
                return

            if action == "close_others":
                try:
                    if hasattr(w, "close_all_other_images"):
                        w.close_all_other_images()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to close other images.", e, self._err_state)
                return

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in other images action.", e, self._err_state)

    def set_selected_rotation_angle(self, angle: int) -> None:
        """
        Selected（最後にクリックした ImageWindow）の回転角度を指定角度に設定する。
        可能なら set_undoable_property ルートを優先（絶対角度）。

        Args:
            angle (int): 設定する角度（0-360想定）。
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            target_angle: int = int(angle)
        except Exception:
            return

        try:
            # Undo対応ルート優先
            if hasattr(w, "set_undoable_property"):
                try:
                    w.set_undoable_property("rotation_angle", float(target_angle), "update_image")
                    return
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to set image rotation via undoable property.", e, self._err_state
                    )

            # フォールバック
            if hasattr(w, "set_rotation_angle"):
                try:
                    w.set_rotation_angle(float(target_angle))
                except Exception as e:
                    report_unexpected_error(
                        self.mw, "Failed to set image rotation via fallback setter.", e, self._err_state
                    )

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in set_selected_rotation_angle.", e, self._err_state)

    def flip_selected(self, axis: str) -> None:
        """
        Selected（最後にクリックした ImageWindow）を反転する。

        Args:
            axis (str): "h" | "v"
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if axis == "h":
                for method_name in ["flip_horizontal_action", "flip_horizontal", "toggle_flip_horizontal"]:
                    if hasattr(w, method_name):
                        try:
                            getattr(w, method_name)()
                            return
                        except Exception as e:
                            report_unexpected_error(self.mw, "Failed to flip image horizontally.", e, self._err_state)
                return

            if axis == "v":
                for method_name in ["flip_vertical_action", "flip_vertical", "toggle_flip_vertical"]:
                    if hasattr(w, method_name):
                        try:
                            getattr(w, method_name)()
                            return
                        except Exception as e:
                            report_unexpected_error(self.mw, "Failed to flip image vertically.", e, self._err_state)
                return

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in flip_selected.", e, self._err_state)

    def reset_selected_transform(self, kind: str) -> None:
        """
        Selected（最後にクリックした ImageWindow）のTransform系をリセットする。

        Args:
            kind (str):
                - "size" | "opacity" | "rotation" | "flips"
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if kind == "size":
                if hasattr(w, "reset_image_size"):
                    try:
                        w.reset_image_size()
                        return
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to reset image size.", e, self._err_state)
                if hasattr(w, "set_undoable_property"):
                    try:
                        w.set_undoable_property("scale_factor", 1.0, "update_image")
                    except Exception as e:
                        report_unexpected_error(
                            self.mw, "Failed to reset scale via undoable property.", e, self._err_state
                        )
                return

            if kind == "opacity":
                if hasattr(w, "reset_opacity"):
                    try:
                        w.reset_opacity()
                        return
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to reset image opacity.", e, self._err_state)
                if hasattr(w, "set_undoable_property"):
                    try:
                        w.set_undoable_property("opacity", 1.0, "update_image")
                    except Exception as e:
                        report_unexpected_error(
                            self.mw, "Failed to reset opacity via undoable property.", e, self._err_state
                        )
                return

            if kind == "rotation":
                if hasattr(w, "reset_rotation"):
                    try:
                        w.reset_rotation()
                        return
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to reset image rotation.", e, self._err_state)
                if hasattr(w, "set_undoable_property"):
                    try:
                        w.set_undoable_property("rotation_angle", 0.0, "update_image")
                    except Exception as e:
                        report_unexpected_error(
                            self.mw, "Failed to reset rotation via undoable property.", e, self._err_state
                        )
                return

            if kind == "flips":
                if hasattr(w, "reset_flip"):
                    try:
                        w.reset_flip()
                        return
                    except Exception as e:
                        report_unexpected_error(self.mw, "Failed to reset image flips.", e, self._err_state)
                if hasattr(w, "set_undoable_property"):
                    try:
                        w.set_undoable_property("flip_horizontal", False, "update_image")
                        w.set_undoable_property("flip_vertical", False, "update_image")
                    except Exception as e:
                        report_unexpected_error(
                            self.mw, "Failed to reset flips via undoable property.", e, self._err_state
                        )
                return

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in reset_selected_transform.", e, self._err_state)

    def run_selected_manage_action(self, action: str) -> None:
        """
        画像タブ > Manage（Selected）操作を実行する。

        Args:
            action (str):
                - "reselect": 画像の再選択
                - "clone": 複製
                - "save_json": 個別設定をJSON保存（FileManagerへ委譲）
        """
        w: Optional[Any] = self._get_selected_image()
        if w is None:
            return

        try:
            if action == "reselect":
                try:
                    if hasattr(w, "reselect_image"):
                        w.reselect_image()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to reselect image.", e, self._err_state)
                return

            if action == "clone":
                try:
                    if hasattr(w, "clone_image"):
                        w.clone_image()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to clone image.", e, self._err_state)
                return

            if action == "save_json":
                try:
                    fm: Any = getattr(self.mw, "file_manager", None)
                    if fm is not None and hasattr(fm, "save_window_to_json"):
                        fm.save_window_to_json(w)
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to save image settings as JSON.", e, self._err_state)
                return

        except Exception as e:
            report_unexpected_error(self.mw, "Unexpected error in image manage action.", e, self._err_state)

    def get_selected_image(self) -> Optional[ImageWindow]:
        """現在選択中の ImageWindow を返す（外部用の公開API）。

        Returns:
            Optional[ImageWindow]: ImageWindow（未選択/対象外なら None）。
        """
        return self._get_selected_image()

    def fit_selected_to_display(self, screen_index: int) -> None:
        """選択中の ImageWindow を指定ディスプレイにフィットする。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
        """
        w: Optional[Any] = self.get_selected_image()
        if w is None:
            return

        try:
            if hasattr(w, "fit_to_display"):
                w.fit_to_display(int(screen_index))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to fit selected image to display.", e, self._err_state)

    def center_selected_on_display(self, screen_index: int) -> None:
        """選択中の ImageWindow を指定ディスプレイ中央に配置する。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
        """
        w: Optional[Any] = self.get_selected_image()
        if w is None:
            return

        try:
            if hasattr(w, "center_on_display"):
                w.center_on_display(int(screen_index))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to center selected image on display.", e, self._err_state)

    def snap_selected_to_display_edge(self, screen_index: int, edge: str) -> None:
        """選択中画像を指定ディスプレイの端へスナップする。"""
        w = self.get_selected_image()
        if w is None:
            return
        try:
            if hasattr(w, "snap_to_display_edge"):
                w.snap_to_display_edge(int(screen_index), str(edge))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to snap selected image to edge.", e, self._err_state)

    def snap_selected_to_display_corner(self, screen_index: int, corner: str) -> None:
        """選択中画像を指定ディスプレイの四隅へスナップする。"""
        w = self.get_selected_image()
        if w is None:
            return
        try:
            if hasattr(w, "snap_to_display_corner"):
                w.snap_to_display_corner(int(screen_index), str(corner))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to snap selected image to corner.", e, self._err_state)

    def normalize_all_images_by_selected(self, mode: str) -> None:
        """選択中 ImageWindow を基準に、全画像の scale_factor を揃える（前処理）。

        仕様:
            - 対象: 全 ImageWindow
            - 基準: 選択中（Selected）ImageWindow
            - 変更: scale_factor のみ（位置は触らない）
            - mode:
                - "same_pct": 選択中と同じ scale_factor にする
                - "same_width": 表示幅（window.width()）が選択中と同じになるよう scale_factor を調整
                - "same_height": 表示高さが選択中と同じになるよう scale_factor を調整

        Args:
            mode (str): "same_pct" | "same_width" | "same_height"
        """
        selected = self.get_selected_image()
        if selected is None:
            # 原則はUI側でdisabledにするが、保険で何もしない
            return

        # 全画像を取得
        wins: list[Any] = []
        try:
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "image_windows"):
                wins = list(getattr(self.mw.window_manager, "image_windows", []))
            elif hasattr(self.mw, "image_windows"):
                wins = list(getattr(self.mw, "image_windows", []))
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to collect image windows.", e, self._err_state)
            return

        if not wins:
            return

        # 基準値
        try:
            ref_scale: float = float(getattr(selected, "scale_factor", 1.0))
        except Exception:
            ref_scale = 1.0

        try:
            ref_w: int = int(selected.width())
            ref_h: int = int(selected.height())
        except Exception:
            ref_w = 1
            ref_h = 1

        if hasattr(self.mw, "undo_stack"):
            try:
                self.mw.undo_stack.beginMacro("Normalize Images")
            except Exception:
                pass

        try:
            for w in wins:
                if w is None:
                    continue

                try:
                    cur_scale: float = float(getattr(w, "scale_factor", 1.0))
                except Exception:
                    cur_scale = 1.0

                # 現在表示サイズ（回転は v1 では考慮しない）
                try:
                    cur_w: int = max(1, int(w.width()))
                    cur_h: int = max(1, int(w.height()))
                except Exception:
                    cur_w = 1
                    cur_h = 1

                new_scale: float = cur_scale

                if mode == "same_pct":
                    new_scale = ref_scale

                elif mode == "same_width":
                    # width を ref_w に合わせる
                    # new_scale = cur_scale * (ref_w / cur_w)
                    new_scale = cur_scale * (float(ref_w) / float(cur_w))

                elif mode == "same_height":
                    new_scale = cur_scale * (float(ref_h) / float(cur_h))

                else:
                    return

                # 極端な値を防ぐ（安全策）
                if not (0.001 <= float(new_scale) <= 1000.0):
                    continue

                # Undo対応ルート優先
                if hasattr(w, "set_undoable_property"):
                    try:
                        w.set_undoable_property("scale_factor", float(new_scale), "update_image")
                        continue
                    except Exception:
                        pass

                # フォールバック
                try:
                    if hasattr(w, "scale_factor"):
                        w.scale_factor = float(new_scale)
                    if hasattr(w, "update_image"):
                        w.update_image()
                except Exception as e:
                    report_unexpected_error(self.mw, "Failed to apply normalize scale to an image.", e, self._err_state)

        finally:
            if hasattr(self.mw, "undo_stack"):
                try:
                    self.mw.undo_stack.endMacro()
                except Exception:
                    pass

        # UI同期（選択中の表示/チェック等が崩れないように）
        try:
            if hasattr(self.mw, "_img_on_selection_changed"):
                self.mw._img_on_selection_changed(getattr(self.mw, "last_selected_window", None))
        except Exception:
            pass

    def _get_all_images(self) -> list[ImageWindow]:
        """全画像ウィンドウを取得する。"""
        try:
            if hasattr(self.mw, "window_manager") and hasattr(self.mw.window_manager, "image_windows"):
                return list(getattr(self.mw.window_manager, "image_windows", []))
            elif hasattr(self.mw, "image_windows"):
                return list(getattr(self.mw, "image_windows", []))
        except Exception:
            pass
        return []

    def set_all_image_opacity(self) -> None:
        """全画像の不透明度を一括変更（ダイアログ）。"""
        try:
            from ui.dialogs import SliderSpinDialog

            # Start from 100 or current average? Just 100 is fine
            def cb(val: int) -> None:
                self.set_all_image_opacity_realtime(val)

            dialog = SliderSpinDialog(
                tr("title_img_opacity"), tr("label_opacity"), 0, 100, 100, cb, self.mw, suffix="%"
            )
            dialog.exec()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk image opacity dialog.", e, self._err_state)

    def set_all_image_opacity_realtime(self, val: int) -> None:
        """全画像の不透明度を一括変更（リアルタイム）。"""
        wins = self._get_all_images()
        for w in wins:
            try:
                if w is None:
                    continue

                # Undoなしで直接適用（スライダー中は重いので）
                # 確定時にUndo積むのが理想だが、v1では簡易実装
                if hasattr(w, "set_opacity"):
                    w.set_opacity(float(val) / 100.0)
                elif hasattr(w, "opacity"):
                    w.opacity = float(val) / 100.0
                    if hasattr(w, "update_image"):
                        w.update_image()
            except Exception:
                pass

    def set_all_image_size_percentage(self) -> None:
        """全画像のサイズ（倍率）を一括変更（ダイアログ）。"""
        try:
            from ui.dialogs import SliderSpinDialog

            def cb(val: int) -> None:
                self.set_all_image_size_realtime(val)

            dialog = SliderSpinDialog(tr("title_img_size"), tr("label_size_pct"), 1, 300, 100, cb, self.mw, suffix="%")
            dialog.exec()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk image size dialog.", e, self._err_state)

    def set_all_image_size_realtime(self, val: int) -> None:
        """全画像のサイズを一括変更（リアルタイム）。"""
        wins = self._get_all_images()
        scale = float(val) / 100.0

        for w in wins:
            try:
                if w is None:
                    continue

                if hasattr(w, "scale_factor"):
                    w.scale_factor = scale
                if hasattr(w, "update_image"):
                    w.update_image()
            except Exception:
                pass

    def set_all_image_rotation(self) -> None:
        """全画像の回転を一括変更（ダイアログ）。"""
        try:
            from ui.dialogs import SliderSpinDialog

            def cb(val: int) -> None:
                self.set_all_image_rotation_realtime(val)

            dialog = SliderSpinDialog(
                tr("title_img_rotation"), tr("label_rotation"), 0, 360, 0, cb, self.mw, suffix="°"
            )
            dialog.exec()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk image rotation dialog.", e, self._err_state)

    def set_all_image_rotation_realtime(self, val: int) -> None:
        """全画像の回転を一括変更（リアルタイム）。"""
        wins = self._get_all_images()
        angle = float(val) % 360.0

        for w in wins:
            try:
                if w is None:
                    continue

                if hasattr(w, "set_rotation_angle"):
                    w.set_rotation_angle(angle)
            except Exception:
                pass

    def reset_all_flips(self) -> None:
        """全画像の反転状態をリセットする。"""
        wins = self._get_all_images()
        if hasattr(self.mw, "undo_stack"):
            self.mw.undo_stack.beginMacro("Reset All Flips")

        try:
            for w in wins:
                try:
                    if w is None:
                        continue
                    if hasattr(w, "reset_flip"):
                        w.reset_flip()
                    elif hasattr(w, "set_undoable_property"):
                        w.set_undoable_property("flip_horizontal", False, "update_image")
                        w.set_undoable_property("flip_vertical", False, "update_image")
                except Exception:
                    pass
        finally:
            if hasattr(self.mw, "undo_stack"):
                self.mw.undo_stack.endMacro()

    def reset_all_animation_speeds(self) -> None:
        """全画像の再生速度をリセット(100%)する。"""
        wins = self._get_all_images()
        for w in wins:
            try:
                if w is None:
                    continue
                if hasattr(w, "reset_animation_speed"):
                    w.reset_animation_speed()
            except Exception:
                pass

    def toggle_all_image_animation_speed(self) -> None:
        """全画像の再生/停止をトグルする（停止中なら再生、再生中なら停止）。

        仕様: 最初の1枚の状態を見て、それに合わせる（簡易）。
        """
        wins = self._get_all_images()
        if not wins:
            return

        # 1枚目の状態確認
        target_state_play = True
        try:
            first = wins[0]
            # 0なら停止中とみなして再生(original_speed)へ
            # 0以外なら再生中とみなして停止(0)へ
            current = getattr(first, "animation_speed_factor", 100)
            if current != 0:
                target_state_play = False
        except Exception:
            pass

        for w in wins:
            try:
                if w is None:
                    continue
                if target_state_play:
                    # 再生へ
                    if hasattr(w, "reset_animation_speed"):
                        w.reset_animation_speed()  # 元の速度に戻す
                else:
                    # 停止へ
                    if hasattr(w, "set_animation_speed_factor"):
                        w.set_animation_speed_factor(0)

            except Exception:
                pass

    def stop_all_image_animations(self) -> None:
        """全画像のアニメーションを停止する。"""
        wins = self._get_all_images()
        for w in wins:
            try:
                if w is None:
                    continue
                if hasattr(w, "set_animation_speed_factor"):
                    w.set_animation_speed_factor(0)
            except Exception:
                pass

    def set_all_gif_apng_playback_speed(self) -> None:
        """全画像の再生速度を一括変更（ダイアログ）。"""
        try:
            from ui.dialogs import SliderSpinDialog

            def cb(val: int) -> None:
                self.set_all_gif_apng_playback_speed_realtime(val)

            dialog = SliderSpinDialog(
                tr("title_anim_speed"), tr("label_anim_speed"), 0, 500, 100, cb, self.mw, suffix="%"
            )
            dialog.exec()
        except Exception as e:
            report_unexpected_error(self.mw, "Failed to open bulk playback speed dialog.", e, self._err_state)

    def set_all_gif_apng_playback_speed_realtime(self, val: int) -> None:
        """全画像の再生速度を一括変更（リアルタイム）。"""
        wins = self._get_all_images()
        for w in wins:
            try:
                if w is None:
                    continue
                if hasattr(w, "set_animation_speed_factor"):
                    w.set_animation_speed_factor(val)
            except Exception:
                pass

    def pack_all_left_top(self, screen_index: int, space: int = 0) -> None:
        """全 ImageWindow を指定ディスプレイの左上へ詰めて配置する（サイズは変更しない）。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
            space (int): セル間隔（px）。
        """
        from PySide6.QtWidgets import QApplication

        wins = self._get_all_images()
        if not wins:
            return

        screens = QApplication.screens()
        if not (0 <= screen_index < len(screens)):
            return

        target_screen = screens[screen_index]
        base_geo = target_screen.geometry()
        start_x = base_geo.x()
        start_y = base_geo.y()

        current_x = start_x + space
        current_y = start_y + space
        max_h_in_row = 0
        screen_w = base_geo.width()

        if hasattr(self.mw, "undo_stack"):
            try:
                self.mw.undo_stack.beginMacro("Pack Images Left-Top")
            except Exception:
                pass

        try:
            for w in wins:
                if w is None:
                    continue
                try:
                    w_width = w.width()
                    w_height = w.height()

                    # 右端を超えるなら改行
                    if current_x + w_width + space > start_x + screen_w:
                        current_x = start_x + space
                        current_y += max_h_in_row + space
                        max_h_in_row = 0

                    if hasattr(w, "set_undoable_property"):
                        w.set_undoable_property("position", {"x": current_x, "y": current_y}, "update_position")
                    else:
                        w.move(current_x, current_y)
                        if hasattr(w, "update_position"):
                            w.update_position()

                    current_x += w_width + space
                    max_h_in_row = max(max_h_in_row, w_height)

                except Exception as e:
                    report_unexpected_error(self.mw, "Error packing image window", e, self._err_state)
        finally:
            if hasattr(self.mw, "undo_stack"):
                try:
                    self.mw.undo_stack.endMacro()
                except Exception:
                    pass

    def pack_all_center(self, screen_index: int, space: int = 0) -> None:
        """全 ImageWindow を指定ディスプレイの中央へ詰めて配置する（サイズは変更しない）。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
            space (int): セル間隔（px）。
        """
        from PySide6.QtWidgets import QApplication

        wins = self._get_all_images()
        if not wins:
            return

        screens = QApplication.screens()
        if not (0 <= screen_index < len(screens)):
            return

        target_screen = screens[screen_index]
        screen_geo = target_screen.geometry()

        # レイアウト計算（シミュレーション）
        screen_w = screen_geo.width()

        rows = []  # List[List[ImageWindow]]
        row_widths = []
        row_heights = []

        current_row = []
        current_w_sum = 0
        current_h_max = 0

        valid_wins = [w for w in wins if w is not None]

        for w in valid_wins:
            try:
                ww = w.width()
                wh = w.height()

                added_space = space if current_row else 0

                if current_w_sum + added_space + ww > screen_w and current_row:
                    rows.append(current_row)
                    row_widths.append(current_w_sum)
                    row_heights.append(current_h_max)

                    current_row = [w]
                    current_w_sum = ww
                    current_h_max = wh
                else:
                    current_w_sum += added_space + ww
                    current_h_max = max(current_h_max, wh)
                    current_row.append(w)
            except Exception:
                continue

        if current_row:
            rows.append(current_row)
            row_widths.append(current_w_sum)
            row_heights.append(current_h_max)

        total_content_h = sum(row_heights) + (len(rows) - 1) * space
        start_y = screen_geo.y() + (screen_geo.height() - total_content_h) // 2

        if hasattr(self.mw, "undo_stack"):
            try:
                self.mw.undo_stack.beginMacro("Pack Images Center")
            except Exception:
                pass

        try:
            current_y = start_y
            for i, row in enumerate(rows):
                row_w = row_widths[i]
                row_h = row_heights[i]

                start_x = screen_geo.x() + (screen_w - row_w) // 2
                current_x = start_x

                for w in row:
                    try:
                        if hasattr(w, "set_undoable_property"):
                            w.set_undoable_property("position", {"x": current_x, "y": current_y}, "update_position")
                        else:
                            w.move(current_x, current_y)
                            if hasattr(w, "update_position"):
                                w.update_position()

                        current_x += w.width() + space
                    except Exception:
                        pass

                current_y += row_h + space

        except Exception as e:
            report_unexpected_error(self.mw, "Error packing image window (center)", e, self._err_state)
        finally:
            if hasattr(self.mw, "undo_stack"):
                try:
                    self.mw.undo_stack.endMacro()
                except Exception:
                    pass
