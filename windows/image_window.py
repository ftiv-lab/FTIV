# windows/image_window.py

import io
import logging
import math
import os
import traceback
import warnings
from typing import Any, Dict, List

import shiboken6
from PIL import Image, ImageSequence, PngImagePlugin
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
    QTransform,
)
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QProgressDialog

from models.window_config import ImageWindowConfig
from ui.context_menu import ContextMenuBuilder
from utils.translator import tr

from .base_window import BaseOverlayWindow

logger = logging.getLogger(__name__)

# PngImagePluginの警告を無視
warnings.simplefilter("ignore", PngImagePlugin.PngImageFile)


class ImageWindow(BaseOverlayWindow):
    """画像をオーバーレイ表示するウィンドウクラス。

    GIFアニメーション、回転、拡大縮小、不透明度、反転などの機能を持ち、
    親子関係による変形の伝播もサポートします。
    """

    def __init__(
        self, main_window: Any, image_path: str = "", original_speed: int = 100, position: QPoint = QPoint(0, 0)
    ):
        """ImageWindowの初期化。

        Args:
            main_window (Any): メインウィンドウのインスタンス。
            image_path (str, optional): 読み込む画像パス。 Defaults to "".
            original_speed (int, optional): アニメーションの基本速度。 Defaults to 100.
            position (QPoint, optional): 初回表示位置。 Defaults to QPoint(0, 0).
        """
        super().__init__(main_window, config_class=ImageWindowConfig)

        # 初期値の適用
        self.config.image_path = image_path
        self.config.position = {"x": position.x(), "y": position.y()}
        self.setGeometry(position.x(), position.y(), 100, 100)

        # ディレクトリ管理
        self.json_directory = getattr(self.main_window, "json_directory", os.getcwd())
        self.last_directory: str = ""

        # 画像固有変数の初期化
        self.frames: List[QPixmap] = []
        self.current_frame: int = 0
        self.original_speed: int = original_speed
        self.original_animation_speed_factor: float = self.animation_speed_factor

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.is_rotating: bool = False

        self.setAcceptDrops(True)
        if image_path:
            self.load_image(image_path)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    # --- プロパティ定義 ---
    @property
    def image_path(self) -> str:
        return self.config.image_path

    @image_path.setter
    def image_path(self, value: str):
        self.config.image_path = value if value else ""

    @property
    def scale_factor(self) -> float:
        return self.config.scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.config.scale_factor = float(value)

    @property
    def opacity(self) -> float:
        return self.config.opacity

    @opacity.setter
    def opacity(self, value: float):
        self.config.opacity = float(value)

    @property
    def rotation_angle(self) -> float:
        return self.config.rotation_angle

    @rotation_angle.setter
    def rotation_angle(self, value: float):
        self.config.rotation_angle = float(value)

    @property
    def flip_horizontal(self) -> bool:
        return self.config.flip_horizontal

    @flip_horizontal.setter
    def flip_horizontal(self, value: bool):
        self.config.flip_horizontal = bool(value)

    @property
    def flip_vertical(self) -> bool:
        return self.config.flip_vertical

    @flip_vertical.setter
    def flip_vertical(self, value: bool):
        self.config.flip_vertical = bool(value)

    @property
    def animation_speed_factor(self) -> float:
        return self.config.animation_speed_factor

    @animation_speed_factor.setter
    def animation_speed_factor(self, value: float):
        self.config.animation_speed_factor = float(value)

    @property
    def is_locked(self) -> bool:
        """移動/変形ロック状態。"""
        return bool(getattr(self.config, "is_locked", False))

    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        self.config.is_locked = bool(value)

    def show_context_menu(self, pos: QPoint):
        """右クリックメニューを表示する。"""
        try:
            builder = ContextMenuBuilder(self, self.main_window)

            # 1. 基本操作
            builder.add_action("menu_add_image", self.add_new_image)
            builder.add_action("menu_reselect_image", self.reselect_image)
            builder.add_action("menu_clone_image", self.clone_image)
            builder.add_connect_group_menu()
            builder.add_action("menu_show_properties", self.show_property_panel)
            builder.add_separator()

            # 2. ファイル操作
            builder.add_action("menu_save_image_json", self.save_image_to_json)
            builder.add_action("menu_load_image_json", self.load_image_from_json)
            builder.add_separator()

            # 3. サイズ・不透明度
            builder.add_action("menu_set_image_size_pct", self.open_size_dialog)
            builder.add_action("menu_reset_image_size", self.reset_image_size)
            builder.add_separator()

            builder.add_action("menu_set_opacity", self.open_opacity_dialog)
            builder.add_action("menu_reset_opacity", self.reset_opacity)
            builder.add_separator()

            # 追加：ディスプレイ操作（Fit / Center）
            fit_menu = builder.add_submenu("menu_fit_to_display")
            center_menu = builder.add_submenu("menu_center_on_display")

            try:
                screens = QApplication.screens()
            except Exception as e:
                logger.warning(f"Failed to get screens: {e}")
                screens = []

            for i, _s in enumerate(screens):
                # 例: "Screen 1", "Screen 2" ...（ここは翻訳不要にして短く）
                label = f"Screen {i + 1}"
                builder.add_action(label, lambda checked=False, idx=i: self.fit_to_display(idx), parent_menu=fit_menu)
                builder.add_action(
                    label, lambda checked=False, idx=i: self.center_on_display(idx), parent_menu=center_menu
                )

            builder.add_separator()

            # 4. GIF/APNG 再生（名称を明確化）
            builder.add_action("menu_set_gif_apng_playback_speed", self.open_anim_speed_dialog)
            builder.add_action("menu_toggle_gif_apng_playback", self.toggle_image_animation_speed)
            builder.add_action("menu_reset_gif_apng_playback_speed", self.reset_animation_speed)
            builder.add_separator()

            # 5. 回転・反転
            builder.add_action("menu_set_rotation", self.open_rotation_dialog)
            rot_menu = builder.add_submenu("menu_set_rotation_90")
            for angle in range(0, 271, 90):
                action = builder.add_action(
                    f"{angle}°", self.create_rotation_action_handler(angle), checkable=True, parent_menu=rot_menu
                )
                if angle == int(self.rotation_angle):
                    action.setChecked(True)

            builder.add_action("menu_reset_rotation", self.reset_rotation)
            builder.add_separator()

            builder.add_action("menu_flip_h", self.flip_horizontal_action, checkable=True, checked=self.flip_horizontal)
            builder.add_action("menu_flip_v", self.flip_vertical_action, checkable=True, checked=self.flip_vertical)
            builder.add_separator()

            # --- アニメ関連（移動/フェード）はMainWindowのAnimationタブに一本化済み ---
            builder.add_action(
                "menu_lock_transform",
                lambda checked: self.set_undoable_property("is_locked", bool(checked), None),
                checkable=True,
                checked=self.is_locked,
            )

            # 6. ウィンドウ操作
            builder.add_action(
                "menu_toggle_frontmost_image", self.toggle_frontmost, checkable=True, checked=self.is_frontmost
            )
            builder.add_action("menu_hide_other_images", self.hide_all_other_windows)
            builder.add_action("menu_hide_image", self.hide_action)
            builder.add_action("menu_show_image", self.show_action)
            builder.add_separator()

            builder.add_action("menu_close_other_images", self.close_all_other_images)
            builder.add_action("menu_close_image", self.close_image)
            builder.add_separator()

            builder.add_action(
                "menu_click_through",
                lambda: self.set_click_through(not self.is_click_through),
                checkable=True,
                checked=self.is_click_through,
            )

            builder.exec(self.mapToGlobal(pos))

        except Exception:
            pass  # Suppress context menu errors

    def load_image(self, image_path: str):
        """画像ファイルを読み込み、フレームを構築する。

        Args:
            image_path (str): 読み込む画像ファイルのパス。
        """
        self.frames = []
        if not os.path.exists(image_path):
            self.create_placeholder_image(image_path)
            return

        progress = QProgressDialog(tr("msg_loading_image"), tr("label_cancel"), 0, 100, self)
        progress.setWindowTitle(tr("title_loading"))
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        try:
            with Image.open(image_path) as img:
                if "icc_profile" in img.info:
                    img.info.pop("icc_profile")

                if getattr(img, "is_animated", False):
                    total = img.n_frames
                    for i, frame in enumerate(ImageSequence.Iterator(img)):
                        QApplication.processEvents()
                        if not shiboken6.isValid(self) or progress.wasCanceled():
                            return

                        qimage = self.pillow_image_to_qimage(frame)
                        self.frames.append(QPixmap.fromImage(qimage))
                        progress.setValue(int((i + 1) / total * 100))

                    self.original_speed = int(img.info.get("duration", 100))
                    self._update_animation_timer()
                else:
                    self.frames.append(QPixmap.fromImage(self.pillow_image_to_qimage(img)))
                    self.timer.stop()

                self.last_directory = os.path.dirname(image_path)
                self.current_frame = 0
                self.update_image()
            progress.close()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, tr("msg_error"), tr("msg_error_loading").format(e))
            self.create_placeholder_image(image_path)

    def load_image_wrapper(self):
        """Undo/Redo用の再読み込みラッパー。"""
        if self.image_path:
            self.load_image(self.image_path)

    def create_placeholder_image(self, original_path: str):
        """画像が見つからない場合のプレースホルダーを作成する。"""
        self.image_path = original_path
        self.frames = []
        size = 200
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(40, 40, 40, 200))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.red, 4))
        painter.drawRect(2, 2, size - 4, size - 4)
        painter.drawLine(0, 0, size, size)
        painter.drawLine(size, 0, 0, size)

        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(Qt.white)
        filename = os.path.basename(original_path) if original_path else "Unknown"
        text_rect = QRect(10, size // 2 - 40, size - 20, 80)
        painter.fillRect(text_rect, QColor(0, 0, 0, 150))
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, f"IMAGE NOT FOUND\n{filename}")
        painter.end()

        self.frames.append(pixmap)
        self.current_frame = 0
        self.timer.stop()
        self.update_image()

    def to_dict(self) -> Dict[str, Any]:
        """現在の状態を辞書形式で出力する。"""
        self.config.geometry = {"x": self.x(), "y": self.y(), "width": self.width(), "height": self.height()}
        self.config.position = {"x": self.x(), "y": self.y()}

        # 旧 absolute move は使わない方針：次回保存で消えるよう None に落とす
        if hasattr(self.config, "start_position"):
            self.config.start_position = None
        if hasattr(self.config, "end_position"):
            self.config.end_position = None

        data = self.config.model_dump(mode="json", exclude_none=True)
        data["type"] = "image"
        return data

    def apply_data(self, data: Dict[str, Any]):
        """辞書データから状態を復元する。"""
        try:
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self._update_animation_timer()
            self.is_frontmost = self.config.is_frontmost
            self.is_click_through = self.config.is_click_through

            geo = self.config.geometry
            if geo:
                self.setGeometry(
                    geo.get("x", self.x()), geo.get("y", self.y()), geo.get("width", 100), geo.get("height", 100)
                )

            self.update_image()
            self.show()

            if self.move_loop_enabled:
                self.start_move_animation()
            elif self.move_position_only_enabled:
                self.start_move_position_only_animation()

            if self.is_fading_enabled:
                self.start_fade_in()
            elif self.fade_in_only_loop_enabled:
                self.start_fade_in_only()
            elif self.fade_out_only_loop_enabled:
                self.start_fade_out_only()

            if self.is_hidden:
                self.hide_action()

        except Exception:
            # Loading data errors are non-critical here (failed restore)
            pass

    def pillow_image_to_qimage(self, pillow_image: Image.Image) -> QImage:
        """PILの画像をQImageに変換する。"""
        buffer = io.BytesIO()
        pillow_image.save(buffer, format="PNG")
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        return qimage

    def update_image(self):
        """現在のフレームに変形（回転、拡大、反転、不透明度）を適用して描画を更新する。"""
        try:
            if not self.frames:
                return
            pixmap = self.frames[self.current_frame]
            scaled = pixmap.scaled(pixmap.size() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            transform = QTransform()
            transform.translate(scaled.width() / 2, scaled.height() / 2)
            transform.rotate(self.rotation_angle)
            if self.flip_horizontal:
                transform.scale(-1, 1)
            if self.flip_vertical:
                transform.scale(1, -1)
            transform.translate(-scaled.width() / 2, -scaled.height() / 2)

            transformed_pixmap = scaled.transformed(transform, mode=Qt.SmoothTransformation)

            final_pixmap = QPixmap(transformed_pixmap.size())
            final_pixmap.fill(Qt.transparent)
            painter = QPainter(final_pixmap)
            painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            painter.setOpacity(self.opacity)
            painter.drawPixmap(0, 0, transformed_pixmap)
            painter.end()

            self.setPixmap(final_pixmap)
            self.resize(final_pixmap.width(), final_pixmap.height())
            self.config.geometry["width"], self.config.geometry["height"] = self.width(), self.height()
            self.sig_properties_changed.emit(self)
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Error updating image: {e}")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        self.draw_selection_frame(painter)
        painter.end()

    def next_frame(self):
        """GIFの次フレームへ更新する。"""
        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.update_image()

    def mouseDoubleClickEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl+Double Click: BaseOverlayWindowのロジック（移動/フェードアニメのトグル）へ
            super().mouseDoubleClickEvent(event)
            return

        # Default: GIF/APNG アニメ速度切替
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_image_animation_speed()

    def wheelEvent(self, event) -> None:
        """マウスホイールイベント。

        ロック中は拡大縮小を無効化する。
        """
        try:
            # ロック中は拡大縮小を止める
            if getattr(self, "is_locked", False):
                event.accept()
                return

            old_scale = self.scale_factor
            step = 0.99 if (event.modifiers() & Qt.ShiftModifier) else 0.9
            if event.angleDelta().y() < 0:
                step = 1.0 / step

            self.scale_factor *= step
            self.update_image()
            if old_scale != 0:
                self.propagate_scale_to_children(self.scale_factor / old_scale)

            event.accept()
        except Exception:
            traceback.print_exc()

    def keyPressEvent(self, event) -> None:
        """キー押下イベント。

        ロック中は配置が変わる操作（ノード追加/ナビ/変形）を無効化する。
        ただし管理系（Delete/H/F）は許可する。
        """
        try:
            # --- 管理系（ロック中でも許可）---
            if event.key() == Qt.Key_Delete:
                self.close_image()
                event.accept()
                return

            if event.key() == Qt.Key_H:
                self.hide_action()
                event.accept()
                return

            if event.key() == Qt.Key_F:
                self.toggle_frontmost()
                event.accept()
                return

            # --- ロック中はここから先を止める ---
            if getattr(self, "is_locked", False):
                event.accept()
                return

            # --- 配置/ノード操作（TextWindowに合わせる）---
            if event.key() == Qt.Key_Tab:
                # 必要なら子ノード作成などを実装可。現状はパス。
                event.accept()
                return

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # 必要なら兄弟ノード作成などを実装可。現状はパス。
                event.accept()
                return

            # --- ナビゲーション（TextWindowに合わせる）---
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                if hasattr(self.main_window, "window_manager") and hasattr(
                    self.main_window.window_manager, "navigate_selection"
                ):
                    self.main_window.window_manager.navigate_selection(self, event.key())
                event.accept()
                return

        except Exception:
            traceback.print_exc()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """D&Dで画像差し替え（安全・Undo対応に寄せる）。"""
        if not event.mimeData().hasUrls():
            return

        path = event.mimeData().urls()[0].toLocalFile()
        if not path:
            return

        self.last_directory = os.path.dirname(path)
        self.set_undoable_property("image_path", path, "load_image_wrapper")

        if self.main_window and hasattr(self.main_window, "update_image_window_list"):
            self.main_window.update_image_window_list()

        event.acceptProposedAction()

    # --- 基本セッター ---
    def set_opacity(self, value: float):
        self.opacity = float(value)
        self.update_image()

    def set_rotation_angle(self, angle: float):
        self.rotation_angle = float(angle)
        self.update_image()

    def set_animation_speed_factor(self, factor: float):
        self.animation_speed_factor = float(factor)
        self._update_animation_timer()

    def _open_image_slider_dialog(
        self,
        title: str,
        label: str,
        min_val: int,
        max_val: int,
        initial_val: int,
        property_name: str,
        update_method_name: str,
        decimals: int = 0,
        suffix: str = "",
        unit_scale: float = 1.0,
    ) -> None:
        """プレビュー中Undoなし・OKで1回Undoのスライダーダイアログ共通処理。

        Args:
            title (str): ダイアログタイトル
            label (str): ラベル
            min_val (int): 最小（UI値）
            max_val (int): 最大（UI値）
            initial_val (int): 初期（UI値）
            property_name (str): 内部プロパティ名（例: opacity / scale_factor / rotation_angle / animation_speed_factor）
            update_method_name (str): 反映用メソッド名（例: update_image / _update_animation_timer）
            decimals (int): 小数桁（UI側）
            suffix (str): UI表示サフィックス（例: "%"）
            unit_scale (float): UI値→内部値変換倍率（例: 100.0 なら UI=100 -> internal=1.0）
        """
        try:
            from ui.dialogs import PreviewCommitDialog
            from utils.commands import PropertyChangeCommand

            # 現在値（内部値）を保存して Cancel 復帰に使う
            try:
                old_internal: float = float(getattr(self, property_name))
            except Exception:
                old_internal = 0.0

            # UI値から内部値へ変換
            def _to_internal(ui_val: float) -> float:
                try:
                    return float(ui_val) / float(unit_scale)
                except Exception:
                    return float(ui_val)

            # 内部値からUI値へ変換（Cancel復帰用）
            def _to_ui(internal_val: float) -> float:
                try:
                    return float(internal_val) * float(unit_scale)
                except Exception:
                    return float(internal_val)

            def _apply_internal(val_internal: float) -> None:
                """Undoなしで内部値を適用して更新（プレビュー用）。"""
                try:
                    setattr(self, property_name, float(val_internal))
                except Exception:
                    return

                try:
                    if update_method_name and hasattr(self, update_method_name):
                        getattr(self, update_method_name)()
                    else:
                        # フォールバック
                        if hasattr(self, "update_image"):
                            self.update_image()
                except Exception:
                    pass

            def on_preview(ui_val: float) -> None:
                _apply_internal(_to_internal(ui_val))

            def on_commit(ui_val: float) -> None:
                """OK確定時に1回だけUndoを積む。"""
                new_internal: float = _to_internal(ui_val)

                # プレビューで既に new が適用されている可能性があるが、Undo記録は old->new で1回にする
                if float(new_internal) == float(old_internal):
                    # 何も変わっていないなら何もしない
                    _apply_internal(old_internal)
                    return

                # 念のため確定値を適用
                _apply_internal(new_internal)

                # Undo登録
                try:
                    mw = getattr(self, "main_window", None)
                    if mw is not None and hasattr(mw, "undo_stack"):
                        mw.undo_stack.push(
                            PropertyChangeCommand(self, property_name, old_internal, new_internal, update_method_name)
                        )
                except Exception:
                    pass

            # Cancel時に戻す値（ui値）
            cancel_ui_val: float = _to_ui(old_internal)

            dialog = PreviewCommitDialog(
                title=title,
                label=label,
                min_val=float(min_val),
                max_val=float(max_val),
                initial_val=float(cancel_ui_val),
                on_preview=on_preview,
                on_commit=on_commit,
                parent=self,
                suffix=suffix,
                decimals=decimals,
            )
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to open dialog: {e}")
            traceback.print_exc()

    def open_opacity_dialog(self):
        self._open_image_slider_dialog(
            tr("title_set_opacity"),
            tr("label_opacity"),
            0,
            100,
            int(self.opacity * 100),
            "opacity",
            "update_image",
            unit_scale=100.0,
        )

    def open_size_dialog(self):
        self._open_image_slider_dialog(
            tr("title_set_image_size_pct_input"),
            tr("label_size_pct_range"),
            1,
            500,
            int(self.scale_factor * 100),
            "scale_factor",
            "update_image",
            suffix="%",
            unit_scale=100.0,
        )

    def open_rotation_dialog(self):
        self._open_image_slider_dialog(
            tr("title_set_rotation"),
            tr("label_rotation_angle_range"),
            0,
            360,
            int(self.rotation_angle),
            "rotation_angle",
            "update_image",
        )

    def _update_animation_timer(self):
        """タイマーの状態を現在の設定に基づいて更新する。"""
        if self.original_speed > 0 and self.animation_speed_factor > 0:
            self.timer.start(int(self.original_speed / self.animation_speed_factor))
        else:
            self.timer.stop()
        self.sig_properties_changed.emit(self)

    def open_anim_speed_dialog(self):
        self._open_image_slider_dialog(
            tr("title_anim_speed"),
            tr("label_anim_speed"),
            0,
            500,
            int(self.animation_speed_factor * 100),
            "animation_speed_factor",
            "_update_animation_timer",
            unit_scale=100.0,
        )

    # --- 各種アクション ---
    def create_rotation_action_handler(self, angle: int):
        return lambda: self.set_undoable_property("rotation_angle", float(angle), "update_image")

    def reset_flip(self) -> None:
        """左右/上下反転を両方OFFに戻す（MainWindowの一括操作互換用）。"""
        # Undo対応（BaseOverlayWindowの set_undoable_property を利用）
        if hasattr(self.main_window, "undo_stack"):
            try:
                self.main_window.undo_stack.beginMacro("Reset Flip")
            except Exception:
                pass
        try:
            self.set_undoable_property("flip_horizontal", False, "update_image")
            self.set_undoable_property("flip_vertical", False, "update_image")
        finally:
            if hasattr(self.main_window, "undo_stack"):
                try:
                    self.main_window.undo_stack.endMacro()
                except Exception:
                    pass

    def reset_rotation(self):
        self.set_undoable_property("rotation_angle", 0.0, "update_image")

    def flip_horizontal_action(self):
        self.set_undoable_property("flip_horizontal", not self.flip_horizontal, "update_image")

    def flip_vertical_action(self):
        self.set_undoable_property("flip_vertical", not self.flip_vertical, "update_image")

    def reset_opacity(self):
        self.set_undoable_property("opacity", 1.0, "update_image")

    def reset_image_size(self):
        self.set_undoable_property("scale_factor", 1.0, "update_image")

    def reset_animation_speed(self):
        self.set_undoable_property("animation_speed_factor", 1.0, "_update_animation_timer")

    def toggle_image_animation_speed(self):
        """アニメーション再生/停止を切り替える。"""
        if self.animation_speed_factor > 0:
            self.original_animation_speed_factor = self.animation_speed_factor
            new_speed = 0.0
        else:
            new_speed = self.original_animation_speed_factor
        self.set_undoable_property("animation_speed_factor", new_speed, "_update_animation_timer")

    def add_new_image(self) -> None:
        """新規画像ウィンドウを追加する（正規ルートに統一）。

        方針:
            - ファイル選択 → MainWindow.add_image_from_path() に委譲
            - 生成・管理・シグナル接続は MainWindow/WindowManager 側に統一
        """
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("title_select_new_image"),
                self.last_directory,
                "Image Files (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff *.gif *.ico *.tga *.ppm)",
            )
            if not path:
                return

            self.last_directory = os.path.dirname(path)

            mw: Any = getattr(self, "main_window", None)
            if mw is None:
                QMessageBox.warning(self, tr("msg_warning"), "MainWindow is not available.")
                return

            # 正規ルート (ImageActions)
            if hasattr(mw, "img_actions") and hasattr(mw.img_actions, "add_image_from_path"):
                mw.img_actions.add_image_from_path(path)
                return

            # コントローラー経由のフォールバック
            if hasattr(mw, "main_controller") and hasattr(mw.main_controller, "image_actions"):
                mw.main_controller.image_actions.add_image_from_path(path)
                return

            # 互換フォールバック（基本ここには来ない想定）
            if hasattr(mw, "window_manager"):
                mw.window_manager.add_image_window(path, pos=mw.mapToGlobal(QPoint(50, 50)))
                return

            QMessageBox.warning(self, tr("msg_warning"), "No image add route is available.")

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Error adding image: {e}")
            traceback.print_exc()

    def reselect_image(self):
        """現在のウィンドウの画像を差し替える（互換・安全性強化）。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("title_reselect_image"),
            self.last_directory,
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff *.gif *.ico *.tga *.ppm)",
        )
        if not path:
            return

        self.last_directory = os.path.dirname(path)

        # Undo/Redo 対応で差し替え
        self.set_undoable_property("image_path", path, "load_image_wrapper")

        # 互換（現状 no-op だが、将来一覧UIを作った時にも活きる）
        if self.main_window and hasattr(self.main_window, "update_image_window_list"):
            self.main_window.update_image_window_list()

    def close_image(self):
        self.close()

    def closeEvent(self, event):
        if hasattr(self, "timer"):
            self.timer.stop()
        super().closeEvent(event)

    def clone_image(self) -> None:
        """現在の画像ウィンドウを複製する（WindowManager に委譲）。

        目的:
            - 複製の生成経路を WindowManager に統一し、制限・選択同期・シグナル接続の整合性を保つ。
        """
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                QMessageBox.warning(self, tr("msg_warning"), "WindowManager is not available.")
                return

            mw.window_manager.clone_image_window(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to clone image: {e}")
            traceback.print_exc()

    def get_filename(self) -> str:
        return os.path.basename(self.image_path) if self.image_path else tr("unnamed_image")

    def hide_all_other_windows(self) -> None:
        """自分以外の画像を隠す（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.hide_all_other_image_windows(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to hide other images: {e}")
            traceback.print_exc()

    def close_all_other_images(self) -> None:
        """自分以外の画像を閉じる（WindowManager に委譲）。"""
        try:
            mw: Any = getattr(self, "main_window", None)
            if mw is None or not hasattr(mw, "window_manager"):
                return

            mw.window_manager.close_all_other_images(self)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to close other images: {e}")
            traceback.print_exc()

    def save_image_to_json(self):
        """現在の画像設定をJSONに保存します（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.save_window_to_json(self)

    def load_image_from_json(self):
        """JSONから画像設定を読み込みます（FileManagerに委譲）。"""
        if self.main_window and hasattr(self.main_window, "file_manager"):
            self.main_window.file_manager.load_window_from_json(self)

    def show_property_panel(self):
        self.sig_request_property_panel.emit(self)

    def propagate_scale_to_children(self, ratio: float):
        """親子関係にある子ウィンドウに拡大率を伝播させる。"""
        if not self.child_windows:
            return
        p_center = self.geometry().center()
        for child in self.child_windows:
            try:
                vec = (child.geometry().center() - p_center) * ratio
                new_center = p_center + vec
                if hasattr(child, "scale_factor"):
                    child.scale_factor *= ratio
                    child.update_image()
                elif hasattr(child, "font_size"):
                    child.font_size = float(child.font_size) * ratio
                    if hasattr(child, "background_corner_radius"):
                        child.background_corner_radius = int(
                            child.font_size * getattr(child, "background_corner_ratio", 0)
                        )
                    child.update_text()
                child.move(int(new_center.x() - child.width() / 2), int(new_center.y() - child.height() / 2))
                if hasattr(child, "propagate_scale_to_children"):
                    child.propagate_scale_to_children(ratio)

            except Exception:
                pass  # Propagation fail should not crash

    def propagate_rotation_to_children(self, delta_angle: float):
        """親子関係にある子ウィンドウに回転角度を伝播させる。"""
        if not self.child_windows:
            return
        p_center, rad = self.geometry().center(), math.radians(delta_angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        for child in self.child_windows:
            try:
                c_center = child.geometry().center()
                dx, dy = c_center.x() - p_center.x(), c_center.y() - p_center.y()
                new_center = QPoint(
                    int(p_center.x() + (dx * cos_a - dy * sin_a)), int(p_center.y() + (dx * sin_a + dy * cos_a))
                )
                child.move(new_center.x() - child.width() // 2, new_center.y() - child.height() // 2)
                if hasattr(child, "rotation_angle"):
                    child.rotation_angle += delta_angle
                    child.update_image()
                if hasattr(child, "propagate_rotation_to_children"):
                    child.propagate_rotation_to_children(delta_angle)

            except Exception:
                pass  # Propagation fail should not crash

    def fit_to_display(self, screen_index: int, use_available_geometry: bool = True) -> None:
        """指定ディスプレイに対して、画像を最大表示（アスペクト比維持）＋中央配置する。

        Args:
            screen_index (int): 対象ディスプレイのインデックス（QApplication.screens() の順）。
            use_available_geometry (bool): True の場合 availableGeometry（タスクバー除外）を使う。
        """
        try:
            screens = QApplication.screens()
            if not screens or screen_index < 0 or screen_index >= len(screens):
                return

            screen = screens[screen_index]
            geo = screen.availableGeometry() if use_available_geometry else screen.geometry()

            if not self.frames:
                # 未ロード等
                return

            # 回転はここでは考慮しない（v1：まずは簡単・安定を優先）
            base = self.frames[self.current_frame]
            bw = max(1, int(base.width()))
            bh = max(1, int(base.height()))

            # 画面内に収める最大倍率（KeepAspect）
            sx = float(geo.width()) / float(bw)
            sy = float(geo.height()) / float(bh)
            new_scale = max(0.01, min(sx, sy))

            # Undo対応（1操作にまとめる）
            if hasattr(self.main_window, "undo_stack"):
                try:
                    self.main_window.undo_stack.beginMacro("Fit to Display")
                except Exception:
                    pass

            try:
                if hasattr(self, "set_undoable_property"):
                    self.set_undoable_property("scale_factor", float(new_scale), "update_image")
                else:
                    self.scale_factor = float(new_scale)
                    self.update_image()

                # update_image 後のサイズで中央配置
                self._center_to_geometry(geo)

            finally:
                if hasattr(self.main_window, "undo_stack"):
                    try:
                        self.main_window.undo_stack.endMacro()
                    except Exception:
                        pass

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to fit image to display: {e}")
            traceback.print_exc()

    def center_on_display(self, screen_index: int, use_available_geometry: bool = True) -> None:
        """指定ディスプレイの中央へ移動する（サイズは変更しない）。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
            use_available_geometry (bool): True の場合 availableGeometry を使う。
        """
        try:
            screens = QApplication.screens()
            if not screens or screen_index < 0 or screen_index >= len(screens):
                return

            screen = screens[screen_index]
            geo = screen.availableGeometry() if use_available_geometry else screen.geometry()

            self._center_to_geometry(geo)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to center image on display: {e}")
            traceback.print_exc()

    def _center_to_geometry(self, geo: QRect) -> None:
        """指定ジオメトリの中央へウィンドウを移動する（内部用）。

        Args:
            geo (QRect): 中央配置の基準領域。
        """
        try:
            target_x = int(geo.x() + (geo.width() - self.width()) / 2)
            target_y = int(geo.y() + (geo.height() - self.height()) / 2)

            old_pos = self.pos()

            self.move(target_x, target_y)
            if hasattr(self, "config"):
                self.config.position = {"x": int(self.x()), "y": int(self.y())}

            # Undo（MoveWindowCommand を使う）
            try:
                if hasattr(self.main_window, "add_undo_command"):
                    from utils.commands import MoveWindowCommand

                    cmd = MoveWindowCommand(self, old_pos, self.pos())
                    self.main_window.add_undo_command(cmd)
            except Exception:
                pass

            # 接続線があれば更新
            try:
                for line in getattr(self, "connected_lines", []):
                    try:
                        line.update_position()
                    except Exception:
                        pass
            except Exception:
                pass

        except Exception:
            pass

    def snap_to_display_edge(self, screen_index: int, edge: str, use_available_geometry: bool = True) -> None:
        """指定ディスプレイの端にスナップする（サイズは変えない）。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
            edge (str): "left" | "right" | "top" | "bottom"
            use_available_geometry (bool): True の場合 availableGeometry を使う。
        """
        try:
            screens = QApplication.screens()
            if not screens or screen_index < 0 or screen_index >= len(screens):
                return

            screen = screens[screen_index]
            geo = screen.availableGeometry() if use_available_geometry else screen.geometry()

            x = self.x()
            y = self.y()

            if edge == "left":
                x = int(geo.left())
            elif edge == "right":
                x = int(geo.right() - self.width())
            elif edge == "top":
                y = int(geo.top())
            elif edge == "bottom":
                y = int(geo.bottom() - self.height())
            else:
                return

            old_pos = self.pos()
            self.move(int(x), int(y))
            if hasattr(self, "config"):
                self.config.position = {"x": int(self.x()), "y": int(self.y())}

            # Undo
            try:
                if hasattr(self.main_window, "add_undo_command"):
                    from utils.commands import MoveWindowCommand

                    self.main_window.add_undo_command(MoveWindowCommand(self, old_pos, self.pos()))
            except Exception:
                pass

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to snap to edge: {e}")
            traceback.print_exc()

    def snap_to_display_corner(self, screen_index: int, corner: str, use_available_geometry: bool = True) -> None:
        """指定ディスプレイの四隅にスナップする（サイズは変えない）。

        Args:
            screen_index (int): 対象ディスプレイのインデックス。
            corner (str): "tl" | "tr" | "bl" | "br"
            use_available_geometry (bool): True の場合 availableGeometry を使う。
        """
        try:
            screens = QApplication.screens()
            if not screens or screen_index < 0 or screen_index >= len(screens):
                return

            screen = screens[screen_index]
            geo = screen.availableGeometry() if use_available_geometry else screen.geometry()

            if corner == "tl":
                x = int(geo.left())
                y = int(geo.top())
            elif corner == "tr":
                x = int(geo.right() - self.width())
                y = int(geo.top())
            elif corner == "bl":
                x = int(geo.left())
                y = int(geo.bottom() - self.height())
            elif corner == "br":
                x = int(geo.right() - self.width())
                y = int(geo.bottom() - self.height())
            else:
                return

            old_pos = self.pos()
            self.move(int(x), int(y))
            if hasattr(self, "config"):
                self.config.position = {"x": int(self.x()), "y": int(self.y())}

            # Undo
            try:
                if hasattr(self.main_window, "add_undo_command"):
                    from utils.commands import MoveWindowCommand

                    self.main_window.add_undo_command(MoveWindowCommand(self, old_pos, self.pos()))
            except Exception:
                pass

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), f"Failed to snap to corner: {e}")
            traceback.print_exc()
