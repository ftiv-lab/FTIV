import logging
import math
import traceback
from typing import Any, Optional

import shiboken6
from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
    QRegion,
)
from PySide6.QtWidgets import QColorDialog, QDialog, QInputDialog, QWidget

from models.constants import AppDefaults
from models.enums import AnchorPosition, ArrowStyle
from models.window_config import TextWindowConfig
from ui.context_menu import ContextMenuBuilder
from ui.dialogs import (
    SliderSpinDialog,
    TextInputDialog,
    TextSpacingDialog,
)
from utils.font_dialog import choose_font
from utils.translator import tr
from windows.base_window import BaseOverlayWindow
from windows.mixins.inline_editor_mixin import InlineEditorMixin
from windows.mixins.text_properties_mixin import TextPropertiesMixin

logger = logging.getLogger(__name__)


class ConnectorLabel(TextPropertiesMixin, InlineEditorMixin, BaseOverlayWindow):  # type: ignore
    """
    接続線の上に表示されるラベル専用のウィンドウ
    TextWindowとほぼ同じ機能を持つが、位置はConnectorLineによって管理される
    """

    def __init__(self, main_window: Any, connector: Any, text: str = "") -> None:
        """ConnectorLine上に表示されるラベル専用ウィンドウを初期化する。

        Args:
            main_window (Any): MainWindow 相当。
            connector (Any): 親となる ConnectorLine。
            text (str): 初期テキスト。
        """
        # TextWindowConfigを使用して初期化
        BaseOverlayWindow.__init__(self, main_window, config_class=TextWindowConfig)
        InlineEditorMixin.__init__(self)

        self.connector: Any = connector

        try:
            self._init_text_renderer(main_window)
        except Exception:
            pass

        # 初期設定
        self.config.text = str(text or "")
        self.config.font_size = 14
        self.config.font_color = "#ffffff"

        # デフォルトで少しリッチに見えるように設定
        self.config.background_color = "#222222"
        self.config.background_opacity = 80
        self.config.background_corner_ratio = 0.5
        self.config.horizontal_margin_ratio = 0.2
        self.config.vertical_margin_ratio = 0.1

        # 影をデフォルトでON
        self.config.shadow_enabled = True
        self.config.shadow_blur = 5
        self.config.shadow_opacity = 60

        # ドラッグ無効（位置は線に従うため）
        self.setAcceptDrops(False)

        # コンテキストメニュー
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 初回描画は即時で行う（初期表示が遅れないように）
        self._update_text_immediate()

    # ==========================================
    # Property Definitions
    # Moved to TextPropertiesMixin
    # ==========================================

    # ==========================================
    # Methods
    # ==========================================

    def _update_text_immediate(self) -> None:
        """TextRendererを使用して即時描画する（内部用）。"""
        try:
            # Mixinの描画処理を呼ぶ（setPixmap, sig_properties_changed）
            super()._update_text_immediate()

            # --- ConnecotrLabel固有の処理 ---

            # CanvasSizeに合わせてリサイズ（当たり判定用）
            # Note: TextRenderer.render で self.canvas_size が更新されている前提
            if hasattr(self, "canvas_size") and self.canvas_size:
                if not getattr(self, "_is_editing", False):
                    self.resize(self.canvas_size)

            # 親のコネクタ位置も再計算
            if self.connector:
                try:
                    self.connector.update_position()
                except Exception as e:
                    logger.error(f"Failed to update connector position from label: {e}")

        except Exception as e:
            logger.error(f"Failed to render connector label: {e}\n{traceback.format_exc()}")

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        self.draw_selection_frame(painter)
        painter.end()

    def closeEvent(self, event: Any) -> None:
        """ラベルが閉じられた場合の互換通知（元の方針へ戻す）。

        Notes:
            ConnectorLabel が予期せず閉じられた時に、上位側が状態を保てるよう
            互換シグナルを出す（既存挙動に合わせる）。
        """
        try:
            try:
                self.sig_connector_deleted.emit(self)
            except Exception:
                pass
        finally:
            try:
                event.accept()
            except Exception:
                pass

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # InlineEditorMixin start
            self._start_inline_edit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        """
        ラベルがクリックされた時の処理。
        親の線ではなく、このラベル自体を選択状態にしてプロパティパネルを表示させる。
        """
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                # 自分(Label)を選択状態にする
                if self.main_window:
                    self.main_window.set_last_selected_window(self)

                # 視覚的に分かりやすくするため、親の線も選択表示にする（オプション）
                if self.connector:
                    self.connector.set_selected(True)

                # ★修正: ドラッグ開始座標などを記録するために親クラスの処理も呼ぶが、
                # is_dragging フラグは直後に False にして移動を防ぐ
                super().mousePressEvent(event)
                self.is_dragging = False  # 強制的にドラッグ不可にする

                event.accept()
            else:
                super().mousePressEvent(event)
        except Exception:
            pass

    def edit_text_realtime(self):
        original_text = self.text

        def live_update(new_text):
            self.text = new_text
            self.update_text()

        dialog = TextInputDialog(self.text, self, callback=live_update)

        screen_geo = self.screen().availableGeometry()
        dlg_w = dialog.width()
        dlg_h = dialog.height()
        target_x = self.x() + self.width() + 20
        target_y = self.y()
        if target_x + dlg_w > screen_geo.right():
            target_x = self.x() - dlg_w - 20
        if target_y + dlg_h > screen_geo.bottom():
            target_y = screen_geo.bottom() - dlg_h
        dialog.move(target_x, target_y)

        if dialog.exec() == QDialog.Accepted:
            final_text = dialog.get_text()
            if final_text != original_text:
                self.set_undoable_property("text", final_text, "update_text")
        else:
            try:
                self.text = original_text
                self.update_text()
            except Exception:
                pass

    # --- 余白設定用メソッド (★追加) ---

    def _apply_label_layout_change(self, fn: Any, macro_name: str = "Change Label Layout") -> None:
        """ラベルのレイアウト系変更を Undo マクロでまとめて実行する。

        Args:
            fn (Any): 実行する処理（例: set_undoable_property を複数呼ぶ関数）
            macro_name (str): Undoマクロ名
        """
        mw = getattr(self, "main_window", None)
        stack = getattr(mw, "undo_stack", None) if mw is not None else None

        if stack is not None:
            try:
                stack.beginMacro(macro_name)
            except Exception:
                stack = None

        try:
            fn()
        finally:
            if stack is not None:
                try:
                    stack.endMacro()
                except Exception:
                    pass

    def open_spacing_settings(self):
        """余白・文字間隔の一括設定ダイアログを開く"""
        # 縦書き/横書きに応じた値でダイアログを初期化
        if self.is_vertical:
            dialog = TextSpacingDialog(
                self.horizontal_margin_ratio,
                self.vertical_margin_ratio,
                self.v_margin_top_ratio,
                self.v_margin_bottom_ratio,
                self.v_margin_left_ratio,
                self.v_margin_right_ratio,
                self,
                is_vertical=True,
            )
        else:
            dialog = TextSpacingDialog(
                self.horizontal_margin_ratio,
                self.vertical_margin_ratio,
                self.margin_top_ratio,
                self.margin_bottom_ratio,
                self.margin_left_ratio,
                self.margin_right_ratio,
                self,
                is_vertical=False,
            )

        if dialog.exec() == QDialog.Accepted:
            values_dict = dialog.get_values_dict()
            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.beginMacro("Change Label Spacing")

            # 辞書の最後のキー以外は update_text を None に
            keys = list(values_dict.keys())
            for key in keys[:-1]:
                self.set_undoable_property(key, values_dict[key], None)
            # 最後のキーで update_text を呼ぶ
            self.set_undoable_property(keys[-1], values_dict[keys[-1]], "update_text")

            if hasattr(self.main_window, "undo_stack"):
                self.main_window.undo_stack.endMacro()

    def show_context_menu(self, pos) -> None:
        """ラベル専用の右クリックメニュー（充実版）を表示する。"""
        try:
            builder = ContextMenuBuilder(self, self.main_window)

            # --- 1) すぐ編集 ---
            builder.add_action("menu_add_label", self.edit_text_realtime)
            builder.add_action("menu_clear_label_text", lambda checked=False: self._clear_label_text())

            builder.add_separator()

            # --- 2) プロパティ ---
            builder.add_action(
                "menu_show_properties", lambda checked=False: self.main_window.on_request_property_panel(self)
            )

            builder.add_separator()

            # --- 3) 簡易スタイル（頻出だけ） ---
            quick = builder.add_submenu("menu_label_quick_style")
            builder.add_action("menu_change_font", lambda checked=False: self._change_label_font(), parent_menu=quick)
            builder.add_action(
                "menu_change_color", lambda checked=False: self._change_label_font_color(), parent_menu=quick
            )
            builder.add_action(
                "menu_change_bg_color", lambda checked=False: self._change_label_bg_color(), parent_menu=quick
            )
            builder.add_action(
                "menu_change_bg_opacity", lambda checked=False: self._change_label_bg_opacity(), parent_menu=quick
            )

            builder.add_separator()

            # --- 4) 縦書き設定（Undoマクロ） ---
            builder.add_action(
                "menu_toggle_vertical",
                lambda checked=False: self._apply_label_layout_change(
                    lambda: self.set_undoable_property("is_vertical", not self.is_vertical, "update_text"),
                    "Toggle Label Vertical",
                ),
                checkable=True,
                checked=self.is_vertical,
            )

            builder.add_separator()

            # --- 5) 余白 ---
            builder.add_action("menu_margin_settings", self.open_spacing_settings)

            builder.add_separator()

            # --- 6) スタイルプリセット ---
            if hasattr(self.main_window, "style_manager"):
                style_menu = builder.add_submenu("menu_style_presets")
                builder.add_action(
                    "menu_open_style_gallery", lambda checked=False: self.open_style_gallery(), parent_menu=style_menu
                )
                builder.add_separator(parent_menu=style_menu)
                builder.add_action(
                    "menu_save_style",
                    lambda checked=False: self.main_window.style_manager.save_text_style(self),
                    parent_menu=style_menu,
                )

            builder.add_separator()

            # --- 7) 線の操作 ---
            builder.add_action("menu_open_connector_menu", lambda checked=False: self._open_parent_line_menu())
            builder.add_action(
                "menu_delete_line", lambda checked=False: self.connector.delete_line() if self.connector else None
            )

            builder.exec(self.mapToGlobal(pos))

        except Exception:
            pass

    def open_style_gallery(self):
        from ui.dialogs import StyleGalleryDialog

        dialog = StyleGalleryDialog(self.main_window.style_manager, self)
        if dialog.exec() == QDialog.Accepted:
            json_path = dialog.get_selected_style_path()
            if json_path:
                self.main_window.style_manager.load_text_style(self, json_path)

    def wheelEvent(self, event: Any) -> None:
        """マウスホイールでフォントサイズを拡大縮小（Undo対応＋デバウンス）。

        方針:
            - 変更は set_undoable_property('font_size', ...) でUndoに積む
            - 描画は即時ではなく update_text_debounced() で最後の1回に寄せる

        Args:
            event (Any): QWheelEvent
        """
        if self._is_editing:
            return

        try:
            delta: int = int(event.angleDelta().y())
            if delta == 0:
                event.accept()
                return

            old_size: float
            try:
                old_size = float(self.font_size)
            except Exception:
                old_size = float(getattr(self.config, "font_size", AppDefaults.CONNECTOR_FONT_SIZE))

            # 上回転(delta > 0) -> 縮小、下回転(delta < 0) -> 拡大（既存挙動を維持）
            factor: float = 0.9 if delta > 0 else 1.1
            new_size_f: float = float(old_size) * factor

            # 安全策
            new_size_i: int = max(1, min(500, int(round(new_size_f))))
            old_size_i: int = max(1, min(500, int(round(old_size))))

            if new_size_i == old_size_i:
                event.accept()
                return

            # Undoは積むが、即レンダ(update_text)は走らせない
            # ConnectorLabel側は update_method_name=None にして描画をデバウンス予約
            self.set_undoable_property("font_size", int(new_size_i), None)
            self.update_text_debounced()

            # ホイール中だけデバウンスを強める
            try:
                val = getattr(self, "_wheel_debounce_setting", AppDefaults.WHEEL_DEBOUNCE_MS)
                self._render_debounce_ms = int(val)
                self._wheel_render_relax_timer.start(150)
            except Exception:
                pass

            event.accept()

        except Exception:
            try:
                event.accept()
            except Exception:
                pass

    def set_undoable_property(
        self,
        property_name: str,
        new_value: Any,
        update_method_name: Optional[str] = None,
    ) -> None:
        """Undo可能な形式でプロパティを変更する（ConnectorLabel用の最適化）。

        Notes:
            font_size は連打されやすく、update_text が重い。
            そのため font_size 変更時は update_text を即時実行せず、デバウンス予約に寄せる。

        Args:
            property_name (str): 変更プロパティ名。
            new_value (Any): 新しい値。
            update_method_name (Optional[str]): 通常の更新メソッド名。
        """
        if property_name == "font_size":
            super().set_undoable_property(property_name, new_value, None)
            self.update_text_debounced()
            return

        super().set_undoable_property(property_name, new_value, update_method_name)

    def _toggle_label_visibility(self) -> None:
        """このラベルを表示/非表示する（テキスト空＋hide を含む）。"""
        try:
            cur = str(getattr(self, "text", "") or "")
            if cur.strip():
                # OFF：テキストを消して隠す
                self._apply_label_layout_change(
                    lambda: self.set_undoable_property("text", "", "update_text"),
                    "Hide Label",
                )
                try:
                    self.hide_action()
                except Exception:
                    self.hide()
            else:
                # ON：編集へ誘導（空だと見えないため）
                try:
                    if self.isHidden():
                        self.show()
                except Exception:
                    pass
                self.edit_text_realtime()
        except Exception:
            pass

    def _clear_label_text(self) -> None:
        """ラベル文字を消して非表示にする（1 hooking）。"""
        try:
            self._apply_label_layout_change(
                lambda: self.set_undoable_property("text", "", "update_text"),
                "Clear Label Text",
            )
            try:
                self.hide_action()
            except Exception:
                self.hide()
        except Exception:
            pass

    def _change_label_font(self) -> None:
        """ラベルのフォントを変更する（OK確定でUndo1回のまとまり）。"""
        try:
            font = choose_font(self, QFont(self.font_family, int(self.font_size)))
            if font is None:
                return

            def _apply() -> None:
                self.set_undoable_property("font_family", font.family(), None)
                self.set_undoable_property("font_size", int(font.pointSize()), "update_text")

            self._apply_label_layout_change(_apply, "Change Label Font")
        except Exception:
            pass

    def _change_label_font_color(self) -> None:
        """ラベル文字色を変更する。"""
        try:
            current = QColor(str(getattr(self.config, "font_color", "#FFFFFFFF")))
            c = QColorDialog.getColor(current, self, options=QColorDialog.ShowAlphaChannel)
            if not c.isValid():
                return

            self._apply_label_layout_change(
                lambda: self.set_undoable_property("font_color", c.name(QColor.HexArgb), "update_text"),
                "Change Label Font Color",
            )
        except Exception:
            pass

    def _change_label_bg_color(self) -> None:
        """ラベル背景色を変更する。"""
        try:
            current = QColor(str(getattr(self.config, "background_color", "#00000000")))
            c = QColorDialog.getColor(current, self, options=QColorDialog.ShowAlphaChannel)
            if not c.isValid():
                return

            self._apply_label_layout_change(
                lambda: self.set_undoable_property("background_color", c.name(QColor.HexArgb), "update_text"),
                "Change Label BG Color",
            )
        except Exception:
            pass

    def _change_label_bg_opacity(self) -> None:
        """ラベル背景透明度を変更する（簡易）。"""
        try:
            cur = int(getattr(self.config, "background_opacity", 80))
            v, ok = QInputDialog.getInt(self, tr("title_set_bg_opacity"), tr("label_opacity"), cur, 0, 100)
            if not ok:
                return

            self._apply_label_layout_change(
                lambda: self.set_undoable_property("background_opacity", int(v), "update_text"),
                "Change Label BG Opacity",
            )
        except Exception:
            pass

    def _open_parent_line_menu(self) -> None:
        """親の線の右クリックメニューを開く（導線）。"""
        try:
            if self.connector is None:
                return
            # 線のメニューは線の座標基準なので、ラベル位置を使って表示
            self.connector.show_context_menu(self.connector.mapFromGlobal(self.mapToGlobal(QPoint(0, 0))))
        except Exception:
            pass


