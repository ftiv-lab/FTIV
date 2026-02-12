# ui/property_panel.py

import logging
import typing
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union, cast

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from models.enums import ArrowStyle
from ui.dialogs import DatePickerDialog
from ui.widgets import CollapsibleBox
from utils.due_date import display_due_iso, is_valid_timezone, normalize_due_input_allow_empty, normalize_due_time
from utils.font_dialog import choose_font
from utils.translator import tr

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class PropertyPanel(QWidget):
    """選択されたオブジェクトのプロパティを表示・編集するためのフローティングパネル。

    TextWindow, ImageWindow, ConnectorLine の属性をリアルタイムで反映・操作します。
    """

    def __init__(self, parent: Optional[QWidget] = None, main_window: Optional[QWidget] = None) -> None:
        """PropertyPanelを初期化します。

        Args:
            parent (Optional[QWidget]): Qt親ウィジェット。独立表示時は None。
            main_window (Optional[QWidget]): MainWindow参照（状態同期用）。
        """
        super().__init__(parent)
        self.mw = main_window if main_window is not None else parent
        self.setWindowTitle(tr("prop_panel_title"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(260, 600)  # Phase 5: Slim default
        self.setObjectName("PropertyPanel")  # For Global Theme Targeting

        self.current_target: Optional[Any] = None

        # メインレイアウト構築
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Phase 5: No horiz scroll
        self.main_layout.addWidget(self.scroll_area)

        # Undo/Redoショートカットの登録
        if self.mw and hasattr(self.mw, "undo_action"):
            self.addAction(self.mw.undo_action)
            self.addAction(self.mw.redo_action)

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
        self.btn_task_mode = None
        self.lbl_editing_target = None
        self.btn_text_orientation = None
        self.btn_text_style_more = None
        self.lbl_task_progress = None
        self.btn_complete_all = None
        self.btn_uncomplete_all = None
        self.edit_note_title = None
        self.edit_note_tags = None
        self.edit_note_due_at = None
        self.cmb_note_due_precision = None
        self.edit_note_due_time = None
        self.edit_note_due_timezone = None
        self.btn_pick_note_due_at = None
        self.btn_due_today = None
        self.btn_due_tomorrow = None
        self.btn_due_next_week = None
        self.btn_due_clear = None
        self.btn_note_star = None
        self.btn_note_archived = None
        self.btn_apply_note_meta = None
        self._section_boxes: dict[str, CollapsibleBox] = {}
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

    def _load_property_panel_section_state(self, key: str, default: bool) -> bool:
        normalized = str(key or "").strip().lower()
        if not normalized:
            return bool(default)
        settings = getattr(self.mw, "app_settings", None)
        raw = getattr(settings, "property_panel_section_state", {}) if settings is not None else {}
        if not isinstance(raw, dict):
            return bool(default)
        if normalized not in raw:
            return bool(default)
        return bool(raw.get(normalized))

    def _save_property_panel_section_state(self, key: str, checked: bool) -> None:
        normalized = str(key or "").strip().lower()
        if not normalized:
            return
        settings = getattr(self.mw, "app_settings", None)
        if settings is None:
            return
        current = getattr(settings, "property_panel_section_state", {})
        state = dict(current) if isinstance(current, dict) else {}
        value = bool(checked)
        if state.get(normalized) == value:
            return
        state[normalized] = value
        settings.property_panel_section_state = state
        settings_manager = getattr(self.mw, "settings_manager", None)
        if settings_manager is not None and hasattr(settings_manager, "save_app_settings"):
            settings_manager.save_app_settings()

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

    def _on_target_position_changed(self, pos) -> None:
        """ターゲットの位置変更通知を受け取る。"""
        if self.current_target == self.sender():
            self.update_coordinates()

    def set_target_and_disconnect_old(self, target):
        # Helper if needed, but modifying set_target directly above
        pass

    def refresh_ui(self) -> None:
        """現在のターゲットに合わせてUIを完全に再構築します。"""

        from windows.connector import ConnectorLabel, ConnectorLine
        from windows.image_window import ImageWindow
        from windows.text_window import TextWindow

        self._init_property_widgets()
        self.clear_layout(self.scroll_layout)

        if self.current_target is None:
            lbl = QLabel(tr("prop_no_selection"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl)
            return

        # ターゲット毎のビルド分岐
        if isinstance(self.current_target, (TextWindow, ConnectorLabel)):
            self.build_text_window_ui()
        elif isinstance(self.current_target, ImageWindow):
            self.build_image_window_ui()
        elif isinstance(self.current_target, ConnectorLine):
            self.build_connector_ui()

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
        is_task_mode = bool(t.is_task_mode()) if hasattr(t, "is_task_mode") else False
        if self.lbl_editing_target is not None:
            self.lbl_editing_target.setText(self._format_editing_target_text(t))
        if self.btn_task_mode and hasattr(t, "is_task_mode"):
            self.btn_task_mode.blockSignals(True)
            self.btn_task_mode.setChecked(is_task_mode)
            self.btn_task_mode.blockSignals(False)

        if self.btn_text_orientation:
            self.btn_text_orientation.blockSignals(True)
            self.btn_text_orientation.setChecked(bool(getattr(t, "is_vertical", False)))
            self.btn_text_orientation.setToolTip(tr("msg_task_mode_horizontal_only") if is_task_mode else "")
            self.btn_text_orientation.blockSignals(False)

        if self.lbl_task_progress and hasattr(t, "get_task_progress"):
            done, total = t.get_task_progress()
            self.lbl_task_progress.setText(tr("label_task_progress_fmt").format(done=done, total=total))

        if self.edit_note_title:
            with QSignalBlocker(self.edit_note_title):
                self.edit_note_title.setText(str(getattr(t, "title", "") or ""))

        if self.edit_note_tags:
            raw_tags = getattr(t, "tags", [])
            tag_text = ", ".join(str(tag) for tag in raw_tags if str(tag).strip()) if isinstance(raw_tags, list) else ""
            with QSignalBlocker(self.edit_note_tags):
                self.edit_note_tags.setText(tag_text)

        if self.edit_note_due_at:
            due_text = display_due_iso(str(getattr(t, "due_at", "") or ""))
            with QSignalBlocker(self.edit_note_due_at):
                self.edit_note_due_at.setText(due_text)
            self._set_due_input_invalid(False)

        if self.cmb_note_due_precision is not None:
            due_precision = self._sanitize_due_precision(getattr(t, "due_precision", "date"))
            idx = self.cmb_note_due_precision.findData(due_precision)
            with QSignalBlocker(self.cmb_note_due_precision):
                self.cmb_note_due_precision.setCurrentIndex(idx if idx >= 0 else 0)

        if self.edit_note_due_time is not None:
            with QSignalBlocker(self.edit_note_due_time):
                self.edit_note_due_time.setText(str(getattr(t, "due_time", "") or ""))

        if self.edit_note_due_timezone is not None:
            with QSignalBlocker(self.edit_note_due_timezone):
                self.edit_note_due_timezone.setText(str(getattr(t, "due_timezone", "") or ""))

        self._sync_due_detail_enabled_state()

        if self.btn_note_star:
            self.btn_note_star.blockSignals(True)
            self.btn_note_star.setChecked(bool(getattr(t, "is_starred", False)))
            self.btn_note_star.blockSignals(False)

        if self.btn_note_archived:
            self.btn_note_archived.blockSignals(True)
            self.btn_note_archived.setChecked(bool(getattr(t, "is_archived", False)))
            self.btn_note_archived.blockSignals(False)

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

    def _pick_note_due_date(self) -> None:
        if self.edit_note_due_at is None:
            return
        selected = DatePickerDialog.pick_date(self, self.edit_note_due_at.text())
        if selected is None:
            return
        self.edit_note_due_at.setText(selected)
        self._set_due_input_invalid(False)

    @staticmethod
    def _due_text_for_offset(days: int) -> str:
        return (date.today() + timedelta(days=int(days))).isoformat()

    def _set_quick_due_offset(self, days: int) -> None:
        if self.edit_note_due_at is None:
            return
        self.edit_note_due_at.setText(self._due_text_for_offset(days))
        self._set_due_input_invalid(False)

    def _clear_quick_due(self) -> None:
        if self.edit_note_due_at is None:
            return
        self.edit_note_due_at.setText("")
        self._set_due_input_invalid(False)

    @staticmethod
    def _sanitize_due_precision(value: Any) -> str:
        raw = str(value or "").strip().lower()
        return "datetime" if raw == "datetime" else "date"

    @staticmethod
    def _resolve_note_meta_trigger_source(raw: str, sender_obj: Any) -> str:
        normalized = str(raw or "button").strip().lower()
        if normalized in {"button", "enter", "blur"}:
            return normalized
        if normalized != "auto":
            return "button"
        if isinstance(sender_obj, QLineEdit) and sender_obj.hasFocus():
            return "enter"
        return "blur"

    def _set_due_input_invalid(self, invalid: bool, message: str = "") -> None:
        if self.edit_note_due_at is None:
            return
        self.edit_note_due_at.setProperty("inputInvalid", bool(invalid))
        self.edit_note_due_at.setToolTip(str(message or "") if invalid else "")
        style = self.edit_note_due_at.style()
        if style is not None:
            style.unpolish(self.edit_note_due_at)
            style.polish(self.edit_note_due_at)
        self.edit_note_due_at.update()

    def _sync_due_detail_enabled_state(self) -> None:
        precision = self._sanitize_due_precision(
            self.cmb_note_due_precision.currentData() if self.cmb_note_due_precision else "date"
        )
        enabled = precision == "datetime"
        if self.edit_note_due_time is not None:
            self.edit_note_due_time.setEnabled(enabled)
        if self.edit_note_due_timezone is not None:
            self.edit_note_due_timezone.setEnabled(enabled)

    def _on_due_precision_changed(self, _: int) -> None:
        self._sync_due_detail_enabled_state()

    def _on_text_orientation_toggled(self, checked: bool, target: Any) -> None:
        if not hasattr(target, "set_undoable_property"):
            return
        target.set_undoable_property("is_vertical", bool(checked), "update_text")
        self.update_property_values()

    @staticmethod
    def _parse_tags_csv(raw: str) -> list[str]:
        tags: list[str] = []
        seen: set[str] = set()
        for token in str(raw or "").split(","):
            tag = token.strip()
            key = tag.lower()
            if not tag or key in seen:
                continue
            tags.append(tag)
            seen.add(key)
        return tags

    def _apply_note_metadata_to_target(self, target: Any, trigger_source: str = "button") -> bool:
        trigger = self._resolve_note_meta_trigger_source(trigger_source, self.sender())
        title = self.edit_note_title.text().strip() if self.edit_note_title is not None else ""
        tags = self._parse_tags_csv(self.edit_note_tags.text() if self.edit_note_tags is not None else "")
        due_raw = self.edit_note_due_at.text().strip() if self.edit_note_due_at is not None else ""
        due_precision = self._sanitize_due_precision(
            self.cmb_note_due_precision.currentData() if self.cmb_note_due_precision is not None else "date"
        )
        due_time_raw = self.edit_note_due_time.text().strip() if self.edit_note_due_time is not None else ""
        due_timezone_raw = self.edit_note_due_timezone.text().strip() if self.edit_note_due_timezone is not None else ""
        starred = self.btn_note_star.isChecked() if self.btn_note_star is not None else False
        archived = self.btn_note_archived.isChecked() if self.btn_note_archived is not None else False

        due_iso = normalize_due_input_allow_empty(due_raw)
        if due_iso is None:
            self._set_due_input_invalid(True, tr("msg_invalid_due_date_format"))
            if trigger != "blur":
                QMessageBox.warning(self, tr("msg_error"), tr("msg_invalid_due_date_format"))
            return False
        self._set_due_input_invalid(False)

        normalized_due_time = normalize_due_time(due_time_raw)
        if normalized_due_time is None:
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_invalid_due_time_format"))
            normalized_due_time = ""
            due_precision = "date"

        if due_precision != "datetime":
            normalized_due_time = ""
            due_timezone_raw = ""
        elif not normalized_due_time:
            due_precision = "date"
            due_timezone_raw = ""

        if due_timezone_raw and not is_valid_timezone(due_timezone_raw):
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_invalid_due_timezone"))
            due_timezone_raw = ""

        if not due_iso:
            due_precision = "date"
            normalized_due_time = ""
            due_timezone_raw = ""

        if hasattr(target, "set_title_and_tags"):
            target.set_title_and_tags(title, tags)
        else:
            target.set_undoable_property("title", title, "update_text")
            target.set_undoable_property("tags", tags, "update_text")

        if hasattr(target, "set_starred"):
            target.set_starred(starred)
        else:
            target.set_undoable_property("is_starred", bool(starred), "update_text")

        if due_iso:
            if hasattr(target, "set_due_at"):
                target.set_due_at(due_iso)
            else:
                target.set_undoable_property("due_at", due_iso, "update_text")
        else:
            if hasattr(target, "clear_due_at"):
                target.clear_due_at()
            else:
                target.set_undoable_property("due_at", "", "update_text")

        if hasattr(target, "set_undoable_property"):
            target.set_undoable_property("due_precision", due_precision, None)
            target.set_undoable_property("due_time", str(normalized_due_time or ""), None)
            target.set_undoable_property("due_timezone", str(due_timezone_raw or ""), None)

        if hasattr(target, "set_archived"):
            target.set_archived(bool(archived))
        else:
            target.set_undoable_property("is_archived", bool(archived), "update_text")

        self.update_property_values()
        if self.mw and hasattr(self.mw, "info_tab"):
            self.mw.info_tab.refresh_data()
        return True

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

    @staticmethod
    def _format_editing_target_text(target: Any) -> str:
        base = tr("label_anim_selected_fmt").format(name=type(target).__name__)
        text = str(getattr(target, "text", "") or "").strip()
        if not text:
            return base
        first_line = text.split("\n")[0].strip()
        if len(first_line) > 30:
            first_line = first_line[:30] + "..."
        if not first_line:
            return base
        return f"{base} / {first_line}"

    # --- UI Helper Methods ---

    def create_collapsible_group(self, title: str, expanded: bool = True, state_key: str | None = None) -> QFormLayout:
        """Phase 5: Collapsible Group Implementation"""
        box = CollapsibleBox(title)

        # Content Widget & Layout
        content_widget = QWidget()
        layout = QFormLayout(content_widget)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 8, 4, 4)  # Phase 5: Tight margins
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)  # Phase 5: Wrap labels
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        box.setContentLayout(layout)

        # Initial State
        actual_expanded = expanded
        if state_key is not None:
            actual_expanded = self._load_property_panel_section_state(state_key, expanded)
            self._section_boxes[state_key] = box
            box.toggle_button.toggled.connect(
                lambda checked, key=state_key: self._save_property_panel_section_state(key, checked)
            )
        box.toggle_button.setChecked(actual_expanded)
        box.on_toggled(actual_expanded)

        self.scroll_layout.addWidget(box)
        return layout

    def create_group(self, title: str) -> QFormLayout:
        """Deprecated: Use create_collapsible_group. Kept for compatibility during refactor."""
        return self.create_collapsible_group(title, True)

    def add_dual_row(self, layout: QFormLayout, widget1: QWidget, widget2: QWidget, label1: str = "", label2: str = ""):
        """Phase 5: Add two widgets in a single row (2-column grid)."""
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        if label1:
            l1 = QLabel(label1)
            l1.setProperty("class", "small")
            h_layout.addWidget(l1)
        h_layout.addWidget(widget1)

        if label2:
            l2 = QLabel(label2)
            l2.setProperty("class", "small")
            h_layout.addWidget(l2)
        h_layout.addWidget(widget2)

        layout.addRow(container)

    def create_spinbox(
        self,
        value: float,
        min_v: float,
        max_v: float,
        step: float,
        callback: Callable,
        is_float: bool = False,
    ) -> Union[QSpinBox, QDoubleSpinBox]:
        """Phase 5: Create spinbox without adding to layout."""
        spin = QDoubleSpinBox() if is_float else QSpinBox()
        if is_float:
            spin.setDecimals(2)
        spin.setRange(min_v, max_v)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.valueChanged.connect(callback)
        return spin

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
        spin = self.create_spinbox(value, min_v, max_v, step, callback, is_float)
        layout.addRow(label, spin)
        return spin

    def create_slider_spin(
        self,
        value: float,
        min_v: float,
        max_v: float,
        commit_cb: Callable[[float], None],
        preview_cb: Optional[Callable[[float], None]] = None,
        unit_scale: float = 1.0,
    ) -> Tuple[QWidget, QDoubleSpinBox, QSlider]:
        """Phase 5: Create slider+spin container."""
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        spin = QDoubleSpinBox()
        spin.setRange(float(min_v), float(max_v))
        spin.setValue(float(value))
        spin.setSingleStep(1.0 if unit_scale == 1.0 else 0.1)

        slider = QSlider(Qt.Orientation.Horizontal)
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
        return container, spin, slider

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
        container, spin, slider = self.create_slider_spin(value, min_v, max_v, commit_cb, preview_cb, unit_scale)
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

        slider = QSlider(Qt.Orientation.Horizontal)
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

    def add_slider_spin_float(
        self,
        layout: QFormLayout,
        label: str,
        value: float,
        min_v: float,
        max_v: float,
        commit_cb: Callable[[float], None],
        preview_cb: Optional[Callable[[float], None]] = None,
        step: float = 0.1,
    ) -> Tuple[QDoubleSpinBox, QSlider]:
        """Float値対応のslider+spinbox combo生成。

        Args:
            layout: 追加先レイアウト。
            label: 行のラベル。
            value: 現在値。
            min_v: 最小値。
            max_v: 最大値。
            commit_cb: 確定反映コールバック。
            preview_cb: プレビューコールバック（ドラッグ中）。
            step: spinbox刻み。

        Returns:
            Tuple[QDoubleSpinBox, QSlider]: (spinbox, slider)
        """
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # Calculate decimals from step
        decimals = 2 if step < 0.1 else 1

        # Float spinbox
        spin = QDoubleSpinBox()
        spin.setRange(min_v, max_v)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.setValue(value)

        # Integer slider (scaled dynamically based on step)
        scale_factor = int(1.0 / step) if step > 0 else 10
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(min_v * scale_factor), int(max_v * scale_factor))
        slider.setSingleStep(1)
        slider.setValue(int(value * scale_factor))

        state: dict[str, bool] = {"is_dragging": False}

        def on_slider_pressed() -> None:
            state["is_dragging"] = True

        def on_slider_released() -> None:
            state["is_dragging"] = False
            v = slider.value() / scale_factor
            commit_cb(v)

        def on_slider_changed(val: int) -> None:
            v = val / scale_factor
            with QSignalBlocker(spin):
                spin.setValue(v)
            if state["is_dragging"] and preview_cb:
                preview_cb(v)

        def on_spin_changed(val: float) -> None:
            with QSignalBlocker(slider):
                slider.setValue(int(val * scale_factor))
            commit_cb(val)

        slider.sliderPressed.connect(on_slider_pressed)
        slider.sliderReleased.connect(on_slider_released)
        slider.valueChanged.connect(on_slider_changed)
        spin.valueChanged.connect(on_spin_changed)

        h_layout.addWidget(slider)
        h_layout.addWidget(spin)
        layout.addRow(label, container)
        return spin, slider

    def create_color_button(self, current_color: QColor, callback: Callable) -> QPushButton:
        """Phase 5: Create color button."""
        btn = QPushButton()
        btn.setFixedHeight(24)
        self.update_color_button_style(btn, current_color)

        def on_click():
            color = QColorDialog.getColor(
                current_color, self, tr("prop_color"), QColorDialog.ColorDialogOption.ShowAlphaChannel
            )
            if color.isValid():
                self.update_color_button_style(btn, color)
                callback(color)

        btn.clicked.connect(on_click)
        return btn

    def add_color_button(
        self, layout: QFormLayout, label: str, current_color: QColor, callback: Callable
    ) -> QPushButton:
        btn = self.create_color_button(current_color, callback)
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
                    return color.name(QColor.NameFormat.HexArgb)
                return "#FFFFFFFF"

            c = QColor(str(color))
            if c.isValid():
                return c.name(QColor.NameFormat.HexArgb)
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

    def create_action_button(self, label: str, callback: Callable, class_name: str = "secondary-button") -> QPushButton:
        btn = QPushButton(label)
        btn.setProperty("class", class_name)
        btn.clicked.connect(callback)
        return btn

    def add_action_button(
        self, layout: QFormLayout, label: str, callback: Callable, class_name: str = "secondary-button"
    ) -> QPushButton:
        btn = self.create_action_button(label, callback, class_name)
        layout.addRow("", btn)
        return btn

    # --- Section Builders ---

    def build_common_ui(self, target: Any) -> None:
        """全ウィンドウ共通のトランスフォーム設定。"""
        # Phase 5: Collapsible Group & Dual Row
        layout = self.create_collapsible_group(tr("prop_grp_transform"), expanded=True)

        # Dual Row for X / Y
        self.spin_x = self.create_spinbox(target.x(), -9999, 9999, 1, lambda v: target.move(v, target.y()))
        self.spin_y = self.create_spinbox(target.y(), -9999, 9999, 1, lambda v: target.move(target.x(), v))

        self.add_dual_row(layout, self.spin_x, self.spin_y, tr("prop_x"), tr("prop_y"))

        self.add_action_button(layout, tr("btn_toggle_front"), target.toggle_frontmost, "secondary-button")

    def build_text_window_ui(self) -> None:
        """テキストウィンドウ用のUI構築。"""
        from windows.connector import ConnectorLabel
        from windows.text_window import TextWindow

        target = self.current_target

        if not isinstance(target, ConnectorLabel):
            self.build_common_ui(target)
        else:
            layout = self.create_group(tr("prop_grp_transform"))
            layout.addRow(QLabel(tr("prop_pos_auto_linked")))
            self.add_action_button(layout, tr("btn_toggle_front"), target.toggle_frontmost, "secondary-button")

        if isinstance(target, TextWindow):
            self.lbl_editing_target = QLabel(self._format_editing_target_text(target))
            self.lbl_editing_target.setProperty("class", "info-label")
            self.scroll_layout.addWidget(self.lbl_editing_target)

            mode_row = QWidget()
            mode_row_layout = QHBoxLayout(mode_row)
            mode_row_layout.setContentsMargins(0, 0, 0, 0)
            mode_row_layout.setSpacing(4)
            lbl_mode = QLabel(tr("label_content_mode"))
            lbl_mode.setProperty("class", "small")
            # Text Content (TextWindow only)
            self.btn_task_mode = self.create_action_button(
                tr("menu_toggle_task_mode"),
                lambda checked: target.set_content_mode("task" if checked else "note"),
                "toggle",
            )
            self.btn_task_mode.setCheckable(True)
            self.btn_task_mode.setChecked(target.is_task_mode())
            mode_row_layout.addWidget(lbl_mode, 0)
            mode_row_layout.addWidget(self.btn_task_mode, 1)
            self.scroll_layout.addWidget(mode_row)

            text_content_layout = self.create_collapsible_group(
                tr("prop_grp_text_content"), expanded=True, state_key="text_content"
            )

            self.btn_text_orientation = self.create_action_button(
                tr("btn_toggle_orientation"),
                lambda checked: self._on_text_orientation_toggled(checked, target),
                "toggle",
            )
            self.btn_text_orientation.setCheckable(True)
            self.btn_text_orientation.setChecked(bool(getattr(target, "is_vertical", False)))
            self.btn_text_orientation.setToolTip(tr("msg_task_mode_horizontal_only") if target.is_task_mode() else "")
            text_content_layout.addRow("", typing.cast(QWidget, self.btn_text_orientation))

            # タスク進捗UI（タスクモード時のみ表示）
            if target.is_task_mode():
                done, total = target.get_task_progress()
                progress_text = tr("label_task_progress_fmt").format(done=done, total=total)
                self.lbl_task_progress = QLabel(progress_text)
                self.lbl_task_progress.setProperty("class", "info-label")
                text_content_layout.addRow("", typing.cast(QWidget, self.lbl_task_progress))

                btn_row = QWidget()
                btn_h = QHBoxLayout(btn_row)
                btn_h.setContentsMargins(0, 0, 0, 0)
                btn_h.setSpacing(4)

                self.btn_complete_all = QPushButton(tr("btn_complete_all_tasks"))
                self.btn_complete_all.setProperty("class", "secondary-button")
                self.btn_complete_all.clicked.connect(
                    lambda: target.complete_all_tasks() or self.update_property_values()
                )

                self.btn_uncomplete_all = QPushButton(tr("btn_uncomplete_all_tasks"))
                self.btn_uncomplete_all.setProperty("class", "secondary-button")
                self.btn_uncomplete_all.clicked.connect(
                    lambda: target.uncomplete_all_tasks() or self.update_property_values()
                )

                btn_h.addWidget(self.btn_complete_all)
                btn_h.addWidget(self.btn_uncomplete_all)
                text_content_layout.addRow("", btn_row)

            self.edit_note_title = QLineEdit(str(getattr(target, "title", "") or ""))
            self.edit_note_title.setPlaceholderText(tr("placeholder_note_title"))
            text_content_layout.addRow(tr("label_note_title"), typing.cast(QWidget, self.edit_note_title))

            raw_tags = getattr(target, "tags", [])
            tag_text = ", ".join(str(tag) for tag in raw_tags if str(tag).strip()) if isinstance(raw_tags, list) else ""
            self.edit_note_tags = QLineEdit(tag_text)
            self.edit_note_tags.setPlaceholderText(tr("placeholder_note_tags"))
            text_content_layout.addRow(tr("label_note_tags"), typing.cast(QWidget, self.edit_note_tags))

            due_text = display_due_iso(str(getattr(target, "due_at", "") or ""))
            self.edit_note_due_at = QLineEdit(due_text)
            self.edit_note_due_at.setPlaceholderText(tr("placeholder_note_due_at"))
            self.btn_pick_note_due_at = QPushButton(tr("btn_pick_due_date"))
            self.btn_pick_note_due_at.setProperty("class", "secondary-button")
            self.btn_pick_note_due_at.clicked.connect(self._pick_note_due_date)

            due_row = QWidget()
            due_row_layout = QHBoxLayout(due_row)
            due_row_layout.setContentsMargins(0, 0, 0, 0)
            due_row_layout.setSpacing(4)
            due_row_layout.addWidget(self.edit_note_due_at, 1)
            due_row_layout.addWidget(self.btn_pick_note_due_at)
            text_content_layout.addRow(tr("label_note_due_at"), due_row)

            quick_due_row = QWidget()
            quick_due_layout = QHBoxLayout(quick_due_row)
            quick_due_layout.setContentsMargins(0, 0, 0, 0)
            quick_due_layout.setSpacing(4)
            self.btn_due_today = QPushButton(tr("btn_today"))
            self.btn_due_today.setProperty("class", "secondary-button")
            self.btn_due_today.clicked.connect(lambda: self._set_quick_due_offset(0))
            quick_due_layout.addWidget(self.btn_due_today)
            self.btn_due_tomorrow = QPushButton(tr("due_quick_tomorrow"))
            self.btn_due_tomorrow.setProperty("class", "secondary-button")
            self.btn_due_tomorrow.clicked.connect(lambda: self._set_quick_due_offset(1))
            quick_due_layout.addWidget(self.btn_due_tomorrow)
            self.btn_due_next_week = QPushButton(tr("due_quick_next_week"))
            self.btn_due_next_week.setProperty("class", "secondary-button")
            self.btn_due_next_week.clicked.connect(lambda: self._set_quick_due_offset(7))
            quick_due_layout.addWidget(self.btn_due_next_week)
            self.btn_due_clear = QPushButton(tr("btn_clear"))
            self.btn_due_clear.setProperty("class", "secondary-button")
            self.btn_due_clear.clicked.connect(self._clear_quick_due)
            quick_due_layout.addWidget(self.btn_due_clear)
            text_content_layout.addRow("", quick_due_row)

            due_details_box = CollapsibleBox(tr("label_due_details"))
            due_details_widget = QWidget()
            due_details_layout = QFormLayout(due_details_widget)
            due_details_layout.setContentsMargins(4, 4, 4, 4)
            due_details_layout.setSpacing(4)

            self.cmb_note_due_precision = QComboBox()
            self.cmb_note_due_precision.addItem(tr("label_due_precision_date"), "date")
            self.cmb_note_due_precision.addItem(tr("label_due_precision_datetime"), "datetime")
            due_precision = self._sanitize_due_precision(getattr(target, "due_precision", "date"))
            due_precision_idx = self.cmb_note_due_precision.findData(due_precision)
            self.cmb_note_due_precision.setCurrentIndex(due_precision_idx if due_precision_idx >= 0 else 0)
            self.cmb_note_due_precision.currentIndexChanged.connect(self._on_due_precision_changed)

            self.edit_note_due_time = QLineEdit(str(getattr(target, "due_time", "") or ""))
            self.edit_note_due_time.setPlaceholderText(tr("placeholder_due_time"))
            self.edit_note_due_timezone = QLineEdit(str(getattr(target, "due_timezone", "") or ""))
            self.edit_note_due_timezone.setPlaceholderText(tr("placeholder_due_timezone"))

            due_details_layout.addRow(tr("label_due_precision"), typing.cast(QWidget, self.cmb_note_due_precision))
            due_details_layout.addRow(tr("label_due_time"), typing.cast(QWidget, self.edit_note_due_time))
            due_details_layout.addRow(tr("label_due_timezone"), typing.cast(QWidget, self.edit_note_due_timezone))

            due_details_box.setContentLayout(due_details_layout)
            due_details_box.toggle_button.setChecked(False)
            due_details_box.on_toggled(False)
            text_content_layout.addRow("", due_details_box)
            self._sync_due_detail_enabled_state()

            self.btn_note_star = self.create_action_button(tr("label_note_star"), lambda: None, "toggle")
            self.btn_note_star.setCheckable(True)
            self.btn_note_star.setChecked(bool(getattr(target, "is_starred", False)))

            self.btn_note_archived = self.create_action_button(tr("label_note_archived"), lambda: None, "toggle")
            self.btn_note_archived.setCheckable(True)
            self.btn_note_archived.setChecked(bool(getattr(target, "is_archived", False)))

            self.btn_apply_note_meta = QPushButton(tr("btn_apply_note_meta"))
            self.btn_apply_note_meta.setProperty("class", "secondary-button")
            self.edit_note_title.editingFinished.connect(lambda: self._apply_note_metadata_to_target(target, "auto"))
            self.edit_note_tags.editingFinished.connect(lambda: self._apply_note_metadata_to_target(target, "auto"))
            self.edit_note_due_at.editingFinished.connect(lambda: self._apply_note_metadata_to_target(target, "auto"))
            if self.edit_note_due_time is not None:
                self.edit_note_due_time.returnPressed.connect(
                    lambda: self._apply_note_metadata_to_target(target, "enter")
                )
            if self.edit_note_due_timezone is not None:
                self.edit_note_due_timezone.returnPressed.connect(
                    lambda: self._apply_note_metadata_to_target(target, "enter")
                )
            self.btn_apply_note_meta.clicked.connect(lambda: self._apply_note_metadata_to_target(target, "button"))

            meta_btn_row = QWidget()
            meta_btn_layout = QHBoxLayout(meta_btn_row)
            meta_btn_layout.setContentsMargins(0, 0, 0, 0)
            meta_btn_layout.setSpacing(4)
            meta_btn_layout.addWidget(self.btn_note_star)
            meta_btn_layout.addWidget(self.btn_note_archived)
            meta_btn_layout.addWidget(self.btn_apply_note_meta)
            text_content_layout.addRow("", meta_btn_row)

        # Text Style
        text_style_layout = self.create_collapsible_group(
            tr("prop_grp_text_style"), expanded=True, state_key="text_style"
        )

        self.btn_text_font = QPushButton(f"{target.font_family} ({target.font_size}pt)")
        self.btn_text_font.setProperty("class", "secondary-button")

        def change_font():
            font = choose_font(self, QFont(target.font_family, int(target.font_size)))
            if font is not None:
                try:
                    target.set_undoable_property("font_family", font.family())
                    target.set_undoable_property("font_size", font.pointSize())
                    target.update_text()
                except Exception as e:
                    import traceback

                    logger.error(f"Failed to change font: {e}\n{traceback.format_exc()}")
                    QMessageBox.warning(self, tr("msg_error"), f"Font change failed: {e}")

        self.btn_text_font.clicked.connect(change_font)
        text_style_layout.addRow(tr("prop_font_selector"), typing.cast(QWidget, self.btn_text_font))

        # Font Size (slider+spinbox)
        commit, prev = self._make_callbacks(target, "font_size", "update_text", True)
        self.spin_text_font_size, self.slider_text_font_size = self.add_slider_spin(
            text_style_layout, tr("prop_size"), target.font_size, 1, 200, commit, prev
        )

        self.btn_text_color = self.add_color_button(
            text_style_layout,
            tr("prop_color"),
            target.font_color,
            lambda v: target.set_undoable_property("font_color", self._normalize_color_to_hexargb(v), "update_text"),
        )

        commit, prev = self._make_callbacks(target, "text_opacity", "update_text", True)
        self.spin_text_opacity, self.slider_text_opacity = self.add_slider_spin(
            text_style_layout, tr("label_opacity"), target.text_opacity, 0, 100, commit, prev
        )

        # --- Text Gradient ---
        self.btn_text_gradient_toggle = QPushButton(tr("menu_toggle_text_gradient"))
        self.btn_text_gradient_toggle.setProperty("class", "toggle")
        self.btn_text_gradient_toggle.setCheckable(True)
        self.btn_text_gradient_toggle.setChecked(target.text_gradient_enabled)
        self.btn_text_gradient_toggle.clicked.connect(
            lambda c: target.set_undoable_property("text_gradient_enabled", c, "update_text")
        )
        text_style_layout.addRow("", typing.cast(QWidget, self.btn_text_gradient_toggle))

        self.btn_edit_text_gradient = QPushButton("🎨 " + tr("menu_edit_text_gradient"))
        self.btn_edit_text_gradient.setProperty("class", "secondary-button")
        self.btn_edit_text_gradient.clicked.connect(self._open_text_gradient_dialog)
        text_style_layout.addRow("", typing.cast(QWidget, self.btn_edit_text_gradient))

        commit, prev = self._make_callbacks(target, "text_gradient_opacity", "update_text", True)
        self.spin_text_gradient_opacity, self.slider_text_gradient_opacity = self.add_slider_spin(
            text_style_layout, tr("menu_set_text_gradient_opacity"), target.text_gradient_opacity, 0, 100, commit, prev
        )

        # Low-frequency actions are moved to overflow menu for compactness.
        self.btn_text_style_more = QToolButton()
        self.btn_text_style_more.setProperty("class", "secondary-button")
        self.btn_text_style_more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_text_style_more.setText(tr("btn_more_actions"))
        style_more_menu = QMenu(self.btn_text_style_more)
        act_save_text_def = style_more_menu.addAction("💾 " + tr("btn_save_as_default"))
        act_save_text_def.setToolTip(tr("tip_save_text_default"))
        if self.mw and hasattr(self.mw, "main_controller"):
            act_save_text_def.triggered.connect(self.mw.main_controller.txt_actions.save_as_default)
        self.btn_text_style_more.setMenu(style_more_menu)
        text_style_layout.addRow("", typing.cast(QWidget, self.btn_text_style_more))

        # --- Appearance Group (Collapsed) ---
        layout = self.create_collapsible_group(tr("prop_grp_background"), expanded=False, state_key="background")

        # Background Toggle
        self.btn_bg_toggle = self.create_action_button(
            tr("prop_bg_visible"),
            lambda: target.set_undoable_property("background_visible", not target.background_visible, "update_text"),
            "toggle",
        )
        self.btn_bg_toggle.setCheckable(True)
        self.btn_bg_toggle.setChecked(target.background_visible)
        layout.addRow("", cast(QWidget, self.btn_bg_toggle))

        # Bg Color (separate row)
        self.btn_bg_color = self.add_color_button(
            layout,
            tr("prop_color"),
            QColor(target.background_color),
            lambda c: target.set_undoable_property(
                "background_color", self._normalize_color_to_hexargb(c), "update_text"
            ),
        )

        # Bg Corner Radius (slider+spinbox, float 0-1.0)
        commit, prev = self._make_callbacks(target, "background_corner_ratio", "update_text", False)
        self.spin_bg_corner, self.slider_bg_corner = self.add_slider_spin_float(
            layout, tr("prop_corner_radius"), target.background_corner_ratio, 0, 1.0, commit, prev, step=0.05
        )

        # Bg Opacity (0-100 int range)
        c_bg_opacity, self.spin_bg_opacity, self.slider_bg_opacity = self.create_slider_spin(
            target.background_opacity,
            0,
            100,
            lambda v: target.set_undoable_property("background_opacity", v, "update_text"),
            lambda v: setattr(target, "background_opacity", v) or target.update_text(),
        )
        layout.addRow(tr("prop_opacity"), c_bg_opacity)

        # Bg Gradient
        self.btn_bg_gradient_toggle = self.create_action_button(
            tr("prop_gradient_enabled"),
            lambda: target.set_undoable_property(
                "background_gradient_enabled", not target.background_gradient_enabled, "update_text"
            ),
            "toggle",
        )
        self.btn_bg_gradient_toggle.setCheckable(True)
        self.btn_bg_gradient_toggle.setChecked(target.background_gradient_enabled)

        self.btn_edit_bg_gradient = self.create_action_button(
            tr("prop_gradient_edit"), self._open_bg_gradient_dialog, "secondary-button"
        )
        self.add_dual_row(layout, self.btn_bg_gradient_toggle, self.btn_edit_bg_gradient)

        c_bg_g_opacity, self.spin_bg_gradient_opacity, self.slider_bg_gradient_opacity = self.create_slider_spin(
            target.background_gradient_opacity,
            0,
            100,
            lambda v: target.set_undoable_property("background_gradient_opacity", v, "update_text"),
            lambda v: setattr(target, "background_gradient_opacity", v) or target.update_text(),
        )
        layout.addRow(tr("prop_opacity"), c_bg_g_opacity)

        # Archetype Save Button for Background
        btn_save_bg_def = QPushButton("💾 " + tr("btn_save_as_default"))
        btn_save_bg_def.setProperty("class", "secondary-button")
        btn_save_bg_def.setToolTip(tr("tip_save_bg_default"))
        if self.mw and hasattr(self.mw, "main_controller"):
            btn_save_bg_def.clicked.connect(self.mw.main_controller.txt_actions.save_as_default)
        layout.addRow("", typing.cast(QWidget, btn_save_bg_def))

        # --- Effects Group (Collapsed) ---
        layout = self.create_collapsible_group(tr("prop_grp_shadow"), expanded=False, state_key="shadow")

        # Shadow Toggle
        self.btn_shadow_toggle = self.create_action_button(
            tr("prop_shadow_enabled"),
            lambda: target.set_undoable_property("shadow_enabled", not target.shadow_enabled, "update_text"),
            "toggle",
        )
        self.btn_shadow_toggle.setCheckable(True)
        self.btn_shadow_toggle.setChecked(target.shadow_enabled)
        layout.addRow("", cast(QWidget, self.btn_shadow_toggle))

        # Shadow Color (separate row)
        self.btn_shadow_color = self.add_color_button(
            layout,
            tr("prop_color"),
            QColor(target.shadow_color),
            lambda c: target.set_undoable_property("shadow_color", self._normalize_color_to_hexargb(c), "update_text"),
        )

        # Shadow Blur (slider+spinbox, 0-50)
        commit, prev = self._make_callbacks(target, "shadow_blur", "update_text", True)
        self.spin_shadow_blur, self.slider_shadow_blur = self.add_slider_spin(
            layout, tr("prop_blur"), target.shadow_blur, 0, 50, commit, prev
        )

        # Shadow Offset X (slider+spinbox, float -1.0~1.0 - multiplier)
        commit_x, prev_x = self._make_callbacks(target, "shadow_offset_x", "update_text", False)
        self.spin_shadow_offset_x, self.slider_shadow_offset_x = self.add_slider_spin_float(
            layout, tr("label_offset_x"), target.shadow_offset_x, -1.0, 1.0, commit_x, prev_x, step=0.05
        )

        # Shadow Offset Y (slider+spinbox, float -1.0~1.0 - multiplier)
        commit_y, prev_y = self._make_callbacks(target, "shadow_offset_y", "update_text", False)
        self.spin_shadow_offset_y, self.slider_shadow_offset_y = self.add_slider_spin_float(
            layout, tr("label_offset_y"), target.shadow_offset_y, -1.0, 1.0, commit_y, prev_y, step=0.05
        )

        # Shadow Opacity
        c_sh_opacity, self.spin_shadow_opacity, self.slider_shadow_opacity = self.create_slider_spin(
            target.shadow_opacity,
            0,
            100,
            lambda v: target.set_undoable_property("shadow_opacity", v, "update_text"),
            lambda v: setattr(target, "shadow_opacity", v) or target.update_text(),
        )
        layout.addRow(tr("prop_opacity"), c_sh_opacity)

        # --- Outline Group (Restored) ---
        layout = self.create_collapsible_group(tr("prop_grp_outline_settings"), expanded=False, state_key="outline")

        # Helper for Outline
        def add_outline_ui(index: int) -> None:
            prefix = "" if index == 1 else "second_" if index == 2 else "third_"
            ui_label_key = f"prop_outline_{index}"

            # Toggle & Color (Dual)
            btn_toggle = self.create_action_button(
                tr(ui_label_key),
                lambda: target.set_undoable_property(
                    f"{prefix}outline_enabled", not getattr(target, f"{prefix}outline_enabled"), "update_text"
                ),
                "toggle",
            )
            btn_toggle.setCheckable(True)
            btn_toggle.setChecked(getattr(target, f"{prefix}outline_enabled"))
            setattr(self, f"btn_outline_{index}_toggle", btn_toggle)

            btn_color = self.create_color_button(
                QColor(getattr(target, f"{prefix}outline_color")),
                lambda c: target.set_undoable_property(
                    f"{prefix}outline_color", self._normalize_color_to_hexargb(c), "update_text"
                ),
            )
            setattr(self, f"btn_outline_{index}_color", btn_color)

            self.add_dual_row(layout, btn_toggle, btn_color)

            # Width (slider+spinbox, float)
            pref = prefix  # capture for nested functions

            def make_commit_width(p: str) -> Callable[[float], None]:
                def _commit(v: float) -> None:
                    target.set_undoable_property(f"{p}outline_width", v, "update_text")

                return _commit

            def make_prev_width(p: str) -> Callable[[float], None]:
                def _prev(v: float) -> None:
                    setattr(target, f"{p}outline_width", v)
                    target.update_text()

                return _prev

            spin_width, slider_width = self.add_slider_spin_float(
                layout,
                tr("prop_width"),
                getattr(target, f"{prefix}outline_width"),
                0,
                30,  # Realistic max width
                make_commit_width(pref),
                make_prev_width(pref),
                step=0.5,
            )
            setattr(self, f"spin_outline_{index}_width", spin_width)
            setattr(self, f"slider_outline_{index}_width", slider_width)

            # Blur (slider+spinbox, int 0-50 matching model type)
            def make_commit_blur_int(p: str) -> Callable[[int], None]:
                def _commit(v: int) -> None:
                    target.set_undoable_property(f"{p}outline_blur", int(v), "update_text")

                return _commit

            def make_prev_blur_int(p: str) -> Callable[[int], None]:
                def _prev(v: int) -> None:
                    setattr(target, f"{p}outline_blur", int(v))
                    target.update_text()

                return _prev

            spin_blur, slider_blur = self.add_slider_spin(
                layout,
                tr("prop_blur"),
                int(getattr(target, f"{prefix}outline_blur")),
                0,
                50,
                make_commit_blur_int(pref),
                make_prev_blur_int(pref),
            )
            setattr(self, f"spin_outline_{index}_blur", spin_blur)
            setattr(self, f"slider_outline_{index}_blur", slider_blur)

            # Opacity (0-100 int range)
            c_op, spin_op, slider_op = self.create_slider_spin(
                getattr(target, f"{prefix}outline_opacity"),
                0,
                100,
                lambda v: target.set_undoable_property(f"{prefix}outline_opacity", v, "update_text"),
                lambda v: setattr(target, f"{prefix}outline_opacity", v) or target.update_text(),
            )
            setattr(self, f"spin_outline_{index}_opacity", spin_op)
            setattr(self, f"slider_outline_{index}_opacity", slider_op)
            layout.addRow(tr("prop_opacity"), c_op)

        # Add 3 outlines
        for i in range(1, 4):
            add_outline_ui(i)

        # Background Outline
        btn_bg_out_toggle = self.create_action_button(
            tr("prop_bg_outline"),
            lambda: target.set_undoable_property(
                "background_outline_enabled", not target.background_outline_enabled, "update_text"
            ),
            "toggle",
        )
        btn_bg_out_toggle.setCheckable(True)
        btn_bg_out_toggle.setChecked(target.background_outline_enabled)
        self.btn_bg_outline_toggle = btn_bg_out_toggle

        btn_bg_out_color = self.create_color_button(
            QColor(target.background_outline_color),
            lambda c: target.set_undoable_property(
                "background_outline_color", self._normalize_color_to_hexargb(c), "update_text"
            ),
        )
        self.btn_bg_outline_color = btn_bg_out_color
        self.add_dual_row(layout, btn_bg_out_toggle, btn_bg_out_color)

        # BG Outline Width (slider+spinbox, float 0-1.0)
        commit_w, prev_w = self._make_callbacks(target, "background_outline_width_ratio", "update_text", False)
        self.spin_bg_outline_width, self.slider_bg_outline_width = self.add_slider_spin_float(
            layout, tr("label_width_ratio"), target.background_outline_width_ratio, 0, 1.0, commit_w, prev_w, step=0.01
        )
        # Opacity (0-100 int range)
        c_bg_out_op, self.spin_bg_outline_opacity, self.slider_bg_outline_opacity = self.create_slider_spin(
            target.background_outline_opacity,
            0,
            100,
            lambda v: target.set_undoable_property("background_outline_opacity", v, "update_text"),
            lambda v: setattr(target, "background_outline_opacity", v) or target.update_text(),
        )
        layout.addRow(tr("prop_opacity"), c_bg_out_op)

    def build_image_window_ui(self) -> None:
        """画像ウィンドウ用のUI構築。FTIV_a1 style: integer percentage sliders."""
        target = self.current_target
        if not target:
            return

        self.build_common_ui(target)

        layout = self.create_collapsible_group(tr("prop_grp_image"), expanded=True)

        # Scale: 1-500% (FTIV_a1 style)
        commit, prev = self._make_callbacks(target, "scale_factor", "update_image", False)
        self.spin_img_scale, self.slider_img_scale = self.add_slider_spin_percent(
            layout,
            tr("prop_scale"),
            target.scale_factor,
            1,
            500,
            commit,
            prev,
            scale=100.0,
        )

        # Opacity: 0-100% (FTIV_a1 style)
        commit, prev = self._make_callbacks(target, "opacity", "update_image", False)
        self.spin_img_opacity, self.slider_img_opacity = self.add_slider_spin_percent(
            layout,
            tr("prop_opacity"),
            target.opacity,
            0,
            100,
            commit,
            prev,
            scale=100.0,
        )

        # Rotation: 0-360 degrees
        commit, prev = self._make_callbacks(target, "rotation_angle", "update_image", False)
        self.spin_img_rotation, self.slider_img_rotation = self.add_slider_spin(
            layout, tr("prop_rotation"), target.rotation_angle, 0, 360, commit, prev
        )

        # Flip Buttons (FTIV_a1 style: toggle buttons)
        f_layout = QHBoxLayout()
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(4)
        for axis in ["horizontal", "vertical"]:
            btn = QPushButton(tr(f"btn_flip_{axis}"))
            btn.setProperty("class", "toggle")
            btn.setCheckable(True)
            btn.setChecked(getattr(target, f"flip_{axis}", False))
            btn.clicked.connect(lambda c, a=axis: target.set_undoable_property(f"flip_{a}", c, "update_image"))
            f_layout.addWidget(btn)
        layout.addRow(tr("label_flip"), f_layout)

        # Animation Group (FTIV_a1 style: separate group)
        a_layout = self.create_collapsible_group(tr("menu_anim_setting_image"), expanded=False)

        # Animation Speed: 0-500% (FTIV_a1 style)
        commit, prev = self._make_callbacks(target, "animation_speed_factor", "_update_animation_timer", False)
        self.spin_anim_speed, self.slider_anim_speed = self.add_slider_spin_percent(
            a_layout,
            tr("prop_anim_speed"),
            target.animation_speed_factor,
            0,
            500,
            commit,
            prev,
            scale=100.0,
        )

        # Animation Controls (Play/Pause)
        def _anim_play():
            if target.animation_speed_factor == 0:
                new_speed = (
                    target.original_animation_speed_factor if target.original_animation_speed_factor > 0 else 1.0
                )
                target.set_undoable_property("animation_speed_factor", new_speed, "_update_animation_timer")

        def _anim_pause():
            if target.animation_speed_factor > 0:
                target.original_animation_speed_factor = target.animation_speed_factor
                target.set_undoable_property("animation_speed_factor", 0.0, "_update_animation_timer")

        def _anim_seek_start():
            target.current_frame = 0
            target.update_image()

        btn_anim_play = self.create_action_button(tr("btn_anim_play"), _anim_play, "secondary-button")
        btn_anim_pause = self.create_action_button(tr("btn_anim_pause"), _anim_pause, "secondary-button")

        row_anim = QHBoxLayout()
        row_anim.setContentsMargins(0, 0, 0, 0)
        row_anim.setSpacing(4)
        row_anim.addWidget(btn_anim_play)
        row_anim.addWidget(btn_anim_pause)
        a_layout.addRow(tr("menu_anim_toggle"), row_anim)

        # Seek to first frame
        self.add_action_button(a_layout, tr("btn_anim_seek_start"), _anim_seek_start, "secondary-button")

        # Reset playback speed to default
        self.add_action_button(
            a_layout, tr("menu_reset_gif_apng_playback_speed"), target.reset_animation_speed, "secondary-button"
        )

        # Lock Button (preserved from current FTIV)
        self.add_action_button(
            layout,
            tr("btn_unlock") if target.is_locked else tr("btn_lock"),
            lambda: setattr(target, "is_locked", not target.is_locked) or self.refresh_ui(),
            "danger-button" if target.is_locked else "secondary-button",
        )

    def build_connector_ui(self) -> None:
        """接続線用のUI構築。"""
        target = self.current_target
        layout = self.create_collapsible_group(tr("prop_grp_connection"), expanded=True)

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
            (tr("line_style_solid"), Qt.PenStyle.SolidLine),
            (tr("line_style_dash"), Qt.PenStyle.DashLine),
            (tr("line_style_dot"), Qt.PenStyle.DotLine),
        ]
        self.add_combo(layout, tr("menu_line_style"), target.pen_style, styles, lambda v: target.set_line_style(v))

        arrows = [
            (tr("arrow_none"), ArrowStyle.NONE),
            (tr("arrow_end"), ArrowStyle.END),
            (tr("arrow_start"), ArrowStyle.START),
            (tr("arrow_both"), ArrowStyle.BOTH),
        ]
        self.add_combo(layout, tr("prop_arrow"), target.arrow_style, arrows, lambda v: target.set_arrow_style(v))

        if hasattr(target, "label_window") and target.label_window:
            self.add_text_edit(
                layout, tr("label_text"), target.label_window.text, lambda v: target.label_window.set_text(v)
            )

        if hasattr(target, "label_window") and target.label_window:
            btn = self.create_action_button(
                tr("menu_select_text_window"), lambda: self.set_target(target.label_window), "secondary-button"
            )
            layout.addRow("", btn)

        # Delete Button (Danger)
        del_btn = self.create_action_button(
            tr("menu_delete_line"), lambda: target.delete_line() or self.set_target(None), "danger-button"
        )
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
            mw = self.mw
            if mw is not None and hasattr(mw, "is_property_panel_active"):
                try:
                    mw.is_property_panel_active = False
                except Exception:
                    pass

                # トグルボタン群もOFFへ（各タブの同期メソッド経由）
                for tab_name in ["general_tab", "text_tab", "image_tab"]:
                    tab = getattr(mw, tab_name, None)
                    if tab is not None and hasattr(tab, "update_prop_button_state"):
                        tab.update_prop_button_state(False)

                # 見た目更新
                if hasattr(mw, "update_prop_button_style"):
                    mw.update_prop_button_style()
        except Exception:
            pass

        event.accept()
