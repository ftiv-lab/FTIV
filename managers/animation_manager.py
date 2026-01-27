from typing import Any, List, Optional

from PySide6.QtCore import QPoint

from utils.translator import tr


class AnimationManager:
    """アニメーション関連のビジネスロジックを管理するクラス。

    MainWindow から分離されたアニメーション制御機能を提供します。
    """

    def __init__(self, main_window: Any):
        self.mw = main_window

    def _get_anim_tab(self) -> Optional[Any]:
        """AnimationTabへの参照を取得する。"""
        return getattr(self.mw, "animation_tab", None)

    def _get_ui_widget(self, name: str) -> Optional[Any]:
        """UIウィジェットを安全に取得する（AnimationTab優先）。"""
        tab = self._get_anim_tab()
        if tab and hasattr(tab, name):
            return getattr(tab, name)
        if hasattr(self.mw, name):
            return getattr(self.mw, name)
        return None

    def get_target_windows(self) -> List[Any]:
        """
        Animationタブの「適用先(Target)」に応じて対象ウィンドウ一覧を返す。
        """
        combo = self._get_ui_widget("anim_target_combo")
        idx = combo.currentIndex() if combo else 0

        # 0: Selected
        if idx == 0:
            return [self.mw.last_selected_window] if self.mw.last_selected_window else []

        targets: List[Any] = []

        # 1: All Text
        if idx == 1:
            targets.extend(list(self.mw.text_windows))
            # ConnectorLabel を追加
            for conn in list(self.mw.connectors):
                lw = getattr(conn, "label_window", None)
                if lw is not None:
                    targets.append(lw)

        # 2: All Image
        elif idx == 2:
            return list(self.mw.image_windows)

        # 3: All Windows
        else:
            targets.extend(list(self.mw.text_windows))
            targets.extend(list(self.mw.image_windows))
            # ConnectorLabel を追加
            for conn in list(self.mw.connectors):
                lw = getattr(conn, "label_window", None)
                if lw is not None:
                    targets.append(lw)

        # 重複除去（同一インスタンス）
        unique: List[Any] = []
        seen_ids = set()
        for w in targets:
            if w is None:
                continue
            wid = id(w)
            if wid in seen_ids:
                continue
            seen_ids.add(wid)
            unique.append(w)

        return unique

    def sync_from_selected(self, window: Optional[Any]) -> None:
        """Selected ウィンドウの状態を AnimationタブUIへ反映する。"""
        if window is None:
            return

        # UI取得
        anim_dx = self._get_ui_widget("anim_dx")
        anim_dy = self._get_ui_widget("anim_dy")
        anim_base_status = self._get_ui_widget("anim_base_status")

        anim_move_speed = self._get_ui_widget("anim_move_speed")
        anim_abs_move_speed = self._get_ui_widget("anim_abs_move_speed")
        anim_move_pause = self._get_ui_widget("anim_move_pause")
        anim_abs_move_pause = self._get_ui_widget("anim_abs_move_pause")

        anim_move_easing_combo = self._get_ui_widget("anim_move_easing_combo")
        anim_abs_easing_combo = self._get_ui_widget("anim_abs_easing_combo")

        anim_btn_pingpong = self._get_ui_widget("anim_btn_pingpong")
        anim_btn_oneway = self._get_ui_widget("anim_btn_oneway")
        anim_btn_abs_pingpong = self._get_ui_widget("anim_btn_abs_pingpong")
        anim_btn_abs_oneway = self._get_ui_widget("anim_btn_abs_oneway")

        anim_fade_speed = self._get_ui_widget("anim_fade_speed")
        anim_fade_pause = self._get_ui_widget("anim_fade_pause")
        anim_fade_easing_combo = self._get_ui_widget("anim_fade_easing_combo")

        anim_btn_fade_in_out = self._get_ui_widget("anim_btn_fade_in_out")
        anim_btn_fade_in_only = self._get_ui_widget("anim_btn_fade_in_only")
        anim_btn_fade_out_only = self._get_ui_widget("anim_btn_fade_out_only")

        # ---------------------------
        # 1. Relative Move UI sync
        # ---------------------------
        if anim_dx and hasattr(window, "get_move_offset"):
            try:
                off = window.get_move_offset()
                if anim_dx:
                    anim_dx.blockSignals(True)
                if anim_dy:
                    anim_dy.blockSignals(True)
                if anim_dx:
                    anim_dx.setValue(int(off.x()))
                if anim_dy:
                    anim_dy.setValue(int(off.y()))
            finally:
                if anim_dx:
                    anim_dx.blockSignals(False)
                if anim_dy:
                    anim_dy.blockSignals(False)

        if anim_base_status:
            base = getattr(window, "_rel_record_base_pos", None)
            if base is not None:
                anim_base_status.setText(tr("status_anim_base_recorded"))
            else:
                anim_base_status.setText(tr("status_anim_base_not_recorded"))

        # ---------------------------
        # 2. Move Params (Speed/Pause/Easing)
        # ---------------------------
        # Speed
        if hasattr(window, "move_speed"):
            val = int(window.move_speed)
            if anim_move_speed:
                anim_move_speed.setValue(val)
            if anim_abs_move_speed:
                anim_abs_move_speed.setValue(val)

        # Pause
        if hasattr(window, "move_pause_time"):
            val = int(window.move_pause_time)
            if anim_move_pause:
                anim_move_pause.setValue(val)
            if anim_abs_move_pause:
                anim_abs_move_pause.setValue(val)

        # Easing
        easing_name = "Linear"
        cfg = getattr(window, "config", None)
        if cfg is not None and hasattr(cfg, "move_easing"):
            try:
                easing_name = str(getattr(cfg, "move_easing") or "Linear")
            except Exception:
                easing_name = "Linear"

        # Relative Tab Easing
        if anim_move_easing_combo:
            idx = anim_move_easing_combo.findText(easing_name)
            if idx < 0:
                idx = anim_move_easing_combo.findText("Linear")
            try:
                anim_move_easing_combo.blockSignals(True)
                if idx >= 0:
                    anim_move_easing_combo.setCurrentIndex(idx)
            finally:
                anim_move_easing_combo.blockSignals(False)

        # Absolute Tab Easing
        if anim_abs_easing_combo:
            idx = anim_abs_easing_combo.findText(easing_name)
            if idx < 0:
                idx = anim_abs_easing_combo.findText("Linear")
            try:
                anim_abs_easing_combo.blockSignals(True)
                if idx >= 0:
                    anim_abs_easing_combo.setCurrentIndex(idx)
            finally:
                anim_abs_easing_combo.blockSignals(False)

        # ---------------------------
        # 3. Playback Buttons
        # ---------------------------
        try:
            is_rel = getattr(getattr(window, "config", None), "move_use_relative", False)

            # Relative Buttons
            if anim_btn_pingpong and anim_btn_oneway:
                anim_btn_pingpong.blockSignals(True)
                anim_btn_oneway.blockSignals(True)
                anim_btn_pingpong.setChecked(bool(is_rel and getattr(window, "move_loop_enabled", False)))
                anim_btn_oneway.setChecked(bool(is_rel and getattr(window, "move_position_only_enabled", False)))
                anim_btn_pingpong.blockSignals(False)
                anim_btn_oneway.blockSignals(False)

            # Absolute Buttons
            if anim_btn_abs_pingpong and anim_btn_abs_oneway:
                anim_btn_abs_pingpong.blockSignals(True)
                anim_btn_abs_oneway.blockSignals(True)
                anim_btn_abs_pingpong.setChecked(bool(not is_rel and getattr(window, "move_loop_enabled", False)))
                anim_btn_abs_oneway.setChecked(
                    bool(not is_rel and getattr(window, "move_position_only_enabled", False))
                )
                anim_btn_abs_pingpong.blockSignals(False)
                anim_btn_abs_oneway.blockSignals(False)

        except Exception:
            pass

        # ---------------------------
        # 4. Fade UI sync
        # ---------------------------
        if anim_fade_speed and hasattr(window, "fade_speed"):
            try:
                anim_fade_speed.setValue(int(window.fade_speed))
            except Exception:
                pass

        if anim_fade_pause and hasattr(window, "fade_pause_time"):
            try:
                anim_fade_pause.setValue(int(window.fade_pause_time))
            except Exception:
                pass

        # Fade Easing
        if anim_fade_easing_combo:
            f_easing = "Linear"
            if cfg is not None and hasattr(cfg, "fade_easing"):
                try:
                    f_easing = str(getattr(cfg, "fade_easing") or "Linear")
                except Exception:
                    f_easing = "Linear"

            idx = anim_fade_easing_combo.findText(f_easing)
            if idx < 0:
                idx = anim_fade_easing_combo.findText("Linear")

            try:
                anim_fade_easing_combo.blockSignals(True)
                if idx >= 0:
                    anim_fade_easing_combo.setCurrentIndex(idx)
            finally:
                anim_fade_easing_combo.blockSignals(False)

        # Fade Buttons
        if anim_btn_fade_in_out:
            try:
                anim_btn_fade_in_out.blockSignals(True)
                anim_btn_fade_in_out.setChecked(bool(getattr(window, "is_fading_enabled", False)))
            finally:
                anim_btn_fade_in_out.blockSignals(False)

        if anim_btn_fade_in_only:
            try:
                anim_btn_fade_in_only.blockSignals(True)
                anim_btn_fade_in_only.setChecked(bool(getattr(window, "fade_in_only_loop_enabled", False)))
            finally:
                anim_btn_fade_in_only.blockSignals(False)

        if anim_btn_fade_out_only:
            try:
                anim_btn_fade_out_only.blockSignals(True)
                anim_btn_fade_out_only.setChecked(bool(getattr(window, "fade_out_only_loop_enabled", False)))
            finally:
                anim_btn_fade_out_only.blockSignals(False)

    def apply_offset(self) -> None:
        windows = self.get_target_windows()
        anim_dx = self._get_ui_widget("anim_dx")
        anim_dy = self._get_ui_widget("anim_dy")

        dx = int(anim_dx.value()) if anim_dx else 0
        dy = int(anim_dy.value()) if anim_dy else 0

        for w in windows:
            if w is None:
                continue
            if hasattr(w, "config"):
                w.config.move_use_relative = True
            if hasattr(w, "set_move_offset"):
                w.set_move_offset(QPoint(dx, dy))

    def clear_offset(self) -> None:
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue
            if hasattr(w, "clear_relative_move_offset"):
                w.clear_relative_move_offset()

    def record_base(self) -> None:
        w = self.mw.last_selected_window
        if w and hasattr(w, "record_relative_move_base"):
            w.record_relative_move_base()
            self.sync_from_selected(w)

    def record_end(self) -> None:
        w = self.mw.last_selected_window
        if w and hasattr(w, "record_relative_move_end_as_offset"):
            w.record_relative_move_end_as_offset()
            self.sync_from_selected(w)

    def apply_abs_params(self) -> None:
        """絶対移動タブのパラメータ（速度/待機/イージング）を適用する。"""
        windows = self.get_target_windows()

        anim_abs_move_speed = self._get_ui_widget("anim_abs_move_speed")
        anim_abs_move_pause = self._get_ui_widget("anim_abs_move_pause")
        anim_abs_easing_combo = self._get_ui_widget("anim_abs_easing_combo")

        try:
            speed = int(anim_abs_move_speed.value()) if anim_abs_move_speed else 1000
            pause = int(anim_abs_move_pause.value()) if anim_abs_move_pause else 0
            easing_name = str(anim_abs_easing_combo.currentText() or "Linear") if anim_abs_easing_combo else "Linear"
        except Exception:
            return

        for w in windows:
            if w is None:
                continue
            if hasattr(w, "move_speed"):
                w.move_speed = speed
            if hasattr(w, "move_pause_time"):
                w.move_pause_time = pause
            cfg = getattr(w, "config", None)
            if cfg and hasattr(cfg, "move_easing"):
                cfg.move_easing = easing_name

            # runtimeへ反映
            if hasattr(w, "_apply_easing_from_config"):
                try:
                    w._apply_easing_from_config()
                except Exception:
                    pass

            # パラメータ変更時にアニメーション中なら再起動して反映
            if getattr(w, "move_loop_enabled", False):
                if hasattr(w, "start_move_animation"):
                    w.start_move_animation()
            elif getattr(w, "move_position_only_enabled", False):
                if hasattr(w, "start_move_position_only_animation"):
                    w.start_move_position_only_animation()

    def clear_abs_settings(self) -> None:
        """絶対移動の設定（始点・終点）をクリアする。"""
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue
            if hasattr(w, "clear_absolute_move_settings"):
                w.clear_absolute_move_settings()

    def apply_move_params(self) -> None:
        """相対移動タブのパラメータ（速度/待機/イージング）を適用する。"""
        windows = self.get_target_windows()

        anim_move_speed = self._get_ui_widget("anim_move_speed")
        anim_move_pause = self._get_ui_widget("anim_move_pause")
        anim_move_easing_combo = self._get_ui_widget("anim_move_easing_combo")

        try:
            speed = int(anim_move_speed.value()) if anim_move_speed else 1000
            pause = int(anim_move_pause.value()) if anim_move_pause else 0
            easing_name = str(anim_move_easing_combo.currentText() or "Linear") if anim_move_easing_combo else "Linear"
        except Exception:
            return

        for w in windows:
            if w is None:
                continue
            if hasattr(w, "move_speed"):
                w.move_speed = speed
            if hasattr(w, "move_pause_time"):
                w.move_pause_time = pause
            cfg = getattr(w, "config", None)
            if cfg and hasattr(cfg, "move_easing"):
                cfg.move_easing = easing_name

            # runtimeへ反映
            if hasattr(w, "_apply_easing_from_config"):
                try:
                    w._apply_easing_from_config()
                except Exception:
                    pass

            # パラメータ変更時にアニメーション中なら再起動して反映
            if getattr(w, "move_loop_enabled", False):
                if hasattr(w, "start_move_animation"):
                    w.start_move_animation()
            elif getattr(w, "move_position_only_enabled", False):
                if hasattr(w, "start_move_position_only_animation"):
                    w.start_move_position_only_animation()

    def toggle_pingpong(self, checked: bool = False, mode: Optional[str] = None) -> None:
        """PingPong(往復)移動の切り替え。"""
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue

            # モード設定 (Relative or Absolute)
            if mode == "relative":
                if hasattr(w, "config"):
                    w.config.move_use_relative = True
            elif mode == "absolute":
                if hasattr(w, "config"):
                    w.config.move_use_relative = False

            # OneWayをOFFにする (排他制御)
            if hasattr(w, "stop_animation"):
                # 既に動いているかもしれないので止める
                if getattr(w, "move_position_only_enabled", False):
                    w.stop_animation("move_position_only")

            # PingPongを設定
            # プロパティ設定だけでなく、動作の開始/停止を行う必要がある
            current = getattr(w, "move_loop_enabled", False)
            if current != checked:
                if hasattr(w, "toggle_move_position_loop"):
                    # toggle_move_position_loop は引数なしで状態を反転させる
                    w.toggle_move_position_loop()
                else:
                    # フォールバック
                    w.move_loop_enabled = checked
                    if checked and hasattr(w, "start_move_animation"):
                        w.start_move_animation()
                    elif not checked and hasattr(w, "stop_animation"):
                        w.stop_animation("move_loop")

        # UI同期 (Selectedがいる場合のみ)
        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def toggle_oneway(self, checked: bool = False, mode: Optional[str] = None) -> None:
        """OneWay(片道)移動の切り替え。"""
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue

            if mode == "relative":
                if hasattr(w, "config"):
                    w.config.move_use_relative = True
            elif mode == "absolute":
                if hasattr(w, "config"):
                    w.config.move_use_relative = False

            # PingPongをOFFにする
            if hasattr(w, "stop_animation"):
                if getattr(w, "move_loop_enabled", False):
                    w.stop_animation("move_loop")

            # OneWayを設定
            current = getattr(w, "move_position_only_enabled", False)
            if current != checked:
                if hasattr(w, "toggle_move_position_only"):
                    w.toggle_move_position_only()
                else:
                    w.move_position_only_enabled = checked
                    if checked and hasattr(w, "start_move_position_only_animation"):
                        w.start_move_position_only_animation()
                    elif not checked and hasattr(w, "stop_animation"):
                        w.stop_animation("move_position_only")

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def stop_move(self) -> None:
        """移動アニメーション停止。"""
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue
            if hasattr(w, "stop_animation"):
                w.stop_animation("move_loop")
                w.stop_animation("move_position_only")

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def apply_fade_params(self) -> None:
        """フェード用パラメータ適用。"""
        windows = self.get_target_windows()

        anim_fade_speed = self._get_ui_widget("anim_fade_speed")
        anim_fade_pause = self._get_ui_widget("anim_fade_pause")
        anim_fade_easing_combo = self._get_ui_widget("anim_fade_easing_combo")

        try:
            speed = int(anim_fade_speed.value()) if anim_fade_speed else 1000
            pause = int(anim_fade_pause.value()) if anim_fade_pause else 0
            easing_name = str(anim_fade_easing_combo.currentText() or "Linear") if anim_fade_easing_combo else "Linear"
        except Exception:
            return

        for w in windows:
            if w is None:
                continue
            if hasattr(w, "fade_speed"):
                w.fade_speed = speed
            if hasattr(w, "fade_pause_time"):
                w.fade_pause_time = pause
            cfg = getattr(w, "config", None)
            if cfg and hasattr(cfg, "fade_easing"):
                cfg.fade_easing = easing_name

            # runtimeへ反映
            if hasattr(w, "_apply_easing_from_config"):
                try:
                    w._apply_easing_from_config()
                except Exception:
                    pass

            # もしフェードが既に動いていたら、反映後に再スタートして見た目を合わせる
            if getattr(w, "is_fading_enabled", False):
                if hasattr(w, "start_fade_in"):
                    w.start_fade_in()
            elif getattr(w, "fade_in_only_loop_enabled", False):
                if hasattr(w, "start_fade_in_only"):
                    w.start_fade_in_only()
            elif getattr(w, "fade_out_only_loop_enabled", False):
                if hasattr(w, "start_fade_out_only"):
                    w.start_fade_out_only()

    def _stop_fade_internal(self, w: Any) -> None:
        """フェード停止（内部用）。"""
        if hasattr(w, "stop_animation"):
            w.stop_animation("is_fading")
            w.stop_animation("fade_in_only_loop")
            w.stop_animation("fade_out_only_loop")
            return

        # フォールバック
        if hasattr(w, "set_fading_enabled"):
            w.set_fading_enabled(False)
        if hasattr(w, "set_fade_in_only_loop_enabled"):
            w.set_fade_in_only_loop_enabled(False)
        if hasattr(w, "set_fade_out_only_loop_enabled"):
            w.set_fade_out_only_loop_enabled(False)

    def toggle_fade_in_out(self, checked: bool = False) -> None:
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue

            # UI側で排他制御済みだが念のため他を止める
            if checked:
                self._stop_fade_only_others(w, exclude="is_fading")

            # 現在の状態を確認して適用
            if hasattr(w, "toggle_fade"):
                # toggle_fade(enabled: bool)
                w.toggle_fade(checked)
            else:
                if hasattr(w, "set_fading_enabled"):
                    w.set_fading_enabled(checked)
                if checked and hasattr(w, "start_fade_in"):
                    w.start_fade_in()

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def toggle_fade_in_only(self, checked: bool = False) -> None:
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue

            if checked:
                self._stop_fade_only_others(w, exclude="fade_in_only_loop")

            if hasattr(w, "toggle_fade_in_only_loop"):
                w.toggle_fade_in_only_loop(checked)
            else:
                if hasattr(w, "set_fade_in_only_loop_enabled"):
                    w.set_fade_in_only_loop_enabled(checked)
                if checked and hasattr(w, "start_fade_in_only"):
                    w.start_fade_in_only()

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def toggle_fade_out_only(self, checked: bool = False) -> None:
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue

            if checked:
                self._stop_fade_only_others(w, exclude="fade_out_only_loop")

            if hasattr(w, "toggle_fade_out_only_loop"):
                w.toggle_fade_out_only_loop(checked)
            else:
                if hasattr(w, "set_fade_out_only_loop_enabled"):
                    w.set_fade_out_only_loop_enabled(checked)
                if checked and hasattr(w, "start_fade_out_only"):
                    w.start_fade_out_only()

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def _stop_fade_only_others(self, w: Any, exclude: str):
        """指定されたモード以外を停止するヘルパー。"""
        if hasattr(w, "stop_animation"):
            if exclude != "is_fading":
                w.stop_animation("is_fading")
            if exclude != "fade_in_only_loop":
                w.stop_animation("fade_in_only_loop")
            if exclude != "fade_out_only_loop":
                w.stop_animation("fade_out_only_loop")

    def stop_fade(self) -> None:
        windows = self.get_target_windows()
        for w in windows:
            if w is None:
                continue
            self._stop_fade_internal(w)

        if self.mw.last_selected_window in windows:
            self.sync_from_selected(self.mw.last_selected_window)

    def stop_all_animations(self) -> None:
        """全アニメーション（移動・フェード）を停止。"""
        # ターゲット設定に関わらず、緊急停止として全ウィンドウを停止させる
        if hasattr(self.mw, "window_manager"):
            self.mw.window_manager.stop_all_text_animations()
            self.mw.window_manager.stop_all_image_animations()

        # フェードなどは window_manager が管理していない場合があるので念のため直接停止
        all_windows = list(self.mw.text_windows) + list(self.mw.image_windows)
        for w in all_windows:
            self._stop_fade_internal(w)
            if hasattr(w, "stop_animation"):
                w.stop_animation("move_loop")
                w.stop_animation("move_position_only")
