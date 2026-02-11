from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.action_priority_helper import ActionPriorityHelper
from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class AnimationTab(QWidget):
    """アニメーション管理タブ。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window
        self._is_compact_mode = False
        self._compact_label_entries: list[tuple[Any, str, str]] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- Target (Compressed) ---
        self.anim_target_group = QGroupBox(tr("grp_anim_target"))
        # Using HBox to save vertical space
        target_layout = QHBoxLayout(self.anim_target_group)
        target_layout.setContentsMargins(10, 10, 10, 10)

        self.anim_label_apply_to = QLabel(tr("label_anim_apply_to"))
        self.anim_target_combo = QComboBox()
        self.anim_target_combo.addItems(
            [
                tr("anim_target_selected"),
                tr("anim_target_all_text"),
                tr("anim_target_all_image"),
                tr("anim_target_all_windows"),
            ]
        )
        self.anim_target_combo.currentIndexChanged.connect(self.refresh_enabled_state)

        self.anim_selected_label = QLabel(tr("label_anim_selected_none"))
        # self.anim_selected_label.setProperty("class", "dim") # QSS might conflict
        self.anim_selected_label.setProperty("class", "info-label")  # Consistent style
        self.anim_selected_label.setWordWrap(True)

        # Layout: [Label] [Combo] [Selected Label (Stretch)]
        target_layout.addWidget(self.anim_label_apply_to)
        target_layout.addWidget(self.anim_target_combo)
        target_layout.addWidget(self.anim_selected_label, 1)

        layout.addWidget(self.anim_target_group)

        # --- Sub Tabs ---
        self.anim_subtabs = QTabWidget()

        easing_names = [
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

        # =========================================================
        # 1. Absolute Move Tab (絶対移動)
        # =========================================================
        self.abs_page = QWidget()
        abs_page_layout = QVBoxLayout(self.abs_page)

        self.anim_abs_group = QGroupBox(tr("menu_absolute_move"))
        abs_layout = QGridLayout(self.anim_abs_group)

        self.anim_btn_abs_start = QPushButton(tr("menu_record_absolute_start"))
        self.anim_btn_abs_start.setObjectName("ActionBtn")
        self.anim_btn_abs_start.clicked.connect(
            lambda: (
                getattr(self.mw.last_selected_window, "record_absolute_start_pos")()
                if hasattr(self.mw.last_selected_window, "record_absolute_start_pos")
                else None
            )
        )

        self.anim_btn_abs_end = QPushButton(tr("menu_record_absolute_end"))
        self.anim_btn_abs_end.setObjectName("ActionBtn")
        self.anim_btn_abs_end.clicked.connect(
            lambda: (
                getattr(self.mw.last_selected_window, "record_absolute_end_pos")()
                if hasattr(self.mw.last_selected_window, "record_absolute_end_pos")
                else None
            )
        )

        self.anim_btn_abs_clear = QPushButton(tr("menu_clear_absolute_settings"))
        self.anim_btn_abs_clear.clicked.connect(self.mw.animation_manager.clear_abs_settings)

        abs_layout.addWidget(self.anim_btn_abs_start, 0, 0)
        abs_layout.addWidget(self.anim_btn_abs_end, 0, 1)
        abs_layout.addWidget(self.anim_btn_abs_clear, 1, 0, 1, 2)

        # Smart Pairing: Speed & Pause in one row
        self.anim_abs_move_speed = QSpinBox()
        self.anim_abs_move_speed.setRange(10, 100000)
        self.anim_abs_move_pause = QSpinBox()
        self.anim_abs_move_pause.setRange(0, 10000)

        speed_pause_layout = QHBoxLayout()
        self.anim_label_abs_speed = QLabel(tr("label_move_speed"))
        self.anim_label_abs_pause = QLabel(tr("label_pause_time"))

        speed_pause_layout.addWidget(self.anim_label_abs_speed)
        speed_pause_layout.addWidget(self.anim_abs_move_speed)
        speed_pause_layout.addWidget(self.anim_label_abs_pause)
        speed_pause_layout.addWidget(self.anim_abs_move_pause)

        # Add the nested layout to the grid
        abs_layout.addLayout(speed_pause_layout, 2, 0, 1, 2)

        self.anim_abs_easing_combo = QComboBox()
        self.anim_abs_easing_combo.addItems(easing_names)
        self.anim_label_abs_easing = QLabel(tr("label_easing"))

        abs_layout.addWidget(self.anim_label_abs_easing, 3, 0)
        abs_layout.addWidget(self.anim_abs_easing_combo, 3, 1)

        self.anim_btn_apply_abs_params = QPushButton(tr("btn_anim_apply_move_params"))
        self.anim_btn_apply_abs_params.setObjectName("ActionBtn")
        self.anim_btn_apply_abs_params.clicked.connect(self.mw.animation_manager.apply_abs_params)

        abs_layout.addWidget(self.anim_btn_apply_abs_params, 4, 0, 1, 2)

        self.anim_btn_abs_pingpong = QPushButton(tr("menu_absolute_move_pingpong"))
        self.anim_btn_abs_pingpong.setCheckable(True)
        self.anim_btn_abs_pingpong.clicked.connect(
            lambda: self.mw.animation_manager.toggle_pingpong(self.anim_btn_abs_pingpong.isChecked(), mode="absolute")
        )

        self.anim_btn_abs_oneway = QPushButton(tr("menu_absolute_move_oneway"))
        self.anim_btn_abs_oneway.setCheckable(True)
        self.anim_btn_abs_oneway.clicked.connect(
            lambda: self.mw.animation_manager.toggle_oneway(self.anim_btn_abs_oneway.isChecked(), mode="absolute")
        )

        self.anim_btn_abs_stop = QPushButton(tr("btn_anim_stop_move"))
        self.anim_btn_abs_stop.setObjectName("DangerBtn")
        self.anim_btn_abs_stop.clicked.connect(self.mw.animation_manager.stop_move)

        abs_layout.addWidget(self.anim_btn_abs_pingpong, 5, 0)
        abs_layout.addWidget(self.anim_btn_abs_oneway, 5, 1)
        abs_layout.addWidget(self.anim_btn_abs_stop, 6, 0, 1, 2)

        abs_page_layout.addWidget(self.anim_abs_group)
        abs_page_layout.addStretch()

        self.anim_subtabs.addTab(self.abs_page, tr("menu_absolute_move"))

        # =========================================================
        # 2. Relative Move Tab (相対移動)
        # =========================================================
        self.rel_page = QWidget()
        rel_page_layout = QVBoxLayout(self.rel_page)

        self.anim_rel_group = QGroupBox(tr("menu_relative_move"))
        rel_layout = QGridLayout(self.anim_rel_group)

        self.anim_dx = QSpinBox()
        self.anim_dx.setRange(-99999, 99999)

        self.anim_dy = QSpinBox()
        self.anim_dy.setRange(-99999, 99999)

        self.anim_btn_apply_offset = QPushButton(tr("btn_anim_apply_offset"))
        self.anim_btn_apply_offset.setObjectName("ActionBtn")
        self.anim_btn_apply_offset.clicked.connect(self.mw.animation_manager.apply_offset)

        self.anim_btn_record_base = QPushButton(tr("menu_record_relative_move_base"))
        self.anim_btn_record_base.setObjectName("ActionBtn")
        self.anim_btn_record_base.clicked.connect(self.mw.animation_manager.record_base)

        self.anim_btn_record_end = QPushButton(tr("menu_record_relative_move_end"))
        self.anim_btn_record_end.setObjectName("ActionBtn")
        self.anim_btn_record_end.clicked.connect(self.mw.animation_manager.record_end)

        self.anim_btn_clear_offset = QPushButton(tr("menu_clear_relative_move_offset"))
        self.anim_btn_clear_offset.clicked.connect(self.mw.animation_manager.clear_offset)

        self.anim_base_status = QLabel(tr("status_anim_base_not_recorded"))
        self.anim_base_status.setProperty("class", "dim small")

        rel_layout.addWidget(QLabel("dx"), 0, 0)
        rel_layout.addWidget(self.anim_dx, 0, 1)
        rel_layout.addWidget(QLabel("dy"), 0, 2)
        rel_layout.addWidget(self.anim_dy, 0, 3)

        rel_layout.addWidget(self.anim_btn_apply_offset, 1, 0, 1, 4)

        rel_layout.addWidget(self.anim_btn_record_base, 2, 0, 1, 2)
        rel_layout.addWidget(self.anim_btn_record_end, 2, 2, 1, 2)

        rel_layout.addWidget(self.anim_btn_clear_offset, 3, 0, 1, 4)
        rel_layout.addWidget(self.anim_base_status, 4, 0, 1, 4)

        # Smart Pairing: Speed & Pause
        self.anim_move_speed = QSpinBox()
        self.anim_move_speed.setRange(10, 100000)
        self.anim_move_pause = QSpinBox()
        self.anim_move_pause.setRange(0, 10000)

        rel_speed_pause_layout = QHBoxLayout()
        self.anim_label_move_speed = QLabel(tr("label_move_speed"))
        self.anim_label_move_pause = QLabel(tr("label_pause_time"))

        rel_speed_pause_layout.addWidget(self.anim_label_move_speed)
        rel_speed_pause_layout.addWidget(self.anim_move_speed)
        rel_speed_pause_layout.addWidget(self.anim_label_move_pause)
        rel_speed_pause_layout.addWidget(self.anim_move_pause)

        rel_layout.addLayout(rel_speed_pause_layout, 5, 0, 1, 4)

        self.anim_move_easing_combo = QComboBox()
        self.anim_move_easing_combo.addItems(easing_names)
        self.anim_label_move_easing = QLabel(tr("label_easing"))

        rel_layout.addWidget(self.anim_label_move_easing, 6, 0, 1, 2)
        rel_layout.addWidget(self.anim_move_easing_combo, 6, 2, 1, 2)

        self.anim_btn_apply_move_params = QPushButton(tr("btn_anim_apply_move_params"))
        self.anim_btn_apply_move_params.setObjectName("ActionBtn")
        self.anim_btn_apply_move_params.clicked.connect(self.mw.animation_manager.apply_move_params)

        rel_layout.addWidget(self.anim_btn_apply_move_params, 7, 0, 1, 4)

        self.anim_btn_pingpong = QPushButton(tr("menu_relative_move_pingpong"))
        self.anim_btn_pingpong.setCheckable(True)
        self.anim_btn_pingpong.clicked.connect(
            lambda: self.mw.animation_manager.toggle_pingpong(self.anim_btn_pingpong.isChecked(), mode="relative")
        )

        self.anim_btn_oneway = QPushButton(tr("menu_relative_move_oneway"))
        self.anim_btn_oneway.setCheckable(True)
        self.anim_btn_oneway.clicked.connect(
            lambda: self.mw.animation_manager.toggle_oneway(self.anim_btn_oneway.isChecked(), mode="relative")
        )

        self.anim_btn_stop_move = QPushButton(tr("btn_anim_stop_move"))
        self.anim_btn_stop_move.setObjectName("DangerBtn")
        self.anim_btn_stop_move.clicked.connect(self.mw.animation_manager.stop_move)

        rel_layout.addWidget(self.anim_btn_pingpong, 8, 0, 1, 2)
        rel_layout.addWidget(self.anim_btn_oneway, 8, 2, 1, 2)
        rel_layout.addWidget(self.anim_btn_stop_move, 9, 0, 1, 4)

        rel_page_layout.addWidget(self.anim_rel_group)
        rel_page_layout.addStretch()

        self.anim_subtabs.addTab(self.rel_page, tr("menu_relative_move"))

        # =========================================================
        # 3. Fade Tab
        # =========================================================
        self.fade_page = QWidget()
        fade_page_layout = QVBoxLayout(self.fade_page)

        self.anim_fade_group = QGroupBox(tr("menu_anim_fade"))
        fade_layout = QGridLayout(self.anim_fade_group)

        # Smart Pairing: Speed & Pause
        self.anim_fade_speed = QSpinBox()
        self.anim_fade_speed.setRange(100, 100000)
        self.anim_fade_pause = QSpinBox()
        self.anim_fade_pause.setRange(0, 10000)

        fade_speed_pause_layout = QHBoxLayout()
        self.anim_label_fade_speed = QLabel(tr("label_fade_speed"))
        self.anim_label_fade_pause = QLabel(tr("label_pause_time"))

        fade_speed_pause_layout.addWidget(self.anim_label_fade_speed)
        fade_speed_pause_layout.addWidget(self.anim_fade_speed)
        fade_speed_pause_layout.addWidget(self.anim_label_fade_pause)
        fade_speed_pause_layout.addWidget(self.anim_fade_pause)

        fade_layout.addLayout(fade_speed_pause_layout, 0, 0, 1, 4)

        self.anim_fade_easing_combo = QComboBox()
        self.anim_fade_easing_combo.addItems(easing_names)
        self.anim_label_fade_easing = QLabel(tr("label_easing"))

        fade_layout.addWidget(self.anim_label_fade_easing, 1, 0, 1, 2)
        fade_layout.addWidget(self.anim_fade_easing_combo, 1, 2, 1, 2)

        self.anim_btn_apply_fade_params = QPushButton(tr("btn_anim_apply_fade_params"))
        self.anim_btn_apply_fade_params.setObjectName("ActionBtn")
        self.anim_btn_apply_fade_params.clicked.connect(self.mw.animation_manager.apply_fade_params)

        fade_layout.addWidget(self.anim_btn_apply_fade_params, 2, 0, 1, 4)

        self.anim_btn_fade_in_out = QPushButton(tr("menu_toggle_fade_in_out"))
        self.anim_btn_fade_in_out.setCheckable(True)
        self.anim_btn_fade_in_out.clicked.connect(self.mw.animation_manager.toggle_fade_in_out)

        self.anim_btn_fade_in_only = QPushButton(tr("menu_toggle_fade_in_loop"))
        self.anim_btn_fade_in_only.setCheckable(True)
        self.anim_btn_fade_in_only.clicked.connect(self.mw.animation_manager.toggle_fade_in_only)

        self.anim_btn_fade_out_only = QPushButton(tr("menu_toggle_fade_out_loop"))
        self.anim_btn_fade_out_only.setCheckable(True)
        self.anim_btn_fade_out_only.clicked.connect(self.mw.animation_manager.toggle_fade_out_only)

        self.anim_btn_stop_fade = QPushButton(tr("btn_anim_stop_fade"))
        self.anim_btn_stop_fade.setObjectName("DangerBtn")
        self.anim_btn_stop_fade.clicked.connect(self.mw.animation_manager.stop_fade)

        fade_layout.addWidget(self.anim_btn_fade_in_out, 3, 0, 1, 4)
        fade_layout.addWidget(self.anim_btn_fade_in_only, 4, 0, 1, 4)
        fade_layout.addWidget(self.anim_btn_fade_out_only, 5, 0, 1, 4)
        fade_layout.addWidget(self.anim_btn_stop_fade, 6, 0, 1, 4)

        fade_page_layout.addWidget(self.anim_fade_group)
        fade_page_layout.addStretch()

        self.anim_subtabs.addTab(self.fade_page, tr("menu_anim_fade"))

        # =========================================================
        # Stop All Animations
        # =========================================================
        self.btn_stop_all = QPushButton(tr("btn_stop_all_anim"))
        self.btn_stop_all.setObjectName("DangerBtn")
        self.btn_stop_all.clicked.connect(self.mw.animation_manager.stop_all_animations)

        self.btn_stop_all.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_stop_all.setMinimumHeight(45)
        self._init_priority_action_menu()
        self._register_context_menu_paths()

        self.anim_scroll_area = QScrollArea()
        self.anim_scroll_area.setWidgetResizable(True)
        self.anim_scroll_area.setObjectName("AnimationTabScrollArea")
        self.anim_scroll_content = QWidget()
        scroll_layout = QVBoxLayout(self.anim_scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(4)
        scroll_layout.addWidget(self.anim_subtabs)
        self.anim_scroll_area.setWidget(self.anim_scroll_content)
        layout.addWidget(self.anim_scroll_area, 1)

        self._compact_label_entries = self._build_compact_label_entries()
        ActionPriorityHelper.mark_compact_actions(self._compact_label_entries)
        # 初期状態更新
        self.set_compact_mode(False)
        self.refresh_enabled_state()

    def _init_priority_action_menu(self) -> None:
        self.menu_priority_actions = QMenu(self)

        self.act_anim_stop_all = QAction("", self)
        self.act_anim_stop_all.triggered.connect(self.mw.animation_manager.stop_all_animations)
        self.menu_priority_actions.addAction(self.act_anim_stop_all)

        self.act_anim_stop_move = QAction("", self)
        self.act_anim_stop_move.triggered.connect(self.mw.animation_manager.stop_move)
        self.menu_priority_actions.addAction(self.act_anim_stop_move)

        self.act_anim_stop_fade = QAction("", self)
        self.act_anim_stop_fade.triggered.connect(self.mw.animation_manager.stop_fade)
        self.menu_priority_actions.addAction(self.act_anim_stop_fade)

        self.btn_anim_priority_menu = QToolButton(self)
        self.btn_anim_priority_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_anim_priority_menu.setMenu(self.menu_priority_actions)
        self.anim_subtabs.setCornerWidget(self.btn_anim_priority_menu, Qt.Corner.TopRightCorner)
        self._refresh_priority_action_texts()

    def _register_context_menu_paths(self) -> None:
        self.anim_subtabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.anim_subtabs.customContextMenuRequested.connect(
            lambda pos: self._show_priority_menu_global(self.anim_subtabs.mapToGlobal(pos))
        )
        self.anim_selected_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.anim_selected_label.customContextMenuRequested.connect(
            lambda pos: self._show_priority_menu_global(self.anim_selected_label.mapToGlobal(pos))
        )

    def _show_priority_menu_global(self, global_pos: Any) -> None:
        self.menu_priority_actions.exec(global_pos)

    def _refresh_priority_action_texts(self) -> None:
        self.act_anim_stop_all.setText(tr("btn_stop_all_anim"))
        self.act_anim_stop_move.setText(tr("btn_anim_stop_move"))
        self.act_anim_stop_fade.setText(tr("btn_anim_stop_fade"))
        self.btn_anim_priority_menu.setText(tr("anim_priority_actions"))
        self.btn_anim_priority_menu.setToolTip(tr("anim_priority_actions_tooltip"))

    def _build_compact_label_entries(self) -> list[tuple[Any, str, str]]:
        return [
            (
                self.anim_btn_record_base,
                tr("menu_record_relative_move_base"),
                tr("menu_record_relative_move_base_short"),
            ),
            (self.anim_btn_record_end, tr("menu_record_relative_move_end"), tr("menu_record_relative_move_end_short")),
            (
                self.anim_btn_clear_offset,
                tr("menu_clear_relative_move_offset"),
                tr("menu_clear_relative_move_offset_short"),
            ),
            (self.anim_btn_abs_start, tr("menu_record_absolute_start"), tr("menu_record_absolute_start_short")),
            (self.anim_btn_abs_end, tr("menu_record_absolute_end"), tr("menu_record_absolute_end_short")),
            (
                self.anim_btn_abs_clear,
                tr("menu_clear_absolute_settings"),
                tr("menu_clear_absolute_settings_short"),
            ),
            (self.anim_btn_apply_move_params, tr("btn_anim_apply_move_params"), tr("btn_anim_apply_move_params_short")),
            (self.anim_btn_apply_fade_params, tr("btn_anim_apply_fade_params"), tr("btn_anim_apply_fade_params_short")),
            (self.anim_btn_fade_in_only, tr("menu_toggle_fade_in_loop"), tr("menu_toggle_fade_in_loop_short")),
            (self.anim_btn_fade_out_only, tr("menu_toggle_fade_out_loop"), tr("menu_toggle_fade_out_loop_short")),
        ]

    def _apply_compact_labels(self) -> None:
        ActionPriorityHelper.apply_label_mode(self._compact_label_entries, self._is_compact_mode)
        self._refresh_priority_action_texts()

    def on_selection_changed(self, window: Optional[Any]) -> None:
        """選択変更時のUI更新"""
        if window is None:
            self.anim_selected_label.setText(tr("label_anim_selected_none"))
        else:
            name = type(window).__name__
            try:
                self.anim_selected_label.setText(tr("label_anim_selected_fmt").format(name=name))
            except Exception:
                self.anim_selected_label.setText(f"Selected: {name}")

        self.mw.animation_manager.sync_from_selected(window)
        self.refresh_enabled_state()

    def refresh_enabled_state(self) -> None:
        """Target/Selected状態に応じて有効・無効を切り替える。"""
        is_selected_target = self.anim_target_combo.currentIndex() == 0
        has_selected = getattr(self.mw, "last_selected_window", None) is not None

        # Record系は Selected にのみ許可
        enable_record = is_selected_target and has_selected

        # Apply/Play/Stop は Selected無しなら無効（All系ならOK）
        enable_actions = (not is_selected_target) or has_selected

        # Relative
        self.anim_btn_record_base.setEnabled(enable_record)
        self.anim_btn_record_end.setEnabled(enable_record)
        self.anim_btn_apply_offset.setEnabled(enable_actions)
        self.anim_btn_clear_offset.setEnabled(enable_actions)
        self.anim_btn_apply_move_params.setEnabled(enable_actions)
        self.anim_btn_pingpong.setEnabled(enable_actions)
        self.anim_btn_oneway.setEnabled(enable_actions)
        self.anim_btn_stop_move.setEnabled(enable_actions)

        self.anim_move_speed.setEnabled(enable_actions)
        self.anim_move_pause.setEnabled(enable_actions)
        self.anim_move_easing_combo.setEnabled(enable_actions)

        # Absolute
        self.anim_btn_abs_start.setEnabled(enable_record)
        self.anim_btn_abs_end.setEnabled(enable_record)
        self.anim_btn_abs_clear.setEnabled(enable_actions)
        self.anim_btn_apply_abs_params.setEnabled(enable_actions)
        self.anim_btn_abs_pingpong.setEnabled(enable_actions)
        self.anim_btn_abs_oneway.setEnabled(enable_actions)
        self.anim_btn_abs_stop.setEnabled(enable_actions)

        self.anim_abs_move_speed.setEnabled(enable_actions)
        self.anim_abs_move_pause.setEnabled(enable_actions)
        self.anim_abs_easing_combo.setEnabled(enable_actions)

        # Fade
        self.anim_btn_apply_fade_params.setEnabled(enable_actions)
        self.anim_btn_fade_in_out.setEnabled(enable_actions)
        self.anim_btn_fade_in_only.setEnabled(enable_actions)
        self.anim_btn_fade_out_only.setEnabled(enable_actions)
        self.anim_btn_stop_fade.setEnabled(enable_actions)

        self.anim_fade_speed.setEnabled(enable_actions)
        self.anim_fade_pause.setEnabled(enable_actions)
        self.anim_fade_easing_combo.setEnabled(enable_actions)
        if hasattr(self, "act_anim_stop_move"):
            self.act_anim_stop_move.setEnabled(enable_actions)
        if hasattr(self, "act_anim_stop_fade"):
            self.act_anim_stop_fade.setEnabled(enable_actions)

    def refresh_ui(self) -> None:
        """UI文言更新"""
        self.anim_target_group.setTitle(tr("grp_anim_target"))

        # サブタブ名（index決め打ち）
        if self.anim_subtabs.count() >= 1:
            self.anim_subtabs.setTabText(0, tr("menu_absolute_move"))
        if self.anim_subtabs.count() >= 2:
            self.anim_subtabs.setTabText(1, tr("menu_relative_move"))
        if self.anim_subtabs.count() >= 3:
            self.anim_subtabs.setTabText(2, tr("menu_anim_fade"))

        # Absolute
        self.anim_abs_group.setTitle(tr("menu_absolute_move"))
        self.anim_btn_abs_start.setText(tr("menu_record_absolute_start"))
        self.anim_btn_abs_end.setText(tr("menu_record_absolute_end"))
        self.anim_btn_abs_clear.setText(tr("menu_clear_absolute_settings"))
        self.anim_btn_apply_abs_params.setText(tr("btn_anim_apply_move_params"))
        self.anim_btn_abs_pingpong.setText(tr("menu_absolute_move_pingpong"))
        self.anim_btn_abs_oneway.setText(tr("menu_absolute_move_oneway"))
        self.anim_btn_abs_stop.setText(tr("btn_anim_stop_move"))

        self.anim_label_abs_speed.setText(tr("label_move_speed"))
        self.anim_label_abs_pause.setText(tr("label_pause_time"))
        self.anim_label_abs_easing.setText(tr("label_easing"))

        # Relative
        self.anim_rel_group.setTitle(tr("menu_relative_move"))
        self.anim_btn_apply_offset.setText(tr("btn_anim_apply_offset"))
        self.anim_btn_record_base.setText(tr("menu_record_relative_move_base"))
        self.anim_btn_record_end.setText(tr("menu_record_relative_move_end"))
        self.anim_btn_clear_offset.setText(tr("menu_clear_relative_move_offset"))

        self.anim_label_move_speed.setText(tr("label_move_speed"))
        self.anim_label_move_pause.setText(tr("label_pause_time"))
        self.anim_label_move_easing.setText(tr("label_easing"))

        self.anim_btn_apply_move_params.setText(tr("btn_anim_apply_move_params"))
        self.anim_btn_pingpong.setText(tr("menu_relative_move_pingpong"))
        self.anim_btn_oneway.setText(tr("menu_relative_move_oneway"))
        self.anim_btn_stop_move.setText(tr("btn_anim_stop_move"))

        # Fade
        self.anim_fade_group.setTitle(tr("menu_anim_fade"))
        self.anim_label_fade_speed.setText(tr("label_fade_speed"))
        self.anim_label_fade_pause.setText(tr("label_pause_time"))
        self.anim_label_fade_easing.setText(tr("label_easing"))

        self.anim_btn_apply_fade_params.setText(tr("btn_anim_apply_fade_params"))
        self.anim_btn_fade_in_out.setText(tr("menu_toggle_fade_in_out"))
        self.anim_btn_fade_in_only.setText(tr("menu_toggle_fade_in_loop"))
        self.anim_btn_fade_out_only.setText(tr("menu_toggle_fade_out_loop"))
        self.anim_btn_stop_fade.setText(tr("btn_anim_stop_fade"))

        self.btn_stop_all.setText(tr("btn_stop_all_anim"))

        self.anim_label_apply_to.setText(tr("label_anim_apply_to"))

        # Combo
        cur = self.anim_target_combo.currentIndex()
        self.anim_target_combo.blockSignals(True)
        self.anim_target_combo.clear()
        self.anim_target_combo.addItems(
            [
                tr("anim_target_selected"),
                tr("anim_target_all_text"),
                tr("anim_target_all_image"),
                tr("anim_target_all_windows"),
            ]
        )
        if self.anim_target_combo.count() > 0:
            self.anim_target_combo.setCurrentIndex(max(0, min(cur, self.anim_target_combo.count() - 1)))
        self.anim_target_combo.blockSignals(False)
        self._compact_label_entries = self._build_compact_label_entries()
        ActionPriorityHelper.mark_compact_actions(self._compact_label_entries)
        self._apply_compact_labels()

    def set_compact_mode(self, enabled: bool) -> None:
        self._is_compact_mode = bool(enabled)
        self.btn_stop_all.setMinimumHeight(36 if enabled else 45)
        self._apply_compact_labels()