class ConnectorLine(QWidget):
    sig_connector_selected = Signal(object)
    sig_connector_deleted = Signal(object)

    def __init__(self, start_window, end_window, parent=None, color=None, width=AppDefaults.CONNECTOR_WIDTH):
        # 親はMainWindow (Overlayのため)
        # しかしConnectorLine自体はQWidgetとして管理される
        # ★修正: Sticky Note Mode (最小化しても消えないように parent=None で独立させる)
        super().__init__(None)  # was parent

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.start_window = start_window
        self.end_window = end_window

        self.line_color = color if color else QColor(100, 200, 255, 180)
        self.line_width = width
        self.pen_style = Qt.SolidLine
        self.arrow_style = ArrowStyle.NONE
        self.arrow_size = 15

        self.is_selected = False

        self.label_window = None

        # MainWindowの参照を取得
        main_window_ref = getattr(start_window, "main_window", None)
        self.main_window = main_window_ref

        # ConnectorLabelの初期化
        # ★重要: 親をmain_windowに設定し、Zオーダーで線より上に来るようにする
        # これにより、ラベルが線の一部としてではなく、独立したウィンドウとして振る舞える
        self.label_window = ConnectorLabel(main_window_ref, self, text="")
        self.label_window.hide()
        self._label_forced_hidden: bool = False

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.update_position()
        self.show()

    def set_selected(self, selected):
        self.is_selected = selected
        self.update()
        # 線が選択されたら、ラベルの選択枠も表示すると分かりやすい
        if self.label_window:
            self.label_window.set_selected(selected)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.sig_connector_selected.emit(self)
            self.set_selected(True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.label_window:
                if self.label_window.isHidden():
                    self.label_window.show()
                self.label_window.edit_text_realtime()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def update_position(self):
        """
        接続線の再計算と描画更新、およびラベル位置の更新を行う。
        """
        if not self.start_window or not self.end_window:
            self.close()
            return

        try:
            # 接続先のウィンドウが無効または非表示の場合の処理
            if not shiboken6.isValid(self.start_window) or not shiboken6.isValid(self.end_window):
                # self.close()  <-- DELETE: この自爆ロジックが原因の可能性大
                return

            # 接続先のウィンドウが「明示的に非表示」にされている場合のみ隠す
            # (isVisible() だと最小化時にも False になり、復帰時の再描画チラつきの原因になる)
            if self.start_window.isHidden() or self.end_window.isHidden():
                self.hide()
                if self.label_window:
                    self.label_window.hide()
                return
        except RuntimeError:
            # self.close() <-- DELETE
            return

        if self.isHidden():
            self.show()

        # ジオメトリ計算 (クリック判定領域の確保)
        p1 = self.start_window.geometry().center()
        p2 = self.end_window.geometry().center()

        margin = 50
        min_x = min(p1.x(), p2.x()) - margin
        min_y = min(p1.y(), p2.y()) - margin
        max_x = max(p1.x(), p2.x()) + margin
        max_y = max(p1.y(), p2.y()) + margin

        self.setGeometry(QRect(min_x, min_y, max_x - min_x, max_y - min_y))

        # --- ラベルの位置更新 ---
        if hasattr(self, "label_window") and self.label_window:
            # ユーザーが明示的に非表示にしているなら、textがあっても出さない
            if bool(getattr(self, "_label_forced_hidden", False)):
                try:
                    self.label_window.hide()
                except Exception:
                    pass
            else:
                # textがある場合のみ表示（従来通り）
                if self.label_window.text:
                    path = self.calculate_path_in_global()
                    if path.elementCount() > 0:
                        mid_point = path.pointAtPercent(0.5)

                        lw = self.label_window.width()
                        lh = self.label_window.height()

                        self.label_window.move(int(mid_point.x() - lw / 2), int(mid_point.y() - lh / 2))
                        self.label_window.show()
                        self.label_window.raise_()
                else:
                    self.label_window.hide()

        self.update_mask()
        self.update()

    def calculate_path_in_global(self):
        center1 = self.start_window.geometry().center()
        center2 = self.end_window.geometry().center()

        p1 = self.get_edge_point(self.start_window, center2)
        p2 = self.get_edge_point(self.end_window, center1)

        path = QPainterPath()
        path.moveTo(p1)

        dx = p2.x() - p1.x()
        ctrl1 = QPointF(p1.x() + dx * 0.5, p1.y())
        ctrl2 = QPointF(p2.x() - dx * 0.5, p2.y())

        path.cubicTo(ctrl1, ctrl2, p2)
        return path

    def get_edge_point(self, window, target_point):
        rect = window.geometry()
        anchor = getattr(window, "anchor_position", AnchorPosition.AUTO)

        if anchor == AnchorPosition.TOP:
            return QPointF(rect.center().x(), rect.top())
        elif anchor == AnchorPosition.BOTTOM:
            return QPointF(rect.center().x(), rect.bottom())
        elif anchor == AnchorPosition.LEFT:
            return QPointF(rect.left(), rect.center().y())
        elif anchor == AnchorPosition.RIGHT:
            return QPointF(rect.right(), rect.center().y())

        center = rect.center()
        dx = target_point.x() - center.x()
        dy = target_point.y() - center.y()
        if dx == 0 and dy == 0:
            return QPointF(center)

        half_w = rect.width() / 2
        half_h = rect.height() / 2
        tx = abs(half_w / dx) if dx != 0 else float("inf")
        ty = abs(half_h / dy) if dy != 0 else float("inf")
        t = min(tx, ty)
        return QPointF(center.x() + dx * t, center.y() + dy * t)

    def update_mask(self):
        self.calculate_path_in_global()  # side-effect only? or unused? Assuming we can call it without assigning

        # 簡易的に再構築
        center1 = self.start_window.geometry().center()
        center2 = self.end_window.geometry().center()
        p1 = self.get_edge_point(self.start_window, center2) - self.pos().toPointF()
        p2 = self.get_edge_point(self.end_window, center1) - self.pos().toPointF()

        path = QPainterPath()
        path.moveTo(p1)
        dx = p2.x() - p1.x()
        path.cubicTo(QPointF(p1.x() + dx * 0.5, p1.y()), QPointF(p2.x() - dx * 0.5, p2.y()), p2)

        stroker = QPainterPathStroker()
        stroker.setWidth(max(20, self.line_width + 15))
        stroker.setCapStyle(Qt.RoundCap)
        stroke_path = stroker.createStroke(path)

        region = QRegion(stroke_path.toFillPolygon().toPolygon())
        self.setMask(region)

    def paintEvent(self, event):
        if not self.start_window or not self.end_window:
            return
        if not shiboken6.isValid(self.start_window) or not shiboken6.isValid(self.end_window):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center1 = self.start_window.geometry().center()
        center2 = self.end_window.geometry().center()
        p1 = self.get_edge_point(self.start_window, center2) - self.pos().toPointF()
        p2 = self.get_edge_point(self.end_window, center1) - self.pos().toPointF()

        path = QPainterPath()
        path.moveTo(p1)
        dx = p2.x() - p1.x()
        path.cubicTo(QPointF(p1.x() + dx * 0.5, p1.y()), QPointF(p2.x() - dx * 0.5, p2.y()), p2)

        if self.is_selected:
            # 追加：MainWindow の選択枠カラーに合わせる（なければ従来の色）
            highlight_color = QColor(0, 255, 255, 100)
            try:
                mw = getattr(self, "main_window", None)
                s = getattr(mw, "overlay_settings", None)
                if s is not None:
                    c = QColor(str(getattr(s, "selection_frame_color", "#C800FFFF")))
                    # 線のハイライトは控えめに（alpha固定で薄め）
                    c.setAlpha(100)
                    highlight_color = c
            except Exception:
                pass

            highlight_pen = QPen(highlight_color)
            highlight_pen.setWidth(self.line_width + 8)
            highlight_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(highlight_pen)
            painter.drawPath(path)

        if self.pen_style == Qt.SolidLine:
            shadow_pen = QPen(QColor(0, 0, 0, 80))
            shadow_pen.setWidth(self.line_width + 4)
            shadow_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(shadow_pen)
            painter.drawPath(path)

        pen = QPen(self.line_color)
        pen.setWidth(self.line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setStyle(self.pen_style)
        painter.setPen(pen)
        painter.drawPath(path)

        if self.arrow_style != ArrowStyle.NONE:
            painter.setBrush(self.line_color)
            painter.setPen(Qt.NoPen)
            if self.arrow_style in [ArrowStyle.START, ArrowStyle.BOTH]:
                p_start = path.pointAtPercent(0.0)
                p_next = path.pointAtPercent(0.05)
                angle = math.atan2(p_start.y() - p_next.y(), p_start.x() - p_next.x())
                self.draw_arrow(painter, p_start, angle)
            if self.arrow_style in [ArrowStyle.END, ArrowStyle.BOTH]:
                p_end = path.pointAtPercent(1.0)
                p_prev = path.pointAtPercent(0.95)
                angle = math.atan2(p_end.y() - p_prev.y(), p_end.x() - p_prev.x())
                self.draw_arrow(painter, p_end, angle)
        elif self.pen_style == Qt.SolidLine:
            painter.setBrush(self.line_color)
            painter.setPen(Qt.NoPen)
            radius = self.line_width
            painter.drawEllipse(p1, radius, radius)
            painter.drawEllipse(p2, radius, radius)

        painter.end()

    def draw_arrow(self, painter, tip_point, angle):
        arrow_size = max(self.arrow_size, self.line_width * 3)
        p1 = tip_point
        p2 = QPointF(
            tip_point.x() - arrow_size * math.cos(angle - math.pi / 6),
            tip_point.y() - arrow_size * math.sin(angle - math.pi / 6),
        )
        p3 = QPointF(
            tip_point.x() - arrow_size * math.cos(angle + math.pi / 6),
            tip_point.y() - arrow_size * math.sin(angle + math.pi / 6),
        )
        painter.drawPolygon(QPolygonF([p1, p2, p3]))

    def show_context_menu(self, pos):
        """コネクタの右クリックメニュー（ContextMenuBuilder版・線種/矢印対応）。"""
        # まず「選択扱い」を試す（失敗してもメニューは必ず出す）
        try:
            try:
                self.set_selected(True)
            except Exception:
                pass

            try:
                self.sig_connector_selected.emit(self)
            except Exception:
                pass
        except Exception:
            pass

        try:
            builder = ContextMenuBuilder(self, self.main_window)

            # -------------------------
            # Label
            # -------------------------
            builder.add_action(
                "menu_add_label",
                lambda checked=False: self.label_window.edit_text_realtime() if self.label_window else None,
            )
            builder.add_action(
                "menu_toggle_label",
                lambda checked=False: self.set_label_visible(bool(checked)),
                checkable=True,
                checked=self.is_label_visible(),
            )

            builder.add_separator()

            # -------------------------
            # Line Appearance (Color/Width/Opacity)
            # -------------------------
            builder.add_action("menu_line_color", self.change_color)
            builder.add_action("menu_line_width", self.open_width_dialog)
            builder.add_action("menu_line_opacity", self.open_opacity_dialog)

            builder.add_separator()

            # -------------------------
            # Line Style (Solid/Dash/Dot)
            # -------------------------
            style_menu = builder.add_submenu("menu_line_style")

            try:
                cur_style = getattr(self, "pen_style", Qt.SolidLine)
            except Exception:
                cur_style = Qt.SolidLine

            styles = [
                ("line_style_solid", Qt.SolidLine),
                ("line_style_dash", Qt.DashLine),
                ("line_style_dot", Qt.DotLine),
            ]

            for key, style in styles:
                builder.add_action(
                    key,
                    lambda checked=False, s=style: self.set_line_style(s),
                    checkable=True,
                    checked=(cur_style == style),
                    parent_menu=style_menu,
                )

            builder.add_separator()

            # -------------------------
            # Arrow Style (None/Start/End/Both)
            # -------------------------
            arrow_menu = builder.add_submenu("menu_arrow_style")

            try:
                cur_arrow = getattr(self, "arrow_style", ArrowStyle.NONE)
            except Exception:
                cur_arrow = ArrowStyle.NONE

            arrows = [
                ("arrow_none", ArrowStyle.NONE),
                ("arrow_start", ArrowStyle.START),
                ("arrow_end", ArrowStyle.END),
                ("arrow_both", ArrowStyle.BOTH),
            ]

            for key, style in arrows:
                builder.add_action(
                    key,
                    lambda checked=False, s=style: self.set_arrow_style(s),
                    checkable=True,
                    checked=(cur_arrow == style),
                    parent_menu=arrow_menu,
                )

            builder.add_separator()

            # -------------------------
            # Delete
            # -------------------------
            builder.add_action("menu_delete_line", lambda checked=False: self.delete_line())

            builder.exec(self.mapToGlobal(pos))

        except Exception:
            pass  # Suppress context menu errors to avoid console noise

    def open_opacity_dialog(self):
        current = int(self.line_color.alpha() / 255 * 100)

        def cb(val):
            self.line_color.setAlpha(int(val / 100 * 255))
            self.update()

        dialog = SliderSpinDialog(tr("title_line_opacity"), tr("label_opacity"), 0, 100, current, cb, self)
        dialog.exec()

    def open_width_dialog(self):
        def cb(val):
            self.line_width = int(val)
            self.update_position()

        dialog = SliderSpinDialog(tr("title_line_width"), tr("label_line_width"), 1, 50, self.line_width, cb, self)
        dialog.exec()

    def set_line_color(self, color: Any) -> None:
        """線色を QColor（alpha込み）として正規化して設定する。

        Args:
            color (Any): QColor または "#RRGGBB"/"#AARRGGBB" 等の文字列
        """
        try:
            if isinstance(color, QColor):
                c = QColor(color)  # コピー（参照共有を避ける）
            else:
                c = QColor(str(color))

            if not c.isValid():
                return

            self.line_color = c
            self.update()
        except Exception:
            pass

    def change_color(self) -> None:
        """カラーダイアログで線色を変更（alpha込みで保持）。"""
        try:
            c = QColorDialog.getColor(self.line_color, self, options=QColorDialog.ShowAlphaChannel)
            if not c.isValid():
                return
            self.set_line_color(c)
        except Exception:
            pass

    def set_line_style(self, style):
        self.pen_style = style
        self.update()

    def set_arrow_style(self, style):
        self.arrow_style = style
        self.update_position()

    def _begin_delete(self) -> bool:
        """削除処理を開始してよいか判定し、二重削除を無害化する。

        Returns:
            bool: これから削除してよい場合 True。既に削除中/削除済みなら False。
        """
        try:
            if bool(getattr(self, "_deleted", False)):
                return False
            self._deleted = True
            return True
        except Exception:
            # ここで落ちるなら安全側で「削除済み扱い」にする
            try:
                self._deleted = True
            except Exception:
                pass
            return False

    def delete_line(self) -> None:
        """コネクタを削除する（WindowManager に委譲）。

        互換:
            - 既存の呼び出し元（右クリック/ConnectorActions 等）から呼ばれてもOK
        """
        try:
            mw = getattr(self, "main_window", None)
            if mw is not None and hasattr(mw, "window_manager"):
                mw.window_manager.delete_connector(self)
                return

            # フォールバック（極めて稀）
            try:
                self.sig_connector_deleted.emit(self)
            except Exception:
                pass

            try:
                self.close()
            except Exception:
                pass

        except Exception:
            try:
                self.sig_connector_deleted.emit(self)
            except Exception:
                pass

    def closeEvent(self, event: Any) -> None:
        """closeEvent は余計な削除制御をしない（WindowManager主導に戻す）。"""
        try:
            event.accept()
        except Exception:
            pass

    def toggle_label_visibility(self) -> None:
        """ラベルを表示/非表示する（線側メニュー用）。

        仕様:
            - text が空なら「編集へ誘導」（空のままだと見えないため）
            - text があるなら hide/show を切替
        """
        try:
            lw = getattr(self, "label_window", None)
            if lw is None:
                return

            text = ""
            try:
                text = str(getattr(lw, "text", "") or "")
            except Exception:
                text = ""

            if not text.strip():
                # 空なら編集へ（表示できない）
                try:
                    if lw.isHidden():
                        lw.show()
                    lw.raise_()
                except Exception:
                    pass

                try:
                    if hasattr(lw, "edit_text_realtime"):
                        lw.edit_text_realtime()
                except Exception:
                    pass

                # 位置更新
                try:
                    self.update_position()
                except Exception:
                    pass
                return

            # textがある：show/hide をトグル
            try:
                if lw.isHidden():
                    lw.show()
                    lw.raise_()
                else:
                    if hasattr(lw, "hide_action"):
                        lw.hide_action()
                    else:
                        lw.hide()
            except Exception:
                pass

            try:
                self.update_position()
            except Exception:
                pass

        except Exception:
            pass

    def is_label_visible(self) -> bool:
        """ラベルが表示状態かどうかを返す（ユーザーの強制非表示も考慮）。

        Returns:
            bool: 表示中なら True。
        """
        try:
            lw = getattr(self, "label_window", None)
            if lw is None:
                return False
            if bool(getattr(self, "_label_forced_hidden", False)):
                return False
            return not lw.isHidden()
        except Exception:
            return False

    def set_label_visible(self, visible: bool) -> None:
        """ラベル表示状態を設定する（線自体は触らない）。

        仕様:
            - visible=False: ラベルだけ hide（テキストは保持）
            - visible=True:
                - テキストが空なら編集へ誘導
                - テキストがあるなら show
            - この状態は update_position() の自動表示より優先される

        Args:
            visible (bool): Trueで表示、Falseで非表示。
        """
        lw = getattr(self, "label_window", None)
        if lw is None:
            return

        try:
            if not visible:
                self._label_forced_hidden = True
                try:
                    if hasattr(lw, "hide_action"):
                        lw.hide_action()
                    else:
                        lw.hide()
                except Exception:
                    pass
                return

            # visible=True
            self._label_forced_hidden = False

            text = ""
            try:
                text = str(getattr(lw, "text", "") or "")
            except Exception:
                text = ""

            # 空なら編集へ誘導（ONにしても見えない問題の回避）
            if not text.strip():
                try:
                    if lw.isHidden():
                        lw.show()
                    lw.raise_()
                except Exception:
                    pass

                try:
                    if hasattr(lw, "edit_text_realtime"):
                        lw.edit_text_realtime()
                except Exception:
                    pass
                return

            # textがあるなら show
            try:
                if lw.isHidden():
                    lw.show()
                lw.raise_()
            except Exception:
                pass

        finally:
            # 表示状態が変わったら位置更新（線は消さない）
            try:
                self.update_position()
            except Exception:
                pass
