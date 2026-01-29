# windows/base_window.py

import logging
import traceback
import uuid
from typing import Any, Dict, List, Optional, Type

import shiboken6
from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QAction, QColor, QPainter, QPen
from PySide6.QtWidgets import QInputDialog, QLabel, QMessageBox

from models.enums import AnchorPosition
from models.window_config import WindowConfigBase
from utils.commands import MoveWindowCommand, PropertyChangeCommand
from utils.translator import tr

logger = logging.getLogger(__name__)


class BaseOverlayWindow(QLabel):
    """
    FTIVにおけるすべてのオーバーレイウィンドウの基底クラス。
    ドラッグ移動、アニメーション、親子関係、Undo/Redo対応のプロパティ管理を提供します。
    """

    # シグナル定義
    sig_window_selected = Signal(object)
    sig_window_moved = Signal(object)
    sig_window_closed = Signal(object)
    sig_request_property_panel = Signal(object)
    sig_properties_changed = Signal(object)

    def __init__(self, main_window: Any, config_class: Optional[Type[WindowConfigBase]] = None):
        """
        BaseOverlayWindowを初期化します。
        Args:
            main_window (Any): メインウィンドウのインスタンス（UndoStack保持用）。
            config_class (Optional[Type[WindowConfigBase]]): 使用する設定クラス。
        """
        super().__init__()
        self.main_window = main_window

        # Undo/Redoアクションの共有
        if hasattr(self.main_window, "undo_action"):
            self.addAction(self.main_window.undo_action)
        if hasattr(self.main_window, "redo_action"):
            self.addAction(self.main_window.redo_action)

        # 設定オブジェクトの初期化
        if not hasattr(self, "config"):
            ConfigType = config_class if config_class else WindowConfigBase
            self.config = ConfigType()

        # UUIDの保証
        if not self.config.uuid:
            self.config.uuid = str(uuid.uuid4())

        # 管理用変数
        self.child_windows: List["BaseOverlayWindow"] = []
        self.connected_lines: List[Any] = []
        self.is_selected: bool = False
        self.is_dragging: bool = False
        self.last_mouse_pos: Optional[QPoint] = None
        self._drag_start_pos_global: Optional[QPoint] = None

        # ウィンドウ基本設定
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # アニメーション管理
        self.fade_animation: Optional[QPropertyAnimation] = None
        self.fade_easing_curve = QEasingCurve.Type.Linear
        self.move_animation: Optional[QPropertyAnimation] = None
        self.easing_curve = QEasingCurve.Type.Linear

        # 追加: 保存済みの easing を runtime に反映（互換のため getattr で安全に）
        self._apply_easing_from_config()

    # --- プロパティ (Pydantic Configラッパー) ---

    @property
    def uuid(self) -> str:
        return self.config.uuid

    @uuid.setter
    def uuid(self, value: str):
        self.config.uuid = value

    @property
    def parent_window_uuid(self) -> Optional[str]:
        return self.config.parent_uuid

    @parent_window_uuid.setter
    def parent_window_uuid(self, value: Optional[str]):
        self.config.parent_uuid = value

    @property
    def anchor_position(self) -> AnchorPosition:
        return self.config.anchor_position

    @anchor_position.setter
    def anchor_position(self, value: AnchorPosition):
        self.config.anchor_position = value
        for line in self.connected_lines:
            line.update_position()

    @property
    def is_frontmost(self) -> bool:
        return self.config.is_frontmost

    @is_frontmost.setter
    def is_frontmost(self, value: bool):
        self.config.is_frontmost = value
        flags = self.windowFlags()
        if value:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    @property
    def is_hidden(self) -> bool:
        return self.config.is_hidden

    @is_hidden.setter
    def is_hidden(self, value: bool):
        self.config.is_hidden = value

    @property
    def is_click_through(self) -> bool:
        return self.config.is_click_through

    @is_click_through.setter
    def is_click_through(self, value: bool):
        self.config.is_click_through = value
        self.set_click_through(value)

    @property
    def is_locked(self) -> bool:
        """移動/変形ロック状態。"""
        try:
            return bool(getattr(self.config, "is_locked", False))
        except Exception:
            return False

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        try:
            self.config.is_locked = bool(value)
        except Exception:
            pass

    @property
    def move_loop_enabled(self) -> bool:
        return self.config.move_loop_enabled

    @move_loop_enabled.setter
    def move_loop_enabled(self, value: bool):
        self.config.move_loop_enabled = value

    @property
    def move_position_only_enabled(self) -> bool:
        return self.config.move_position_only_enabled

    @move_position_only_enabled.setter
    def move_position_only_enabled(self, value: bool):
        self.config.move_position_only_enabled = value

    @property
    def move_speed(self) -> int:
        return self.config.move_speed

    @move_speed.setter
    def move_speed(self, value: int):
        self.config.move_speed = value

    @property
    def move_pause_time(self) -> int:
        return self.config.move_pause_time

    @move_pause_time.setter
    def move_pause_time(self, value: int):
        self.config.move_pause_time = value

    @property
    def start_position(self) -> Optional[QPoint]:
        if self.config.start_position:
            return QPoint(self.config.start_position["x"], self.config.start_position["y"])
        return None

    @start_position.setter
    def start_position(self, value: Optional[QPoint]):
        self.config.start_position = {"x": value.x(), "y": value.y()} if value else None

    @property
    def end_position(self) -> Optional[QPoint]:
        if self.config.end_position:
            return QPoint(self.config.end_position["x"], self.config.end_position["y"])
        return None

    @end_position.setter
    def end_position(self, value: Optional[QPoint]):
        self.config.end_position = {"x": value.x(), "y": value.y()} if value else None

    @property
    def is_fading_enabled(self) -> bool:
        return self.config.is_fading_enabled

    @is_fading_enabled.setter
    def is_fading_enabled(self, value: bool):
        self.config.is_fading_enabled = value

    @property
    def fade_in_only_loop_enabled(self) -> bool:
        return self.config.fade_in_only_loop_enabled

    @fade_in_only_loop_enabled.setter
    def fade_in_only_loop_enabled(self, value: bool):
        self.config.fade_in_only_loop_enabled = value

    @property
    def fade_out_only_loop_enabled(self) -> bool:
        return self.config.fade_out_only_loop_enabled

    @fade_out_only_loop_enabled.setter
    def fade_out_only_loop_enabled(self, value: bool):
        self.config.fade_out_only_loop_enabled = value

    @property
    def fade_speed(self) -> int:
        return self.config.fade_speed

    @fade_speed.setter
    def fade_speed(self, value: int):
        self.config.fade_speed = value

    @property
    def fade_pause_time(self) -> int:
        return self.config.fade_pause_time

    @fade_pause_time.setter
    def fade_pause_time(self, value: int):
        self.config.fade_pause_time = value

    @property
    def position(self) -> Dict[str, int]:
        """Undo対応用の位置プロパティ（辞書形式）。"""
        return {"x": self.x(), "y": self.y()}

    @position.setter
    def position(self, value: Dict[str, int]):
        """Undo対応用の位置プロパティセッター。"""
        try:
            x = int(value.get("x", self.x()))
            y = int(value.get("y", self.y()))
            self.move(x, y)
            if hasattr(self, "config") and hasattr(self.config, "position"):
                self.config.position = {"x": x, "y": y}
        except Exception as e:
            logger.warning(f"Failed to set position: {e}")

    def update_position(self):
        """位置変更後の更新処理（シグナル発行）。Config同期はSetterで行われる想定。"""
        # 必要なら再描画やシグナル
        self.sig_window_moved.emit(self)
        self.sig_properties_changed.emit(self)

    # --- 描画・選択管理 ---

    def set_selected(self, selected: bool):
        """選択状態を更新し再描画します。"""
        self.is_selected = selected
        self.update()

    def draw_selection_frame(self, painter: QPainter) -> None:
        """
        選択中のハイライト枠を描画します。

        Args:
            painter (QPainter): 描画に使用するペインター。
        """
        if not self.is_selected:
            return

        # MainWindow 側の設定を参照（無ければデフォルト）
        enabled: bool = True
        color_str: str = "#C800FFFF"
        width: int = 4

        try:
            mw: Any = getattr(self, "main_window", None)
            s: Any = getattr(mw, "overlay_settings", None)
            if s is not None:
                enabled = bool(getattr(s, "selection_frame_enabled", True))
                color_str = str(getattr(s, "selection_frame_color", color_str))
                width = int(getattr(s, "selection_frame_width", width))
        except Exception:
            pass

        if not enabled:
            return

        try:
            painter.save()
            pen = QPen(QColor(color_str))
            pen.setWidth(max(1, int(width)))
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(QColor(0, 0, 0, 0))

            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.drawRoundedRect(rect, 5, 5)
            painter.restore()
        except Exception:
            # 描画で落とさない
            try:
                painter.restore()
            except Exception:
                pass

    # --- 親子・コネクタ管理 ---

    def add_child_window(self, window: "BaseOverlayWindow"):
        """子ウィンドウを追加し親子関係を設定します。"""
        if window not in self.child_windows and window is not self:
            self.child_windows.append(window)
            window.parent_window_uuid = self.uuid

    def remove_child_window(self, window: "BaseOverlayWindow"):
        """子ウィンドウをリストから削除します。"""
        if window in self.child_windows:
            self.child_windows.remove(window)
            window.parent_window_uuid = None

    def clear_all_relations(self) -> None:
        """すべての親子関係および接続線を切断します（安全版）。

        方針:
            - 親子関係は window.parent_window_uuid を外して child_windows をクリア
            - コネクタは WindowManager.delete_connector() に委譲して削除経路を一本化
              （WindowManagerが無い/取得できない場合のみ close() フォールバック）
        """
        # 1) 親子関係を解除
        try:
            for child in list(self.child_windows):
                try:
                    child.parent_window_uuid = None
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.child_windows.clear()
        except Exception:
            pass

        # 2) コネクタを解除（WindowManager 経由で削除）
        lines = []
        try:
            lines = list(self.connected_lines)
        except Exception:
            lines = []

        wm = None
        try:
            mw = getattr(self, "main_window", None)
            if mw is not None and hasattr(mw, "window_manager"):
                wm = mw.window_manager
        except Exception:
            wm = None

        for line in lines:
            if line is None:
                continue

            # WindowManager があれば正規ルートで削除
            if wm is not None and hasattr(wm, "delete_connector"):
                try:
                    wm.delete_connector(line)
                    continue
                except Exception:
                    pass

            # フォールバック：closeのみ
            try:
                if hasattr(line, "delete_line"):
                    line.delete_line()
                else:
                    line.close()
            except Exception:
                pass

        try:
            self.connected_lines.clear()
        except Exception:
            pass

    # --- ウィンドウ制御アクション ---

    def toggle_frontmost(self):
        """最前面表示を切り替えます（Undo対応）。"""
        self.set_undoable_property("is_frontmost", not self.is_frontmost)

    def hide_action(self):
        """ウィンドウを非表示にします。"""
        self.is_hidden = True
        self.hide()
        for line in self.connected_lines:
            line.update_position()

    def show_action(self):
        """ウィンドウを表示します。"""
        self.is_hidden = False
        self.show()
        for line in self.connected_lines:
            line.update_position()

    def set_click_through(self, enabled: bool):
        """マウスクリックを透過させるかどうかを設定します。"""
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.show()

    def closeEvent(self, event) -> None:
        """クローズ時のリソース解放処理。

        方針（安定化）:
            - WindowManager が sig_window_closed を受けて管理リストから除去する設計のため、
              ここで deleteLater() は呼ばない（削除経路の二重化を避ける）。
            - 親子関係/接続参照/アニメーションはここで停止・解除する。
        """
        try:
            # 1) WindowManager に「閉じた」ことを通知（remove_window の起点）
            try:
                self.sig_window_closed.emit(self)
            except Exception as e:
                logger.warning(f"Failed to emit sig_window_closed: {e}")

            # 2) アニメ停止
            try:
                self.stop_all_animations()
            except Exception as e:
                logger.warning(f"Failed to stop animations: {e}")

            # 3) 親子/接続の参照を解除（循環参照を切る）
            try:
                self.clear_all_relations()
            except Exception as e:
                logger.warning(f"Failed to clear relations: {e}")

            # deleteLater() は呼ばない（ここが今回の変更点）

        finally:
            try:
                event.accept()
            except Exception as e:
                logger.warning(f"Failed to accept close event: {e}")

    def stop_all_animations(self):
        """すべての実行中のアニメーションを停止します。"""
        self.stop_animation("move_loop")
        self.stop_animation("move_position_only")
        self.stop_animation("is_fading")
        self.stop_animation("fade_out_only_loop")
        self.stop_animation("fade_in_only_loop")

    # --- アニメーション設定 (UI操作) ---

    def set_start_position(self):
        """旧: 開始位置を設定（絶対）。現: 相対移動の基準位置を記録に置き換え。"""
        self.record_relative_move_base()

    def set_end_position(self):
        """旧: 終了位置を設定（絶対）。現: 相対移動の終点記録（オフセット確定）に置き換え。"""
        self.record_relative_move_end_as_offset()

    def set_move_speed(self):
        """移動速度をダイアログから設定します。"""
        speed, ok = QInputDialog.getInt(
            self, tr("title_set_move_speed"), tr("label_move_speed"), self.move_speed, 10, 100000
        )
        if ok:
            self.move_speed = speed
            if self.move_loop_enabled and self.move_animation:
                self.move_animation.stop()
                self.start_move_animation()
            self.update_move_position_only_action()

    def set_move_pause_time(self):
        """移動の待機時間を設定します。"""
        pause_time, ok = QInputDialog.getInt(
            self, tr("title_set_move_pause"), tr("label_pause_time"), self.move_pause_time, 0, 10000
        )
        if ok:
            self.move_pause_time = pause_time

    def _get_easing_curve_names(self) -> Dict[str, QEasingCurve.Type]:
        """利用可能なイージングカーブの一覧を返します。"""
        curves = [
            "Linear",
            "InQuad",
            "OutQuad",
            "InOutQuad",
            "InCubic",
            "OutCubic",
            "InOutCubic",
            "InQuart",
            "OutQuart",
            "InOutQuart",
            "InQuint",
            "OutQuint",
            "InOutQuint",
            "InSine",
            "OutSine",
            "InOutSine",
            "InExpo",
            "OutExpo",
            "InOutExpo",
            "InCirc",
            "OutCirc",
            "InOutCirc",
            "InElastic",
            "OutElastic",
            "InOutElastic",
            "InBack",
            "OutBack",
            "InOutBack",
            "InBounce",
            "OutBounce",
            "InOutBounce",
        ]
        return {name: getattr(QEasingCurve.Type, name) for name in curves}

    def set_easing_curve(self):
        """移動アニメーションのイージングを設定します。"""
        curve_map = self._get_easing_curve_names()
        names = list(curve_map.keys())
        current_name = next((n for n, c in curve_map.items() if c == self.easing_curve), "Linear")

        curve_name, ok = QInputDialog.getItem(
            self, tr("title_select_easing"), tr("label_easing"), names, names.index(current_name), False
        )
        if ok:
            self.easing_curve = curve_map[curve_name]

            # 追加: Configにも保存して、シーン保存/復元で維持できるようにする
            if hasattr(self.config, "move_easing"):
                self.config.move_easing = str(curve_name)

            if self.move_loop_enabled and self.move_animation:
                self.move_animation.stop()
                self.start_move_animation()

    def change_fade_speed(self):
        """フェード速度を設定します。"""
        speed, ok = QInputDialog.getInt(
            self, tr("title_set_fade_speed"), tr("label_fade_speed"), self.fade_speed, 100, 100000
        )
        if ok:
            self.fade_speed = speed

    def set_fade_pause_time(self):
        """フェードの待機時間を設定します。"""
        pause_time, ok = QInputDialog.getInt(
            self, tr("title_set_fade_pause"), tr("label_pause_time"), self.fade_pause_time, 0, 10000
        )
        if ok:
            self.fade_pause_time = pause_time

    def set_fade_easing_curve(self):
        """フェードアニメーションのイージングを設定します。"""
        curve_map = self._get_easing_curve_names()
        names = list(curve_map.keys())
        current_name = next((n for n, c in curve_map.items() if c == self.fade_easing_curve), "Linear")

        curve_name, ok = QInputDialog.getItem(
            self, tr("title_select_easing_fade"), tr("label_easing"), names, names.index(current_name), False
        )
        if ok:
            self.fade_easing_curve = curve_map[curve_name]

            # 追加: Configにも保存して、シーン保存/復元で維持できるようにする
            if hasattr(self.config, "fade_easing"):
                self.config.fade_easing = str(curve_name)

            if self.fade_animation:
                self.fade_animation.setEasingCurve(self.fade_easing_curve)

    # --- アニメーション実行 ---

    def toggle_move_position_loop(self) -> None:
        """移動（往復）のトグル。モード（相対/絶対）は変更せず、現在の設定で動く。"""
        # ★修正: ここで self.config.move_use_relative = True を強制しない

        self.move_loop_enabled = not self.move_loop_enabled
        if self.move_loop_enabled:
            # 排他：片道ループをOFF
            if self.move_position_only_enabled:
                self.move_position_only_enabled = False
                self.stop_animation("move_position_only")
            self.start_move_animation()
        else:
            self.stop_animation("move_loop")

        self.update_move_position_loop_action()

    def toggle_move_position_only(self) -> None:
        """移動（片道）のトグル。モード（相対/絶対）は変更せず、現在の設定で動く。"""
        # ★修正: ここで self.config.move_use_relative = True を強制しない

        self.move_position_only_enabled = not self.move_position_only_enabled
        if self.move_position_only_enabled:
            # 排他：往復ループをOFF
            if self.move_loop_enabled:
                self.move_loop_enabled = False
                self.stop_animation("move_loop")
            self.start_move_position_only_animation()
        else:
            self.stop_animation("move_position_only")

        self.update_move_position_only_action()

    def start_move_animation(self) -> None:
        """
        移動アニメ（往復ループ）。
        config.move_use_relative の値によって 相対/絶対 を切り替える。
        """
        # 相対モードの場合
        if getattr(self.config, "move_use_relative", False):
            self._clear_legacy_absolute_move_fields()
            # 既存の絶対アニメが動いていれば止める
            if self.move_animation:
                try:
                    self.move_animation.stop()
                except Exception:
                    pass
            self._start_relative_move_pingpong()
            return

        # 絶対モードの場合
        self.move_loop_enabled = True

        # 相対アニメが動いていれば止める
        self._stop_relative_animation()

        if not self.start_position or not self.end_position:
            self._emit_status_warning("msg_abs_pos_not_set")
            self.move_loop_enabled = False
            self.update_move_actions()
            return

        # QPropertyAnimation を使用（QPointプロパティ pos を直接動かす）
        self.move_animation = QPropertyAnimation(self, b"pos")
        self.move_animation.setDuration(self.move_speed)
        self.move_animation.setStartValue(self.start_position)
        self.move_animation.setEndValue(self.end_position)
        self.move_animation.setEasingCurve(self.easing_curve)

        # 往復用コールバック
        self.move_animation.finished.connect(self.reverse_move_animation_with_pause)
        self.move_animation.start()

    def reverse_move_animation(self):
        if not self.move_animation:
            return
        if self.move_animation.startValue() == self.start_position:
            self.move_animation.setStartValue(self.end_position)
            self.move_animation.setEndValue(self.start_position)
        else:
            self.move_animation.setStartValue(self.start_position)
            self.move_animation.setEndValue(self.end_position)
        self.move_animation.start()

    def reverse_move_animation_with_pause(self):
        if self.move_loop_enabled:
            QTimer.singleShot(self.move_pause_time, self.reverse_move_animation)

    def start_move_position_only_animation(self) -> None:
        """
        移動アニメ（片道ループ：瞬間戻り）。
        config.move_use_relative の値によって 相対/絶対 を切り替える。
        """
        # 相対モード
        if getattr(self.config, "move_use_relative", False):
            self._clear_legacy_absolute_move_fields()
            if self.move_animation:
                try:
                    self.move_animation.stop()
                except Exception:
                    pass
            self._start_relative_move_oneway_jumpback()
            return

        # 絶対モード
        self.move_position_only_enabled = True
        self._stop_relative_animation()

        if not self.start_position or not self.end_position:
            self._emit_status_warning("msg_abs_pos_not_set")
            self.move_position_only_enabled = False
            self.update_move_actions()
            return

        self.move_animation = QPropertyAnimation(self, b"pos")
        self.move_animation.setDuration(self.move_speed)
        self.move_animation.setStartValue(self.start_position)
        self.move_animation.setEndValue(self.end_position)
        self.move_animation.setEasingCurve(self.easing_curve)

        # 片道用コールバック
        self.move_animation.finished.connect(self.start_move_position_only_with_pause)
        self.move_animation.start()

    def start_move_position_only_with_pause(self):
        if self.move_position_only_enabled:
            QTimer.singleShot(self.move_pause_time, self.start_move_position_only_animation)

    def stop_move_animation_loop(self):
        self.stop_animation("move_loop")

    def toggle_fade(self, enabled: bool):
        self.is_fading_enabled = enabled
        if enabled:
            self.start_fade_in()
        else:
            self.stop_animation("is_fading")

    def toggle_fade_in_only_loop(self, enabled: bool):
        self.fade_in_only_loop_enabled = enabled
        if enabled:
            self.start_fade_in_only()
        else:
            self.stop_animation("fade_in_only_loop")

    def toggle_fade_out_only_loop(self, enabled: bool):
        self.fade_out_only_loop_enabled = enabled
        if enabled:
            self.start_fade_out_only()
        else:
            self.stop_animation("fade_out_only_loop")

    def start_fade_in(self):
        if self.is_fading_enabled:
            self._run_fade_animation(0.0, 1.0, self.start_fade_out_with_pause)

    def start_fade_out(self):
        if self.is_fading_enabled:
            self._run_fade_animation(1.0, 0.0, self.start_fade_in_with_pause)

    def start_fade_in_only(self):
        if self.fade_in_only_loop_enabled:
            self._run_fade_animation(0.0, 1.0, self.start_fade_in_only_with_pause)

    def start_fade_out_only(self):
        if self.fade_out_only_loop_enabled:
            self._run_fade_animation(1.0, 0.0, self.start_fade_out_only_with_pause)

    def _run_fade_animation(self, start_val: float, end_val: float, on_finished: callable):
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(self.fade_speed)
        self.fade_animation.setStartValue(start_val)
        self.fade_animation.setEndValue(end_val)
        self.fade_animation.setEasingCurve(self.fade_easing_curve)
        self.fade_animation.finished.connect(on_finished)
        self.fade_animation.start()

    def start_fade_in_with_pause(self):
        if self.is_fading_enabled:
            QTimer.singleShot(self.fade_pause_time, self.start_fade_in)

    def start_fade_out_with_pause(self):
        if self.is_fading_enabled:
            QTimer.singleShot(self.fade_pause_time, self.start_fade_out)

    def start_fade_out_only_with_pause(self):
        if self.fade_out_only_loop_enabled:
            QTimer.singleShot(self.fade_pause_time, self.start_fade_out_only)

    def start_fade_in_only_with_pause(self):
        if self.fade_in_only_loop_enabled:
            QTimer.singleShot(self.fade_pause_time, self.start_fade_in_only)

    def stop_animation(self, animation_type: Optional[str] = None):
        """指定された種類のアニメーションを停止します。"""
        if animation_type == "move_loop":
            self.move_loop_enabled = False
            if self.move_animation:
                self.move_animation.stop()
            self._stop_relative_animation()
            self.update_move_position_loop_action()

        elif animation_type == "move_position_only":
            self.move_position_only_enabled = False
            if self.move_animation:
                self.move_animation.stop()
            self._stop_relative_animation()
            self.update_move_position_only_action()

        elif animation_type in ["is_fading", "fade_out_only_loop", "fade_in_only_loop"]:
            if animation_type == "is_fading":
                self.is_fading_enabled = False
            elif animation_type == "fade_out_only_loop":
                self.fade_out_only_loop_enabled = False
            elif animation_type == "fade_in_only_loop":
                self.fade_in_only_loop_enabled = False
            if self.fade_animation:
                self.fade_animation.stop()
            self.setWindowOpacity(1.0)
            self.update_fade_actions()

    # --- マウスイベント ---

    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.ControlModifier:
                # Ctrl+クリックによるアニメーション再開
                if self.move_position_only_enabled:
                    self.start_move_position_only_animation()
                elif self.move_loop_enabled:
                    self.start_move_animation()

                if self.is_fading_enabled:
                    self.start_fade_in()
                elif self.fade_out_only_loop_enabled:
                    self.start_fade_out_only()
                elif self.fade_in_only_loop_enabled:
                    self.start_fade_in_only()

            elif event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.ShiftModifier):
                # Shift+Click: Connect to last selected window (Daisy Chain)
                try:
                    mw = getattr(self, "main_window", None)
                    wm = getattr(mw, "window_manager", None) if mw else None
                    if wm:
                        # 直前に選択されていたウィンドウを取得
                        last_sel = getattr(wm, "last_selected_window", None)

                        # 自分自身以外、かつ直前選択がある場合に接続
                        if last_sel and last_sel != self and hasattr(wm, "add_connector"):
                            wm.add_connector(last_sel, self)

                        # 次の接続のために自分を選択状態にする
                        # (ここで is_dragging=True にしないことで、誤ドラッグを防ぐ)
                        self.sig_window_selected.emit(self)
                        event.accept()
                        return

                except Exception as e:
                    logger.warning(f"Failed to connect via Shift+Click: {e}")
                    pass  # 失敗しても通常のクリック処理へ流すか、ここで止めるか。安全のため止める。

                # 接続処理が走った（または失敗した）が、通常のドラッグには行かせない
                event.accept()
                return

            elif event.button() == Qt.MouseButton.LeftButton:
                # ★追加：ロック中はドラッグ移動を開始しない（選択はできる）
                if getattr(self, "is_locked", False):
                    self.sig_window_selected.emit(self)
                    event.accept()
                    return

                self.is_dragging = True
                self.last_mouse_pos = event.globalPosition().toPoint()
                self._drag_start_pos_global = self.pos()
                self.sig_window_selected.emit(self)

            elif event.button() == Qt.MiddleButton:
                self.stop_all_animations()

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Error in mousePressEvent: {e}")
            traceback.print_exc()

    def mouseDoubleClickEvent(self, event):
        """ダブルクリックイベント。"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                # 移動アニメ
                if getattr(self, "move_loop_enabled", False) or getattr(self, "move_position_only_enabled", False):
                    self.stop_animation("move_loop")
                    self.stop_animation("move_position_only")
                else:
                    self.start_move_animation()

                # フェード
                if (
                    getattr(self, "is_fading_enabled", False)
                    or getattr(self, "fade_in_only_loop_enabled", False)
                    or getattr(self, "fade_out_only_loop_enabled", False)
                ):
                    self.stop_animation("is_fading")
                    self.stop_animation("fade_in_only_loop")
                    self.stop_animation("fade_out_only_loop")
                else:
                    if hasattr(self, "start_fade_in"):
                        self.start_fade_in()

                event.accept()
        except Exception:
            traceback.print_exc()

    def mouseMoveEvent(self, event):
        try:
            if self.is_dragging and self.last_mouse_pos:
                current_pos = event.globalPosition().toPoint()
                delta = current_pos - self.last_mouse_pos

                self.move_tree_by_delta(delta)

                # 追加：相対移動アニメ中なら、軌道の基準も一緒に平行移動する
                if getattr(self, "_rel_move_anim", None) is not None:
                    self._shift_relative_move_base_by_delta(delta)

                self.last_mouse_pos = current_pos
                event.accept()
        except Exception:
            traceback.print_exc()

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = False
                if hasattr(self, "config"):
                    self.config.position = {"x": self.x(), "y": self.y()}

                # Undoコマンドの登録
                if self._drag_start_pos_global is not None and self.pos() != self._drag_start_pos_global:
                    if hasattr(self.main_window, "add_undo_command"):
                        cmd = MoveWindowCommand(self, self._drag_start_pos_global, self.pos())
                        self.main_window.add_undo_command(cmd)
                    self._drag_start_pos_global = None
        except Exception:
            traceback.print_exc()

    def move_tree_by_delta(self, delta: QPoint) -> None:
        """自分自身とすべての子ウィンドウを再帰的に移動させます。

        Args:
            delta (QPoint): 移動量。
        """
        self.move(self.pos() + delta)

        try:
            for line in list(self.connected_lines):
                try:
                    line.update_position()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.sig_window_moved.emit(self)
        except Exception:
            pass

        # 反復中に remove しない。最後に prune する。
        try:
            children_snapshot: list[Any] = list(self.child_windows[:])
        except Exception:
            children_snapshot = []

        any_invalid: bool = False

        for child in children_snapshot:
            try:
                if child and shiboken6.isValid(child) and child.isVisible():
                    child.move_tree_by_delta(delta)
                else:
                    any_invalid = True
            except (RuntimeError, AttributeError):
                any_invalid = True
            except Exception:
                # 想定外でも落とさない
                any_invalid = True

        # 無効な子を一括除去（安全）
        if any_invalid:
            try:
                self.child_windows = [c for c in list(self.child_windows) if c is not None and shiboken6.isValid(c)]
            except Exception:
                pass

    # --- UI状態更新 (Action同期) ---

    def update_fade_actions(self):
        actions = self.findChildren(QAction)
        for action in actions:
            if action.text() == tr("menu_toggle_fade_in_out"):
                action.setChecked(self.is_fading_enabled)
            elif action.text() == tr("menu_toggle_fade_out_loop"):
                action.setChecked(self.fade_out_only_loop_enabled)
            elif action.text() == tr("menu_toggle_fade_in_loop"):
                action.setChecked(self.fade_in_only_loop_enabled)

    def update_move_position_loop_action(self):
        for action in self.findChildren(QAction):
            if action.text() == tr("menu_toggle_move_loop"):
                action.setChecked(self.move_loop_enabled)

    def update_move_position_only_action(self):
        for action in self.findChildren(QAction):
            if action.text() == tr("menu_toggle_move_pos_only"):
                action.setChecked(self.move_position_only_enabled)

    def update_move_actions(self):
        self.update_move_position_loop_action()
        self.update_move_position_only_action()

    def set_undoable_property(self, property_name: str, new_value: Any, update_method_name: Optional[str] = None):
        """
        Undo可能な形式でプロパティを変更します。

        Args:
            property_name (str): 変更するプロパティ名。
            new_value (Any): 新しい値。
            update_method_name (Optional[str]): 変更後に呼び出すメソッド名。
        """
        if not shiboken6.isValid(self):
            return

        old_value = getattr(self, property_name)
        if old_value == new_value:
            return

        command = PropertyChangeCommand(
            target=self,
            property_name=property_name,
            old_value=old_value,
            new_value=new_value,
            update_method_name=update_method_name,
        )

        main_window = getattr(self, "main_window", None)
        if main_window and hasattr(main_window, "add_undo_command"):
            main_window.add_undo_command(command)
        else:
            # Fallback
            command.redo()

    def _ensure_relative_move_state(self) -> None:
        if not hasattr(self, "_rel_move_anim"):
            self._rel_move_anim = None
        if not hasattr(self, "_rel_base_pos"):
            self._rel_base_pos = None
        if not hasattr(self, "_rel_direction"):
            self._rel_direction = 1  # 1 or -1
        if not hasattr(self, "_rel_record_base_pos"):
            self._rel_record_base_pos = None

    def _emit_status_warning(self, message_key: str, fallback_text: str = "") -> None:
        """
        フッター等に警告を出す。MainWindow側に show_status_message があればそれを使う。
        """
        try:
            text = tr(message_key)
            if text == message_key and fallback_text:
                text = fallback_text

            mw = getattr(self, "main_window", None)
            if mw and hasattr(mw, "show_status_message"):
                mw.show_status_message(text)
                return

            # WindowManager のシグナル経由に寄せたい場合の保険
            if mw and hasattr(mw, "window_manager") and hasattr(mw.window_manager, "sig_status_message"):
                mw.window_manager.sig_status_message.emit(text)
                return

            # 最終フォールバック（何もしないでも良いが、開発中はprintが便利）

        except Exception:
            pass

    def get_move_offset(self) -> QPoint:
        """
        config.move_offset を QPoint として返す。
        """
        off = getattr(self.config, "move_offset", None) or {}
        x = int(off.get("x", 0))
        y = int(off.get("y", 0))
        return QPoint(x, y)

    def set_move_offset(self, offset: QPoint) -> None:
        """
        QPoint の offset を config.move_offset(dict) に保存する。
        """
        if not hasattr(self.config, "move_offset"):
            # 古いConfig互換用（通常はWindowConfigBaseに追加される想定）
            self.config.move_offset = {"x": 0, "y": 0}  # type: ignore[attr-defined]

        self.config.move_offset = {"x": int(offset.x()), "y": int(offset.y())}  # type: ignore[attr-defined]

    def _is_zero_offset(self, offset: QPoint) -> bool:
        return offset.x() == 0 and offset.y() == 0

    def open_relative_move_offset_dialog(self) -> None:
        """
        相対移動オフセット(dx,dy)を入力して設定する。
        move_use_relative は True にする。
        """
        try:
            dx, ok = QInputDialog.getInt(
                self, tr("menu_set_relative_move_offset"), "dx:", self.get_move_offset().x(), -99999, 99999
            )
            if not ok:
                return

            dy, ok = QInputDialog.getInt(
                self, tr("menu_set_relative_move_offset"), "dy:", self.get_move_offset().y(), -99999, 99999
            )
            if not ok:
                return

            self.config.move_use_relative = True  # type: ignore[attr-defined]
            self.set_move_offset(QPoint(dx, dy))
            self._emit_status_warning(
                "msg_relative_move_offset_set", fallback_text=f"Relative move offset set: dx={dx}, dy={dy}"
            )
        except Exception as e:
            self._emit_status_warning("msg_warning", fallback_text=str(e))

    def record_absolute_start_pos(self) -> None:
        """絶対移動の開始位置を記録する。"""
        self.config.move_use_relative = False  # 絶対モードへ切り替え
        self.start_position = self.pos()
        self._emit_status_warning("msg_abs_start_recorded")

    def record_absolute_end_pos(self) -> None:
        """絶対移動の終了位置を記録する。"""
        self.config.move_use_relative = False  # 絶対モードへ切り替え
        self.end_position = self.pos()
        self._emit_status_warning("msg_abs_end_recorded")

    def record_relative_move_base(self) -> None:
        """
        相対移動の基準位置を記録する（次に「現在位置を終点として記録」でoffset確定）。
        """
        self._ensure_relative_move_state()
        self._rel_record_base_pos = self.pos()  # type: ignore[attr-defined]
        self._emit_status_warning(
            "msg_relative_move_base_recorded",
            fallback_text="Base position recorded. Move the window, then record current position as end.",
        )

    def record_relative_move_end_as_offset(self) -> None:
        """
        現在位置を「終点」として、基準位置との差分を move_offset に保存する。
        move_use_relative は True にする。
        """
        self._ensure_relative_move_state()
        base = self._rel_record_base_pos  # type: ignore[attr-defined]
        if base is None:
            self._emit_status_warning(
                "msg_relative_move_base_not_set", fallback_text="Base position is not recorded yet."
            )
            return

        offset = self.pos() - base
        self.config.move_use_relative = True  # type: ignore[attr-defined]
        self.set_move_offset(offset)
        self._rel_record_base_pos = None  # type: ignore[attr-defined]

        self._emit_status_warning(
            "msg_relative_move_offset_set", fallback_text=f"Relative move offset set: dx={offset.x()}, dy={offset.y()}"
        )

    def clear_relative_move_offset(self) -> None:
        """
        相対移動オフセットを(0,0)に戻す。
        """
        self.config.move_use_relative = True  # type: ignore[attr-defined]
        self.set_move_offset(QPoint(0, 0))
        self._emit_status_warning("msg_relative_move_offset_cleared", fallback_text="Relative move offset cleared.")

    def _start_relative_variant_animation(
        self, start_pos: QPoint, end_pos: QPoint, duration_ms: int, finished_cb
    ) -> None:
        """
        QVariantAnimation で start_pos→end_pos の目標座標を生成し、
        valueChanged で delta を計算して move_tree_by_delta() する。
        """
        from PySide6.QtCore import QVariantAnimation  # ローカルimportで循環/負荷回避

        self._ensure_relative_move_state()

        # 既存の相対アニメがあれば止める
        if getattr(self, "_rel_move_anim", None) is not None:
            try:
                self._rel_move_anim.stop()
            except Exception:
                pass

        anim = QVariantAnimation(self)
        anim.setStartValue(QPoint(int(start_pos.x()), int(start_pos.y())))
        anim.setEndValue(QPoint(int(end_pos.x()), int(end_pos.y())))
        anim.setDuration(int(duration_ms))
        anim.setEasingCurve(self.easing_curve)

        self._rel_last_pos = QPoint(int(start_pos.x()), int(start_pos.y()))

        def _on_value_changed(val):
            if not isinstance(val, QPoint):
                return
            self._on_relative_anim_value_changed(val)

        anim.valueChanged.connect(_on_value_changed)
        anim.finished.connect(finished_cb)

        self._rel_move_anim = anim
        anim.start()

    def _on_relative_anim_value_changed(self, new_pos: QPoint) -> None:
        """
        相対アニメーションの毎フレーム更新。
        new_pos は「親がいるべき絶対座標」なので、delta を計算して tree を動かす。
        """
        self._ensure_relative_move_state()

        last = getattr(self, "_rel_last_pos", None)
        if last is None:
            self._rel_last_pos = QPoint(new_pos)
            return

        delta = new_pos - last
        if delta.x() == 0 and delta.y() == 0:
            return

        # ここが重要：親だけmove()するのではなく、treeごと動かす
        self.move_tree_by_delta(delta)

        self._rel_last_pos = QPoint(new_pos)

    def _start_relative_move_pingpong(self) -> None:
        offset = self.get_move_offset()
        if self._is_zero_offset(offset):
            self._emit_status_warning("msg_relative_move_offset_zero", fallback_text="Relative move offset is (0,0).")
            self.move_loop_enabled = False
            self.update_move_position_loop_action()
            return

        self._ensure_relative_move_state()
        self._rel_base_pos = self.pos()
        self._rel_direction = 1

        def _on_finished():
            if not self.move_loop_enabled:
                return

            def _restart():
                if not self.move_loop_enabled:
                    return
                self._rel_direction *= -1
                self._start_relative_progress_animation(_on_finished)

            QTimer.singleShot(self.move_pause_time, _restart)

        self._start_relative_progress_animation(_on_finished)

    def _start_relative_move_oneway_jumpback(self) -> None:
        offset = self.get_move_offset()
        if self._is_zero_offset(offset):
            self._emit_status_warning("msg_relative_move_offset_zero", fallback_text="Relative move offset is (0,0).")
            self.move_position_only_enabled = False
            self.update_move_position_only_action()
            return

        self._ensure_relative_move_state()
        self._rel_base_pos = self.pos()
        self._rel_direction = 1

        def _on_finished():
            if not self.move_position_only_enabled:
                return

            def _restart():
                if not self.move_position_only_enabled:
                    return

                # 現在位置を「基準(base)」へ瞬間移動（treeごと）
                base = self._rel_base_pos
                if base is not None:
                    delta = base - self.pos()
                    if delta.x() != 0 or delta.y() != 0:
                        self.move_tree_by_delta(delta)

                self._start_relative_progress_animation(_on_finished)

            QTimer.singleShot(self.move_pause_time, _restart)

        self._start_relative_progress_animation(_on_finished)

    def _relative_base_pos(self) -> QPoint:
        """
        相対移動の基準位置。
        要件どおり「再生開始時の現在位置」を基準とするため、単に self.pos() を返す。
        """
        return self.pos()

    def _stop_relative_animation(self) -> None:
        """
        相対移動アニメーションを停止する（内部用）。
        stop_animation() から呼ばれるため必須。
        """
        self._ensure_relative_move_state()

        anim = getattr(self, "_rel_move_anim", None)
        if anim is not None:
            try:
                anim.stop()
            except Exception:
                pass

        self._rel_move_anim = None
        self._rel_last_pos = None

    def _clear_legacy_absolute_move_fields(self) -> None:
        """
        旧: start_position / end_position を使わない方針のため、値を無効化する。
        ※ 保存処理が exclude_none=True でないと JSON からは消えず null には残る。
        """
        try:
            if hasattr(self.config, "start_position"):
                self.config.start_position = None
            if hasattr(self.config, "end_position"):
                self.config.end_position = None
        except Exception:
            pass

    def _shift_relative_move_base_by_delta(self, delta: QPoint) -> None:
        """
        アニメの“基準位置(base)”を平行移動する。
        ドラッグ等でウィンドウを動かした時に呼ぶと、アニメ軌道も一緒に動く。
        """
        self._ensure_relative_move_state()
        if getattr(self, "_rel_base_pos", None) is None:
            return
        self._rel_base_pos = self._rel_base_pos + delta

    def _start_relative_progress_animation(self, on_finished) -> None:
        """
        相対移動：0.0→1.0 の進捗をアニメして、その都度 target_pos を計算して移動する。
        """
        from PySide6.QtCore import QVariantAnimation

        self._ensure_relative_move_state()

        # 既存があれば停止
        if getattr(self, "_rel_move_anim", None) is not None:
            try:
                self._rel_move_anim.stop()
            except Exception:
                pass

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(int(self.move_speed))
        anim.setEasingCurve(self.easing_curve)

        def _on_value_changed(v):
            try:
                t = float(v)
            except Exception:
                return
            self._on_relative_progress_changed(t)

        anim.valueChanged.connect(_on_value_changed)
        anim.finished.connect(on_finished)
        self._rel_move_anim = anim
        anim.start()

    def _on_relative_progress_changed(self, t: float) -> None:
        """
        t(0..1) から target_pos を計算し、現在位置との差分で tree を動かす。
        """
        self._ensure_relative_move_state()

        base = getattr(self, "_rel_base_pos", None)
        if base is None:
            return

        offset = self.get_move_offset()
        if self._is_zero_offset(offset):
            return

        direction = getattr(self, "_rel_direction", 1)
        if direction < 0:
            t = 1.0 - t

        target = base + QPoint(int(offset.x() * t), int(offset.y() * t))
        delta = target - self.pos()
        if delta.x() == 0 and delta.y() == 0:
            return

        self.move_tree_by_delta(delta)

    def _easing_name_from_type(self, curve_type: QEasingCurve.Type) -> str:
        """
        QEasingCurve.Type から名称を引く（保存用）。
        """
        try:
            return QEasingCurve.Type(curve_type).name
        except Exception:
            return "Linear"

    def _apply_easing_from_config(self) -> None:
        """
        config.move_easing / config.fade_easing に保存されているカーブ名を
        runtime（self.easing_curve / self.fade_easing_curve）に反映する。
        - 旧データ互換のため、キーが無い/不正なら Linear にフォールバック
        """
        try:
            move_name = getattr(self.config, "move_easing", "Linear") or "Linear"
            fade_name = getattr(self.config, "fade_easing", "Linear") or "Linear"

            self.easing_curve = getattr(QEasingCurve.Type, str(move_name), QEasingCurve.Type.Linear)
            self.fade_easing_curve = getattr(QEasingCurve.Type, str(fade_name), QEasingCurve.Type.Linear)

            # フェードが既に走ってるなら反映（通常はここではまだ走っていないが安全策）
            if self.fade_animation:
                self.fade_animation.setEasingCurve(self.fade_easing_curve)
        except Exception:
            # 何が起きてもアプリが落ちないように Linear に戻す
            self.easing_curve = QEasingCurve.Type.Linear
            self.fade_easing_curve = QEasingCurve.Type.Linear
            if self.fade_animation:
                try:
                    self.fade_animation.setEasingCurve(self.fade_easing_curve)
                except Exception:
                    pass
