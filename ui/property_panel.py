# ui/property_panel.py

import logging
import typing
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFontDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.enums import ArrowStyle
from utils.translator import tr

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class PropertyPanel(QWidget):
    """選択されたオブジェクトのプロパティを表示・編集するためのフローティングパネル。

    TextWindow, ImageWindow, ConnectorLine の属性をリアルタイムで反映・操作します。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """PropertyPanelを初期化します。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。通常はMainWindow。
        """
        super().__init__(parent)
        self.mw = parent  # Main Window reference
        self.setWindowTitle(tr("prop_panel_title"))
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(300, 600)
        self.setObjectName("PropertyPanel")  # For Global Theme Targeting

        self.current_target: Optional[Any] = None

        # メインレイアウト構築
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        # Undo/Redoショートカットの登録
        if parent and hasattr(parent, "undo_action"):
            self.addAction(parent.undo_action)
            self.addAction(parent.redo_action)

        # メンバ変数の初期化
        self._init_property_widgets()
        self.refresh_ui()

    # _setup_stylesheet removed (Global Style System)

    def _init_property_widgets(self) -> None:
        """ウィジェット参照保持用変数を一括初期化します。"""
        self.spin_x = self.spin_y = None
        self.spin_img_scale = self.slider_img_scale = None
        self.spin_img_opacity = self.slider_img_opacity = None
        self.spin_img_rotation = self.slider_img_rotation = None
        self.spin_anim_speed = self.slider_anim_speed = None
        self.btn_text_font = self.spin_text_font_size = None
        self.btn_text_color = None
        self.spin_text_opacity = self.slider_text_opacity = None
        self.btn_bg_color = None
        self.btn_bg_toggle = None  # New
        self.spin_bg_opacity = self.slider_bg_opacity = None

        # Gradient Widgets
        self.btn_text_gradient_toggle = None
        self.btn_edit_text_gradient = None
        self.spin_text_gradient_opacity = self.slider_text_gradient_opacity = None

        self.btn_bg_gradient_toggle = None
        self.btn_edit_bg_gradient = None
        self.spin_bg_gradient_opacity = self.slider_bg_gradient_opacity = None

        self.spin_bg_corner = self.slider_bg_corner = None
        self.btn_shadow_toggle = self.btn_shadow_color = None
        self.spin_shadow_opacity = self.slider_shadow_opacity = None
        self.spin_shadow_blur = self.slider_shadow_blur = None
        self.spin_shadow_offset_x = self.spin_shadow_offset_y = None

        # Gradient Widgets
        self.btn_text_gradient_toggle = None
        self.btn_edit_text_gradient = None
        self.spin_text_gradient_angle = self.slider_text_gradient_angle = None
        self.spin_text_gradient_opacity = self.slider_text_gradient_opacity = None

        self.btn_bg_gradient_toggle = None
        self.btn_edit_bg_gradient = None
        self.spin_bg_gradient_angle = self.slider_bg_gradient_angle = None
        self.spin_bg_gradient_opacity = self.slider_bg_gradient_opacity = None

        # Annotation Widgets
        self.edit_memo = None
        self.edit_hyperlink = None
        self.edit_icon = None

        # Background Outline Widgets
        self.btn_bg_outline_toggle = None
        self.btn_bg_outline_color = None
        self.spin_bg_outline_width = None
        self.spin_bg_outline_opacity = self.slider_bg_outline_opacity = None

        # Signal Connections
        self._current_pos_conn = None

    def set_target(self, target: Any) -> None:
        """編集対象を設定しUIを更新します。

        Args:
            target (Any): TextWindow, ImageWindow, ConnectorLine 等のインスタンス。
        """
        if self.current_target == target:
            if target:
                target.raise_()
            return

        self.current_target = target

        # 以前のシグナル接続を解除
        if self._current_pos_conn:
            try:
                self.disconnect(self._current_pos_conn)
            except Exception:
                pass
            self._current_pos_conn = None

        self.refresh_ui()

        if self.current_target:
            self.current_target.raise_()

            # 新しいシグナル接続 (MindMapNodeの場合)
            if hasattr(self.current_target, "sig_position_changed"):
                # Note: connect returns a Connection object in pure Qt, but in PySide6
                # we usually keep the signal-slot pair to disconnect.
                # However, disconnect() works with passed signal too.
                # Here we use a simpler approach: connect and store the connection if possible,
                # or just disconnect by signal on next set.

                # Using a wrapper to update UI
                self.current_target.sig_position_changed.connect(self._on_target_position_changed)
                # Store for disconnection (logic slightly complex in PySide,
                # easier to just disconnect specific signal if known)

    def _on_target_position_changed(self, pos) -> None:
        """ターゲットの位置変更通知を受け取る。"""
        if self.current_target == self.sender():
            self.update_coordinates()

    def set_target_and_disconnect_old(self, target):
        # Helper if needed, but modifying set_target directly above
        pass

    def refresh_ui(self) -> None:
        """現在のターゲットに合わせてUIを完全に再構築します。"""
        # from ui.mindmap.mindmap_node import MindMapNode
        from windows.connector import ConnectorLabel, ConnectorLine
        from windows.image_window import ImageWindow
        from windows.text_window import TextWindow

        self._init_property_widgets()
        self.clear_layout(self.scroll_layout)

        if self.current_target is None:
            lbl = QLabel(tr("prop_no_selection"))
            lbl.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(lbl)
            return

        # ターゲット毎のビルド分岐
        if isinstance(self.current_target, (TextWindow, ConnectorLabel)):
            self.build_text_window_ui()
        elif isinstance(self.current_target, ImageWindow):
            self.build_image_window_ui()
        elif isinstance(self.current_target, ConnectorLine):
            self.build_connector_ui()
        # elif isinstance(self.current_target, MindMapNode):
        #     self.build_mindmap_node_ui()

        self.scroll_layout.addStretch()

    def clear_layout(self, layout: QVBoxLayout) -> None:
        """レイアウト内の全てのウィジェットを削除します。"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def update_property_values(self) -> None:
        """UIを再構築せずに、数値データのみを最新状態に更新します。"""
        # from ui.mindmap.mindmap_node import MindMapNode
        from windows.connector import ConnectorLabel
        from windows.image_window import ImageWindow
        from windows.text_window import TextWindow

        if not self.current_target:
            return

        self.update_coordinates()

        if isinstance(self.current_target, ImageWindow):
            self._update_image_values()
        elif isinstance(self.current_target, (TextWindow, ConnectorLabel)):
            self._update_text_values()
        # elif isinstance(self.current_target, MindMapNode):
        #     self._update_mindmap_node_values()

    def update_coordinates(self) -> None:
        """座標表示を更新します。"""
        if self.current_target and self.spin_x and self.spin_y:
            self.spin_x.blockSignals(True)
            self.spin_y.blockSignals(True)

            x, y = 0.0, 0.0
            if hasattr(self.current_target, "scenePos"):
                pos = self.current_target.scenePos()
                x, y = pos.x(), pos.y()
            else:
                x = self.current_target.x()
                y = self.current_target.y()

            self.spin_x.setValue(x)
            self.spin_y.setValue(y)

            self.spin_x.blockSignals(False)
            self.spin_y.blockSignals(False)

    def _update_image_values(self) -> None:
        """画像ウィンドウの数値を更新します。"""
        t: Any = self.current_target
        if t is None:
            return

        # percent 表示に合わせて同期（spin/slider は % で持つ）
        try:
            if self.spin_img_scale and self.slider_img_scale:
                p = int(round(float(t.scale_factor) * 100.0))
                self.spin_img_scale.blockSignals(True)
                self.slider_img_scale.blockSignals(True)
                self.spin_img_scale.setValue(p)
                self.slider_img_scale.setValue(p)
                self.spin_img_scale.blockSignals(False)
                self.slider_img_scale.blockSignals(False)
        except Exception:
            pass

        try:
            if self.spin_img_opacity and self.slider_img_opacity:
                p = int(round(float(t.opacity) * 100.0))
                self.spin_img_opacity.blockSignals(True)
                self.slider_img_opacity.blockSignals(True)
                self.spin_img_opacity.setValue(p)
                self.slider_img_opacity.setValue(p)
                self.spin_img_opacity.blockSignals(False)
                self.slider_img_opacity.blockSignals(False)
        except Exception:
            pass

        try:
            if self.spin_img_rotation and self.slider_img_rotation:
                # rotation は従来通り（度）
                self.spin_img_rotation.blockSignals(True)
                self.slider_img_rotation.blockSignals(True)
                self.spin_img_rotation.setValue(float(t.rotation_angle))
                self.slider_img_rotation.setValue(int(float(t.rotation_angle)))
                self.spin_img_rotation.blockSignals(False)
                self.slider_img_rotation.blockSignals(False)
        except Exception:
            pass

        try:
            if self.spin_anim_speed and self.slider_anim_speed:
                p = int(round(float(t.animation_speed_factor) * 100.0))
                self.spin_anim_speed.blockSignals(True)
                self.slider_anim_speed.blockSignals(True)
                self.spin_anim_speed.setValue(p)
                self.slider_anim_speed.setValue(p)
                self.spin_anim_speed.blockSignals(False)
                self.slider_anim_speed.blockSignals(False)
        except Exception:
            pass

    def _open_text_gradient_dialog(self) -> None:
        """テキストグラデーション編集ダイアログを開く。"""
        # Re-use existing gradient dialog
        from ui.dialogs import GradientEditorDialog

        target = self.current_target
        if not target or not hasattr(target, "config"):
            return

        config = target.config
        # Note: GradientEditorDialog takes (gradient, angle)
        # config.text_gradient is List[Tuple[float, str]]
        dialog = GradientEditorDialog(config.text_gradient, config.text_gradient_angle, self)

        if dialog.exec():
            # Apply changes
            # Ideally wrap in macro for undo
            if hasattr(target, "begin_macro"):
                target.begin_macro("Change Text Gradient")
            target.set_undoable_property("text_gradient", dialog.get_gradient())
            target.set_undoable_property("text_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(target, "end_macro"):
                target.end_macro()
            else:
                # Fallback if no macro support (update manually)
                target.update_text()

    def _open_bg_gradient_dialog(self) -> None:
        """背景グラデーション編集ダイアログを開く。"""
        from ui.dialogs import GradientEditorDialog

        target = self.current_target
        if not target or not hasattr(target, "config"):
            return

        config = target.config
        dialog = GradientEditorDialog(config.background_gradient, config.background_gradient_angle, self)

        if dialog.exec():
            if hasattr(target, "begin_macro"):
                target.begin_macro("Change Background Gradient")
            target.set_undoable_property("background_gradient", dialog.get_gradient())
            target.set_undoable_property("background_gradient_angle", dialog.get_angle(), "update_text")
            if hasattr(target, "end_macro"):
                target.end_macro()
            else:
                target.update_text()

    def _update_text_values(self) -> None:
        """テキスト系ウィンドウの数値を更新します。"""
        t = self.current_target
        if self.btn_text_font:
            self.btn_text_font.setText(f"{t.font_family} ({t.font_size}pt)")
        if self.spin_text_font_size:
            self.spin_text_font_size.blockSignals(True)
            self.spin_text_font_size.setValue(int(t.font_size))
            self.spin_text_font_size.blockSignals(False)

        if self.btn_text_color:
            self.update_color_button_style(self.btn_text_color, t.font_color)

        if self.btn_bg_toggle:
            self.btn_bg_toggle.blockSignals(True)
            self.btn_bg_toggle.setChecked(t.background_visible)
            self.btn_bg_toggle.blockSignals(False)

        if self.btn_bg_color:
            self.update_color_button_style(self.btn_bg_color, t.background_color)

        if self.btn_bg_color:
            self.update_color_button_style(self.btn_bg_color, t.background_color)

        # Gradient Sync
        if self.btn_text_gradient_toggle:
            self.btn_text_gradient_toggle.blockSignals(True)
            self.btn_text_gradient_toggle.setChecked(t.text_gradient_enabled)
            self.btn_text_gradient_toggle.blockSignals(False)

        if self.spin_text_gradient_opacity and self.slider_text_gradient_opacity:
            val = t.text_gradient_opacity
            self.spin_text_gradient_opacity.blockSignals(True)
            self.slider_text_gradient_opacity.blockSignals(True)
            self.spin_text_gradient_opacity.setValue(val)
            self.slider_text_gradient_opacity.setValue(val)
            self.spin_text_gradient_opacity.blockSignals(False)
            self.slider_text_gradient_opacity.blockSignals(False)

        if self.btn_bg_gradient_toggle:
            self.btn_bg_gradient_toggle.blockSignals(True)
            self.btn_bg_gradient_toggle.setChecked(t.background_gradient_enabled)
            self.btn_bg_gradient_toggle.blockSignals(False)

        if self.spin_bg_gradient_opacity and self.slider_bg_gradient_opacity:
            val = t.background_gradient_opacity
            self.spin_bg_gradient_opacity.blockSignals(True)
            self.slider_bg_gradient_opacity.blockSignals(True)
            self.spin_bg_gradient_opacity.setValue(val)
            self.slider_bg_gradient_opacity.setValue(val)
            self.spin_bg_gradient_opacity.blockSignals(False)
            self.slider_bg_gradient_opacity.blockSignals(False)

        # スライダー同期
        pairs = [
            (self.spin_text_opacity, self.slider_text_opacity, t.text_opacity, 1),
            (self.spin_bg_opacity, self.slider_bg_opacity, t.background_opacity, 1),
            (self.spin_bg_corner, self.slider_bg_corner, t.background_corner_ratio, 100),
            (self.spin_shadow_opacity, self.slider_shadow_opacity, t.shadow_opacity, 1),
            (self.spin_shadow_blur, self.slider_shadow_blur, t.shadow_blur, 1),
        ]
        for spin, slider, val, scale in pairs:
            if spin and slider:
                spin.blockSignals(True)
                slider.blockSignals(True)
                spin.setValue(val)
                slider.setValue(int(val * scale))
                spin.blockSignals(False)
                slider.blockSignals(False)

        if self.btn_shadow_toggle:
            self.btn_shadow_toggle.blockSignals(True)
            self.btn_shadow_toggle.setChecked(t.shadow_enabled)
            self.btn_shadow_toggle.blockSignals(False)

        if self.btn_shadow_color:
            self.update_color_button_style(self.btn_shadow_color, t.shadow_color)

        if self.spin_shadow_offset_x:
            self.spin_shadow_offset_x.blockSignals(True)
            self.spin_shadow_offset_x.setValue(t.shadow_offset_x)
            self.spin_shadow_offset_x.blockSignals(False)

        if self.spin_shadow_offset_y:
            self.spin_shadow_offset_y.blockSignals(True)
            self.spin_shadow_offset_y.setValue(t.shadow_offset_y)
            self.spin_shadow_offset_y.blockSignals(False)

        for i in range(1, 4):
            self._update_outline_values(i, t)

        self._update_bg_outline_values(t)

    def _update_outline_values(self, index: int, target: Any) -> None:
        """縁取り設定を同期します。"""
        prefix = "" if index == 1 else "second_" if index == 2 else "third_"
        btn_toggle = getattr(self, f"btn_outline_{index}_toggle", None)
        btn_color = getattr(self, f"btn_outline_{index}_color", None)
        spin_width = getattr(self, f"spin_outline_{index}_width", None)
        spin_opacity = getattr(self, f"spin_outline_{index}_opacity", None)
        slider_opacity = getattr(self, f"slider_outline_{index}_opacity", None)
        spin_blur = getattr(self, f"spin_outline_{index}_blur", None)
        slider_blur = getattr(self, f"slider_outline_{index}_blur", None)

        if btn_toggle:
            btn_toggle.blockSignals(True)
            btn_toggle.setChecked(getattr(target, f"{prefix}outline_enabled"))
            btn_toggle.blockSignals(False)
        if btn_color:
            self.update_color_button_style(btn_color, getattr(target, f"{prefix}outline_color"))
        if spin_width:
            spin_width.blockSignals(True)
            spin_width.setValue(getattr(target, f"{prefix}outline_width"))
            spin_width.blockSignals(False)
        if spin_opacity and slider_opacity:
            val = getattr(target, f"{prefix}outline_opacity")
            spin_opacity.blockSignals(True)
            slider_opacity.blockSignals(True)
            spin_opacity.setValue(val)
            slider_opacity.setValue(val)
            spin_opacity.blockSignals(False)
            slider_opacity.blockSignals(False)
        if spin_blur and slider_blur:
            val = getattr(target, f"{prefix}outline_blur")
            spin_blur.blockSignals(True)
            slider_blur.blockSignals(True)
            spin_blur.setValue(val)
            slider_blur.setValue(val)
            spin_blur.blockSignals(False)
            spin_blur.blockSignals(False)
            slider_blur.blockSignals(False)

    def _update_bg_outline_values(self, target: Any) -> None:
        """背景枠線設定を同期します。"""
        if self.btn_bg_outline_toggle:
            self.btn_bg_outline_toggle.blockSignals(True)
            self.btn_bg_outline_toggle.setChecked(target.background_outline_enabled)
            self.btn_bg_outline_toggle.blockSignals(False)

        if self.btn_bg_outline_color:
            self.update_color_button_style(self.btn_bg_outline_color, target.background_outline_color)

        if self.spin_bg_outline_width:
            self.spin_bg_outline_width.blockSignals(True)
            self.spin_bg_outline_width.setValue(target.background_outline_width_ratio)
            self.spin_bg_outline_width.blockSignals(False)

        if self.spin_bg_outline_opacity and self.slider_bg_outline_opacity:
            val = target.background_outline_opacity
            self.spin_bg_outline_opacity.blockSignals(True)
            self.slider_bg_outline_opacity.blockSignals(True)
            self.spin_bg_outline_opacity.setValue(val)
            self.slider_bg_outline_opacity.setValue(val)
            self.spin_bg_outline_opacity.blockSignals(False)
            self.slider_bg_outline_opacity.blockSignals(False)

    # --- UI Helper Methods ---

    def create_group(self, title: str) -> QFormLayout:
        group = QGroupBox(title)
        layout = QFormLayout()
        group.setLayout(layout)
        self.scroll_layout.addWidget(group)
        return layout

    def add_spinbox(
        self,
        layout: QFormLayout,
        label: str,
        value: float,
        min_v: float,
        max_v: float,
        step: float,
        callback: Callable,
        is_float: bool = False,
    ) -> Union[QSpinBox, QDoubleSpinBox]:
        spin = QDoubleSpinBox() if is_float else QSpinBox()
        if is_float:
            spin.setDecimals(2)
        spin.setRange(min_v, max_v)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.valueChanged.connect(callback)
        layout.addRow(label, spin)
        return spin

    def add_slider_spin(
        self,
        layout: QFormLayout,
        label: str,
        value: float,
        min_v: float,
        max_v: float,
        commit_cb: Callable[[float], None],
        preview_cb: Optional[Callable[[float], None]] = None,
        unit_scale: float = 1.0,
    ) -> Tuple[QDoubleSpinBox, QSlider]:
        """スライダー+スピンの組を追加する（Undo爆発防止版）。

        ルール:
            - スライダードラッグ中：preview_cb（Undoなし）
            - スライダーrelease：commit_cb（Undoあり）
            - スピン変更：commit_cb（Undoあり）

        Args:
            layout (QFormLayout): 追加先レイアウト。
            label (str): ラベル。
            value (float): 初期値（内部値）。
            min_v (float): 最小。
            max_v (float): 最大。
            commit_cb (Callable[[float], None]): 確定反映。
            preview_cb (Optional[Callable[[float], None]]): プレビュー反映。
            unit_scale (float): slider int <-> value float の倍率。

        Returns:
            Tuple[QDoubleSpinBox, QSlider]: (spin, slider)
        """
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        spin = QDoubleSpinBox()
        spin.setRange(float(min_v), float(max_v))
        spin.setValue(float(value))
        spin.setSingleStep(1.0 if unit_scale == 1.0 else 0.1)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_v * unit_scale), int(max_v * unit_scale))
        slider.setValue(int(value * unit_scale))

        state: dict[str, bool] = {"is_dragging": False}

        def on_slider_pressed() -> None:
            state["is_dragging"] = True

        def on_slider_released() -> None:
            state["is_dragging"] = False
            v: float = float(slider.value()) / float(unit_scale)
            commit_cb(v)

        def on_slider_changed(val: int) -> None:
            real_val: float = float(val) / float(unit_scale)
            with QSignalBlocker(spin):
                spin.setValue(real_val)

            if state["is_dragging"]:
                if preview_cb:
                    preview_cb(real_val)
            else:
                # プログラム変更時は commit しない（release/スピンで確定）
                pass

        def on_spin_changed(val: float) -> None:
            v: float = float(val)
            with QSignalBlocker(slider):
                slider.setValue(int(v * unit_scale))
            commit_cb(v)

        slider.sliderPressed.connect(on_slider_pressed)
        slider.sliderReleased.connect(on_slider_released)
        slider.valueChanged.connect(on_slider_changed)
        spin.valueChanged.connect(on_spin_changed)

        h_layout.addWidget(slider)
        h_layout.addWidget(spin)
        layout.addRow(label, container)
        return spin, slider

    def add_slider_spin_percent(
        self,
        layout: QFormLayout,
        label: str,
        value_internal: float,
        min_percent: int,
        max_percent: int,
        commit_cb: Callable[[float], None],
        preview_cb: Optional[Callable[[float], None]] = None,
        scale: float = 100.0,
    ) -> Tuple[QSpinBox, QSlider]:
        """割合（%）表示のスライダー+スピンを追加する（Undo爆発防止版）。

        ルール:
            - スライダードラッグ中：preview_cb を呼ぶ（Undoなし）
            - スライダーを離した時：commit_cb を1回だけ呼ぶ（Undoあり）
            - スピン変更：commit_cb を呼ぶ（Undoあり）

        Args:
            layout (QFormLayout): 追加先レイアウト。
            label (str): 行のラベル。
            value_internal (float): 現在値（内部値）。
            min_percent (int): 最小%。
            max_percent (int): 最大%。
            commit_cb (Callable[[float], None]): 確定反映（内部値）。
            preview_cb (Optional[Callable[[float], None]]): プレビュー反映（内部値）。
            scale (float): 内部値→%の倍率。

        Returns:
            Tuple[QSpinBox, QSlider]: (spinbox, slider)
        """
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        spin = QSpinBox()
        spin.setRange(int(min_percent), int(max_percent))
        spin.setSingleStep(1)
        spin.setSuffix("%")

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_percent), int(max_percent))
        slider.setSingleStep(1)
        slider.setPageStep(1)

        cur_percent: int = int(round(float(value_internal) * float(scale)))
        cur_percent = max(int(min_percent), min(int(max_percent), cur_percent))
        spin.setValue(cur_percent)
        slider.setValue(cur_percent)

        state: dict[str, bool] = {"is_dragging": False}

        def _to_internal(pct: int) -> float:
            return float(pct) / float(scale)

        def on_slider_pressed() -> None:
            state["is_dragging"] = True

        def on_slider_released() -> None:
            state["is_dragging"] = False
            v_internal: float = _to_internal(int(slider.value()))
            commit_cb(v_internal)

        def on_slider_changed(val: int) -> None:
            with QSignalBlocker(spin):
                spin.setValue(int(val))

            v_internal: float = _to_internal(int(val))
            if state["is_dragging"]:
                if preview_cb:
                    preview_cb(v_internal)
            else:
                # プログラム的変更時は commit しない（Undo爆発防止）
                # ここは release/スピン入力で確定する
                pass

        def on_spin_changed(val: int) -> None:
            with QSignalBlocker(slider):
                slider.setValue(int(val))
            v_internal: float = _to_internal(int(val))
            commit_cb(v_internal)

        slider.sliderPressed.connect(on_slider_pressed)
        slider.sliderReleased.connect(on_slider_released)
        slider.valueChanged.connect(on_slider_changed)
        spin.valueChanged.connect(on_spin_changed)

        h_layout.addWidget(slider)
        h_layout.addWidget(spin)
        layout.addRow(label, container)
        return spin, slider

    def add_color_button(
        self, layout: QFormLayout, label: str, current_color: QColor, callback: Callable
    ) -> QPushButton:
        btn = QPushButton()
        btn.setFixedHeight(24)
        self.update_color_button_style(btn, current_color)

        def on_click():
            color = QColorDialog.getColor(current_color, self, label, QColorDialog.ShowAlphaChannel)
            if color.isValid():
                self.update_color_button_style(btn, color)
                callback(color)

        btn.clicked.connect(on_click)
        layout.addRow(label, btn)
        return btn

    def _normalize_color_to_hexargb(self, color: Union[QColor, str]) -> str:
        """色を #AARRGGBB 形式へ正規化する。

        Args:
            color (Union[QColor, str]): QColor または文字列。

        Returns:
            str: #AARRGGBB（不正なら #FFFFFFFF）
        """
        try:
            if isinstance(color, QColor):
                if color.isValid():
                    return color.name(QColor.HexArgb)
                return "#FFFFFFFF"

            c = QColor(str(color))
            if c.isValid():
                return c.name(QColor.HexArgb)
        except Exception:
            pass

        return "#FFFFFFFF"

    def update_color_button_style(self, btn: QPushButton, color: Union[QColor, str]) -> None:
        if isinstance(color, str):
            c_str = color
            qcolor = QColor(color)
        else:
            c_str = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
            qcolor = color

        lum = qcolor.red() * 0.299 + qcolor.green() * 0.587 + qcolor.blue() * 0.114
        text_color = "white" if lum < 128 else "black"
        btn.setStyleSheet(f"background-color: {c_str}; color: {text_color}; border: 1px solid #555;")
        btn.setText(tr("prop_color_selector"))

    def add_combo(
        self, layout: QFormLayout, label: str, current_val: Any, options: list, callback: Callable
    ) -> QComboBox:
        combo = QComboBox()
        for text, data in options:
            combo.addItem(text, data)
            if data == current_val:
                combo.setCurrentIndex(combo.count() - 1)
        combo.currentIndexChanged.connect(lambda idx: callback(combo.itemData(idx)))
        layout.addRow(label, combo)
        return combo

    def add_text_edit(self, layout: QFormLayout, label: str, current_text: str, callback: Callable) -> QLineEdit:
        line_edit = QLineEdit(current_text)
        line_edit.textChanged.connect(callback)
        layout.addRow(label, line_edit)
        return line_edit

    def add_action_button(self, layout: QFormLayout, label: str, callback: Callable) -> QPushButton:
        btn = QPushButton(label)
        btn.clicked.connect(callback)
        layout.addRow("", btn)
        return btn

    # --- Section Builders ---

    def build_common_ui(self, target: Any) -> None:
        """全ウィンドウ共通のトランスフォーム設定。"""
        layout = self.create_group(tr("prop_grp_transform"))
        self.spin_x = self.add_spinbox(
            layout, tr("prop_x"), target.x(), -9999, 9999, 1, lambda v: target.move(v, target.y())
        )
        self.spin_y = self.add_spinbox(
            layout, tr("prop_y"), target.y(), -9999, 9999, 1, lambda v: target.move(target.x(), v)
        )
        self.add_action_button(layout, tr("btn_toggle_front"), target.toggle_frontmost)

    def build_text_window_ui(self) -> None:
        """テキストウィンドウ用のUI構築。"""
        from windows.connector import ConnectorLabel

        target = self.current_target

        if not isinstance(target, ConnectorLabel):
            self.build_common_ui(target)
        else:
            layout = self.create_group(tr("prop_grp_transform"))
            layout.addRow(QLabel(tr("prop_pos_auto_linked")))
            self.add_action_button(layout, tr("btn_toggle_front"), target.toggle_frontmost)

        # テキストスタイル
        t_layout = self.create_group(tr("prop_grp_text"))
        self.btn_text_font = QPushButton(f"{target.font_family} ({target.font_size}pt)")

        def change_font():
            # PySide6 の QFontDialog.getFont は (ok, QFont) を返す（環境により異なる場合があるがエラーログより判断）
            ok, font = QFontDialog.getFont(QFont(target.font_family, int(target.font_size)), self)
            if ok:
                try:
                    target.set_undoable_property("font_family", font.family())
                    target.set_undoable_property("font_size", font.pointSize())
                    target.update_text()
                except Exception as e:
                    import traceback

                    logger.error(f"Failed to change font: {e}\n{traceback.format_exc()}")
                    QMessageBox.warning(self, tr("msg_error"), f"Font change failed: {e}")

        self.btn_text_font.clicked.connect(change_font)
        t_layout.addRow(tr("prop_font_selector"), typing.cast(QWidget, self.btn_text_font))

        self.spin_text_font_size = self.add_spinbox(
            t_layout,
            "Size:",
            int(target.font_size),
            1,
            500,
            1,
            lambda v: target.set_undoable_property("font_size", v, "update_text"),
        )
        t_layout.addRow(tr("prop_font_selector"), typing.cast(QWidget, self.btn_text_font))

        self.spin_text_font_size = self.add_spinbox(
            t_layout,
            "Size:",
            int(target.font_size),
            1,
            500,
            1,
            lambda v: target.set_undoable_property("font_size", v, "update_text"),
        )
        self.btn_text_color = self.add_color_button(
            t_layout,
            tr("prop_color"),
            target.font_color,
            lambda v: target.set_undoable_property("font_color", self._normalize_color_to_hexargb(v), "update_text"),
        )

        commit, prev = self._make_callbacks(target, "text_opacity", "update_text", True)
        self.spin_text_opacity, self.slider_text_opacity = self.add_slider_spin(
            t_layout, tr("label_opacity"), target.text_opacity, 0, 100, commit, prev
        )

        # --- Text Gradient ---
        self.btn_text_gradient_toggle = QPushButton(tr("menu_toggle_text_gradient"))
        self.btn_text_gradient_toggle.setCheckable(True)
        self.btn_text_gradient_toggle.setChecked(target.text_gradient_enabled)
        self.btn_text_gradient_toggle.clicked.connect(
            lambda c: target.set_undoable_property("text_gradient_enabled", c, "update_text")
        )
        t_layout.addRow("", typing.cast(QWidget, self.btn_text_gradient_toggle))

        self.btn_edit_text_gradient = QPushButton("🎨 " + tr("menu_edit_text_gradient"))
        self.btn_edit_text_gradient.clicked.connect(self._open_text_gradient_dialog)
        t_layout.addRow("", typing.cast(QWidget, self.btn_edit_text_gradient))

        commit, prev = self._make_callbacks(target, "text_gradient_opacity", "update_text", True)
        self.spin_text_gradient_opacity, self.slider_text_gradient_opacity = self.add_slider_spin(
            t_layout, tr("menu_set_text_gradient_opacity"), target.text_gradient_opacity, 0, 100, commit, prev
        )

        # Archetype Save Button for Text
        btn_save_text_def = QPushButton("💾 " + tr("btn_save_as_default"))
        btn_save_text_def.setToolTip("現在のテキストスタイルをデフォルトに設定")
        if self.mw and hasattr(self.mw, "main_controller"):
            btn_save_text_def.clicked.connect(self.mw.main_controller.txt_actions.save_as_default)
        t_layout.addRow("", typing.cast(QWidget, btn_save_text_def))

        # 背景
        bg_layout = self.create_group(tr("menu_bg_settings"))

        # visibility toggle
        self.btn_bg_toggle = QPushButton(tr("menu_toggle_background"))
        self.btn_bg_toggle.setCheckable(True)
        self.btn_bg_toggle.setChecked(target.background_visible)
        self.btn_bg_toggle.clicked.connect(
            lambda c: target.set_undoable_property("background_visible", c, "update_text")
        )
        bg_layout.addRow("", typing.cast(QWidget, self.btn_bg_toggle))

        self.btn_bg_color = self.add_color_button(
            bg_layout,
            tr("prop_bg_color"),
            target.background_color,
            lambda v: target.set_undoable_property(
                "background_color", self._normalize_color_to_hexargb(v), "update_text"
            ),
        )
        commit, prev = self._make_callbacks(target, "background_opacity", "update_text", True)
        self.spin_bg_opacity, self.slider_bg_opacity = self.add_slider_spin(
            bg_layout, tr("label_opacity"), target.background_opacity, 0, 100, commit, prev
        )

        # --- Background Gradient ---
        self.btn_bg_gradient_toggle = QPushButton(tr("menu_toggle_bg_gradient"))
        self.btn_bg_gradient_toggle.setCheckable(True)
        self.btn_bg_gradient_toggle.setChecked(target.background_gradient_enabled)
        self.btn_bg_gradient_toggle.clicked.connect(
            lambda c: target.set_undoable_property("background_gradient_enabled", c, "update_text")
        )
        bg_layout.addRow("", typing.cast(QWidget, self.btn_bg_gradient_toggle))

        self.btn_edit_bg_gradient = QPushButton("🎨 " + tr("menu_edit_bg_gradient"))
        self.btn_edit_bg_gradient.clicked.connect(self._open_bg_gradient_dialog)
        bg_layout.addRow("", typing.cast(QWidget, self.btn_edit_bg_gradient))

        commit, prev = self._make_callbacks(target, "background_gradient_opacity", "update_text", True)
        self.spin_bg_gradient_opacity, self.slider_bg_gradient_opacity = self.add_slider_spin(
            bg_layout, tr("menu_set_bg_gradient_opacity"), target.background_gradient_opacity, 0, 100, commit, prev
        )

        commit, prev = self._make_callbacks(target, "background_corner_ratio", "update_text", False)
        self.spin_bg_corner, self.slider_bg_corner = self.add_slider_spin(
            bg_layout, tr("label_ratio"), target.background_corner_ratio, 0.0, 2.0, commit, prev, 100.0
        )

        # Archetype Save Button for Background
        btn_save_bg_def = QPushButton("💾 " + tr("btn_save_as_default"))
        btn_save_bg_def.setToolTip("現在のバックスタイルをデフォルトに設定")
        if self.mw and hasattr(self.mw, "main_controller"):
            btn_save_bg_def.clicked.connect(self.mw.main_controller.txt_actions.save_as_default)
        bg_layout.addRow("", typing.cast(QWidget, btn_save_bg_def))

        # 背景枠線 (Legacy Feature Restoration)
        self.add_bg_outline_settings(target)

        for i in range(1, 4):
            self.add_outline_settings(target, i)

        # 影
        sh_layout = self.create_group(tr("prop_grp_shadow"))
        self.btn_shadow_toggle = QPushButton(tr("menu_toggle_shadow"))
        self.btn_shadow_toggle.setCheckable(True)
        self.btn_shadow_toggle.setChecked(target.shadow_enabled)
        self.btn_shadow_toggle.clicked.connect(
            lambda c: target.set_undoable_property("shadow_enabled", c, "update_text")
        )
        sh_layout.addRow("", typing.cast(QWidget, self.btn_shadow_toggle))
        self.btn_shadow_color = self.add_color_button(
            sh_layout,
            tr("prop_color"),
            target.shadow_color,
            lambda v: target.set_undoable_property("shadow_color", self._normalize_color_to_hexargb(v), "update_text"),
        )
        commit, prev = self._make_callbacks(target, "shadow_opacity", "update_text", True)
        self.spin_shadow_opacity, self.slider_shadow_opacity = self.add_slider_spin(
            sh_layout, tr("label_opacity"), target.shadow_opacity, 0, 100, commit, prev
        )
        commit, prev = self._make_callbacks(target, "shadow_blur", "update_text", True)
        self.spin_shadow_blur, self.slider_shadow_blur = self.add_slider_spin(
            sh_layout, tr("label_blur"), target.shadow_blur, 0, 100, commit, prev
        )
        self.spin_shadow_offset_x = self.add_spinbox(
            sh_layout,
            tr("label_shadow_offset_x"),
            target.shadow_offset_x,
            -10.0,
            10.0,
            0.1,
            lambda v: target.set_undoable_property("shadow_offset_x", v, "update_text"),
            True,
        )
        self.spin_shadow_offset_y = self.add_spinbox(
            sh_layout,
            tr("label_shadow_offset_y"),
            target.shadow_offset_y,
            -10.0,
            10.0,
            0.1,
            lambda v: target.set_undoable_property("shadow_offset_y", v, "update_text"),
            True,
        )

    def add_outline_settings(self, target: Any, index: int) -> None:
        """縁取り設定セクションを追加します。"""
        prefix = "" if index == 1 else "second_" if index == 2 else "third_"
        layout = self.create_group(f"{tr('prop_grp_outline')} ({index})")

        toggle = QPushButton("Enable")
        toggle.setCheckable(True)
        toggle.setChecked(getattr(target, f"{prefix}outline_enabled"))
        toggle.clicked.connect(lambda c: target.set_undoable_property(f"{prefix}outline_enabled", c, "update_text"))
        layout.addRow("", toggle)
        setattr(self, f"btn_outline_{index}_toggle", toggle)

        btn_c = self.add_color_button(
            layout,
            tr("prop_color"),
            getattr(target, f"{prefix}outline_color"),
            lambda v: target.set_undoable_property(
                f"{prefix}outline_color",
                self._normalize_color_to_hexargb(v),
                "update_text",
            ),
        )
        setattr(self, f"btn_outline_{index}_color", btn_c)

        spin_w = self.add_spinbox(
            layout,
            tr("label_width"),
            getattr(target, f"{prefix}outline_width"),
            0.0,
            100.0,
            0.5,
            lambda v: target.set_undoable_property(f"{prefix}outline_width", v, "update_text"),
            True,
        )
        setattr(self, f"spin_outline_{index}_width", spin_w)

        commit, prev = self._make_callbacks(target, f"{prefix}outline_opacity", "update_text", True)
        s_op, sl_op = self.add_slider_spin(
            layout, tr("label_opacity"), getattr(target, f"{prefix}outline_opacity"), 0, 100, commit, prev
        )
        setattr(self, f"spin_outline_{index}_opacity", s_op)
        setattr(self, f"slider_outline_{index}_opacity", sl_op)

        commit, prev = self._make_callbacks(target, f"{prefix}outline_blur", "update_text", True)
        s_bl, sl_bl = self.add_slider_spin(
            layout, tr("label_blur"), getattr(target, f"{prefix}outline_blur"), 0, 100, commit, prev
        )
        setattr(self, f"spin_outline_{index}_blur", s_bl)
        setattr(self, f"slider_outline_{index}_blur", sl_bl)

    def add_bg_outline_settings(self, target: Any) -> None:
        """背景枠線設定セクションを追加します。"""
        layout = self.create_group(tr("menu_toggle_bg_outline"))

        # Toggle
        toggle = QPushButton("Enable")
        toggle.setCheckable(True)
        toggle.setChecked(target.background_outline_enabled)
        toggle.clicked.connect(lambda c: target.set_undoable_property("background_outline_enabled", c, "update_text"))
        layout.addRow("", toggle)
        self.btn_bg_outline_toggle = toggle

        # Color
        self.btn_bg_outline_color = self.add_color_button(
            layout,
            tr("prop_color"),
            target.background_outline_color,
            lambda v: target.set_undoable_property(
                "background_outline_color", self._normalize_color_to_hexargb(v), "update_text"
            ),
        )

        # Width Ratio
        self.spin_bg_outline_width = self.add_spinbox(
            layout,
            tr("label_bg_outline_width"),
            target.background_outline_width_ratio,
            0.0,
            1.0,
            0.01,
            lambda v: target.set_undoable_property("background_outline_width_ratio", v, "update_text"),
            True,
        )

        # Opacity
        commit, prev = self._make_callbacks(target, "background_outline_opacity", "update_text", True)
        self.spin_bg_outline_opacity, self.slider_bg_outline_opacity = self.add_slider_spin(
            layout, tr("label_opacity"), target.background_outline_opacity, 0, 100, commit, prev
        )

    def build_image_window_ui(self) -> None:
        """画像ウィンドウ用のUI構築。"""
        target = self.current_target
        self.build_common_ui(target)
        layout = self.create_group(tr("prop_grp_appearance"))

        commit, prev = self._make_callbacks(target, "scale_factor", "update_image", False)
        self.spin_img_scale, self.slider_img_scale = self.add_slider_spin_percent(
            layout,
            tr("btn_img_selected_size_pct")
            if tr("btn_img_selected_size_pct") != "btn_img_selected_size_pct"
            else "Size:",
            target.scale_factor,
            1,
            500,
            commit,
            prev,
            scale=100.0,
        )

        commit, prev = self._make_callbacks(target, "opacity", "update_image", False)
        self.spin_img_opacity, self.slider_img_opacity = self.add_slider_spin_percent(
            layout,
            tr("label_opacity"),
            target.opacity,
            0,
            100,
            commit,
            prev,
            scale=100.0,
        )

        commit, prev = self._make_callbacks(target, "rotation_angle", "update_image", False)
        self.spin_img_rotation, self.slider_img_rotation = self.add_slider_spin(
            layout, tr("label_rotation"), target.rotation_angle, 0, 360, commit, prev
        )

        f_layout = QHBoxLayout()
        for axis in ["horizontal", "vertical"]:
            btn = QPushButton(tr(f"menu_flip_{axis[0]}"))
            btn.setCheckable(True)
            btn.setChecked(getattr(target, f"flip_{axis}", False))
            btn.clicked.connect(lambda c, a=axis: target.set_undoable_property(f"flip_{a}", c, "update_image"))
            f_layout.addWidget(btn)
        layout.addRow("Flip:", f_layout)

        a_layout = self.create_group(tr("menu_anim_setting_image"))
        commit, prev = self._make_callbacks(target, "animation_speed_factor", "_update_animation_timer", False)
        self.spin_anim_speed, self.slider_anim_speed = self.add_slider_spin_percent(
            a_layout,
            tr("title_anim_speed"),
            target.animation_speed_factor,
            0,
            500,
            commit,
            prev,
            scale=100.0,
        )
        self.add_action_button(a_layout, tr("menu_reset_gif_apng_playback_speed"), target.reset_animation_speed)

    def build_connector_ui(self) -> None:
        """接続線用のUI構築。"""
        target = self.current_target
        layout = self.create_group(tr("prop_grp_connection"))

        self.add_color_button(
            layout, tr("prop_color"), target.line_color, lambda v: setattr(target, "line_color", v) or target.update()
        )
        self.add_spinbox(
            layout,
            tr("label_width"),
            target.line_width,
            1,
            50,
            1,
            lambda v: setattr(target, "line_width", v) or target.update_position(),
        )

        styles = [
            (tr("line_style_solid"), Qt.SolidLine),
            (tr("line_style_dash"), Qt.DashLine),
            (tr("line_style_dot"), Qt.DotLine),
        ]
        self.add_combo(layout, tr("menu_line_style"), target.pen_style, styles, lambda v: target.set_line_style(v))

        arrows = [
            (tr("arrow_none"), ArrowStyle.NONE),
            (tr("arrow_end"), ArrowStyle.END),
            (tr("arrow_start"), ArrowStyle.START),
            (tr("arrow_both"), ArrowStyle.BOTH),
        ]
        self.add_combo(layout, tr("prop_arrow"), target.arrow_style, arrows, lambda v: target.set_arrow_style(v))

        text = target.label_window.text if hasattr(target, "label_window") and target.label_window else ""
        self.add_text_edit(
            layout,
            tr("prop_label_text"),
            text,
            lambda t: (
                target.label_window.set_undoable_property("text", t, "update_text") if target.label_window else None
            ),
        )

        if hasattr(target, "label_window") and target.label_window:
            btn = QPushButton(tr("btn_select_label_style"))
            btn.setStyleSheet("background-color: #555; color: white; margin-top: 5px;")
            btn.clicked.connect(lambda: self.set_target(target.label_window))
            layout.addRow("", btn)

        del_btn = QPushButton(tr("menu_delete_line"))
        del_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; margin-top: 10px;")
        del_btn.clicked.connect(lambda: target.delete_line() or self.set_target(None))
        layout.addRow("", del_btn)

    def _make_callbacks(
        self, target: Any, prop: str, method: Optional[str] = None, is_int: bool = False
    ) -> Tuple[Callable, Callable]:
        """Undo爆発防止用のコールバックペア（確定時/プレビュー時）を生成します。"""

        def commit(val):
            v = int(val) if is_int else val
            target.set_undoable_property(prop, v, method)

        def preview(val):
            v = int(val) if is_int else val
            setattr(target, prop, v)
            if method and hasattr(target, method):
                getattr(target, method)()

        return commit, preview

    def refresh_ui_text(self) -> None:
        """言語切り替え時にUIテキストを即座に更新します。"""
        self.setWindowTitle(tr("prop_panel_title"))
        # レイアウトを再構築することで全ラベルの翻訳を反映
        self.refresh_ui()

    def closeEvent(self, event: Any) -> None:
        """×で閉じられた場合に、MainWindow側のトグル状態もOFFへ同期する。

        Args:
            event (Any): close event
        """
        try:
            parent = self.parent()
            if parent is not None and hasattr(parent, "is_property_panel_active"):
                try:
                    parent.is_property_panel_active = False
                except Exception:
                    pass

                # トグルボタン群もOFFへ
                for attr in ["btn_toggle_prop", "btn_toggle_prop_image", "btn_toggle_prop_text"]:
                    if hasattr(parent, attr):
                        btn = getattr(parent, attr)
                        try:
                            btn.blockSignals(True)
                            btn.setChecked(False)
                        finally:
                            btn.blockSignals(False)

                # 見た目更新
                if hasattr(parent, "update_prop_button_style"):
                    parent.update_prop_button_style()
        except Exception:
            pass

        event.accept()

    # MindMap legacy code removed


# MindMap update methods removed for V1.0
