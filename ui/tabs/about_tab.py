from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import CollapsibleBox
from utils.translator import tr


class AboutTab(QWidget):
    """情報（About）タブ。"""

    _SECTION_DEFAULTS = {
        "edition": True,
        "system": True,
        "shortcuts": False,
        "performance": False,
    }

    def __init__(self, main_window: Any):
        super().__init__()
        self.mw = main_window
        self._section_boxes: dict[str, CollapsibleBox] = {}
        self._section_state: dict[str, bool] = dict(self._SECTION_DEFAULTS)
        self._manual_expand_overrides: set[str] = set()
        self._compact_enabled = False
        self._applied_compact_state: bool | None = None
        self._suspend_section_events = True
        self._setup_ui()
        self._load_section_state_from_settings()
        self._suspend_section_events = False
        self._apply_compact_mode(force=True)

    def _setup_ui(self) -> None:
        self.setObjectName("AboutTabRoot")
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.root_layout.setSpacing(4)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.root_layout.addWidget(self.scroll_area, 1)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("AboutTabContent")
        self.scroll_area.setWidget(self.scroll_content)

        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)

        self.quick_actions_row = QWidget()
        self.quick_actions_row.setObjectName("AboutQuickActions")
        self.quick_actions_layout = QHBoxLayout(self.quick_actions_row)
        self.quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_actions_layout.setSpacing(4)

        self.btn_manual = QPushButton(tr("btn_manual"))
        self.btn_manual.setObjectName("ActionBtn")
        self.btn_manual.clicked.connect(self.mw.show_manual_dialog)
        self.quick_actions_layout.addWidget(self.btn_manual)

        self.btn_license = QPushButton(tr("btn_license"))
        self.btn_license.setObjectName("ActionBtn")
        self.btn_license.clicked.connect(self.mw.show_license_dialog)
        self.quick_actions_layout.addWidget(self.btn_license)

        self.btn_show_about = QPushButton(tr("btn_show_about_dialog"))
        self.btn_show_about.setObjectName("ActionBtn")
        self.btn_show_about.clicked.connect(self.mw.show_about_dialog)
        self.quick_actions_layout.addWidget(self.btn_show_about)

        self.quick_actions_layout.addStretch(1)

        # Compatibility buttons: keep existing references and signal wiring.
        self.btn_open_log = QPushButton(tr("btn_open_log_folder"))
        self.btn_open_log.setObjectName("ActionBtn")
        self.btn_open_log.clicked.connect(self.mw.open_log_folder)

        self.btn_open_shop = QPushButton(tr("btn_open_shop"))
        self.btn_open_shop.setObjectName("ActionBtn")
        self.btn_open_shop.clicked.connect(self.mw.open_shop_page)

        self.btn_copy_shop_url = QPushButton(tr("btn_copy_url"))
        self.btn_copy_shop_url.setObjectName("ActionBtn")
        self.btn_copy_shop_url.clicked.connect(self.mw.copy_shop_url)

        self.btn_more_actions = QToolButton()
        self.btn_more_actions.setObjectName("ActionBtn")
        self.btn_more_actions.setText(tr("about_more_actions"))
        self.btn_more_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_more_actions = QMenu(self.btn_more_actions)
        self.act_open_log = QAction(tr("btn_open_log_folder"), self)
        self.act_open_log.triggered.connect(self.btn_open_log.click)
        self.menu_more_actions.addAction(self.act_open_log)
        self.act_open_shop = QAction(tr("btn_open_shop"), self)
        self.act_open_shop.triggered.connect(self.btn_open_shop.click)
        self.menu_more_actions.addAction(self.act_open_shop)
        self.act_copy_shop_url = QAction(tr("btn_copy_url"), self)
        self.act_copy_shop_url.triggered.connect(self.btn_copy_shop_url.click)
        self.menu_more_actions.addAction(self.act_copy_shop_url)
        self.btn_more_actions.setMenu(self.menu_more_actions)
        self.quick_actions_layout.addWidget(self.btn_more_actions)

        self.content_layout.addWidget(self.quick_actions_row)

        self.edition_group = self._create_section_box("edition", tr("grp_edition"), True)
        edition_layout = QVBoxLayout()
        edition_layout.setContentsMargins(4, 4, 4, 4)
        edition_layout.setSpacing(4)
        self.label_current_edition = QLabel(tr("label_current_edition").format(edition="STANDARD"))
        self.label_current_edition.setProperty("class", "edition-label")
        edition_layout.addWidget(self.label_current_edition)
        self.edition_group.setContentLayout(edition_layout)
        self.content_layout.addWidget(self.edition_group)

        self.system_group = self._create_section_box("system", tr("grp_system_info"), True)
        system_layout = QVBoxLayout()
        system_layout.setContentsMargins(4, 4, 4, 4)
        system_layout.setSpacing(4)
        self.label_system_summary = QLabel(tr("about_system_summary"))
        self.label_system_summary.setWordWrap(True)
        self.label_system_summary.setProperty("class", "about-hint")
        system_layout.addWidget(self.label_system_summary)
        self.system_group.setContentLayout(system_layout)
        self.content_layout.addWidget(self.system_group)

        self.shortcuts_group = self._create_section_box("shortcuts", tr("grp_shortcuts"), False)
        shortcuts_layout = QVBoxLayout()
        shortcuts_layout.setContentsMargins(4, 4, 4, 4)
        shortcuts_layout.setSpacing(4)
        self.label_shortcuts = QLabel(tr("label_rescue_shortcuts"))
        self.label_shortcuts.setProperty("class", "monospace-label")
        self.label_shortcuts.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        shortcuts_layout.addWidget(self.label_shortcuts)
        self.shortcuts_group.setContentLayout(shortcuts_layout)
        self.content_layout.addWidget(self.shortcuts_group)

        self.perf_group = self._create_section_box("performance", tr("grp_performance"), False)
        perf_layout = QGridLayout()
        perf_layout.setContentsMargins(4, 4, 4, 4)
        perf_layout.setHorizontalSpacing(6)
        perf_layout.setVerticalSpacing(4)

        cur_debounce = getattr(self.mw.app_settings, "render_debounce_ms", 50)
        cur_wheel = getattr(self.mw.app_settings, "wheel_debounce_ms", 80)
        cur_cache = getattr(self.mw.app_settings, "glyph_cache_size", 512)

        self.label_debounce = QLabel(tr("label_debounce"))
        self.spin_debounce = QSpinBox()
        self.spin_debounce.setRange(0, 500)
        self.spin_debounce.setSingleStep(10)
        self.spin_debounce.setValue(int(cur_debounce))

        self.hint_debounce = QLabel(tr("hint_debounce"))
        self.hint_debounce.setProperty("class", "about-hint")
        self.hint_debounce.setWordWrap(True)

        self.label_wheel = QLabel(tr("label_wheel_debounce"))
        self.spin_wheel = QSpinBox()
        self.spin_wheel.setRange(0, 500)
        self.spin_wheel.setSingleStep(10)
        self.spin_wheel.setValue(int(cur_wheel))

        self.hint_wheel = QLabel(tr("hint_wheel_debounce"))
        self.hint_wheel.setProperty("class", "about-hint")
        self.hint_wheel.setWordWrap(True)

        self.label_cache = QLabel(tr("label_cache"))
        self.spin_cache = QSpinBox()
        self.spin_cache.setRange(0, 4096)
        self.spin_cache.setSingleStep(128)
        self.spin_cache.setValue(int(cur_cache))

        self.hint_cache = QLabel(tr("hint_cache"))
        self.hint_cache.setProperty("class", "about-hint")
        self.hint_cache.setWordWrap(True)

        self.btn_apply_perf = QPushButton(tr("btn_apply_perf"))
        self.btn_apply_perf.setObjectName("ActionBtn")
        self.btn_apply_perf.clicked.connect(self._apply_perf)

        perf_layout.addWidget(self.label_debounce, 0, 0)
        perf_layout.addWidget(self.spin_debounce, 0, 1)
        perf_layout.addWidget(self.hint_debounce, 1, 0, 1, 2)

        perf_layout.addWidget(self.label_wheel, 2, 0)
        perf_layout.addWidget(self.spin_wheel, 2, 1)
        perf_layout.addWidget(self.hint_wheel, 3, 0, 1, 2)

        perf_layout.addWidget(self.label_cache, 4, 0)
        perf_layout.addWidget(self.spin_cache, 4, 1)
        perf_layout.addWidget(self.hint_cache, 5, 0, 1, 2)

        perf_layout.addWidget(self.btn_apply_perf, 6, 0, 1, 2)
        self.perf_group.setContentLayout(perf_layout)
        self.content_layout.addWidget(self.perf_group)

        self.content_layout.addStretch(1)

    def _create_section_box(self, key: str, title: str, expanded: bool) -> CollapsibleBox:
        box = CollapsibleBox(title)
        box.toggle_button.setChecked(bool(expanded))
        box.toggle_button.toggled.connect(
            lambda checked, section_key=key: self._on_section_toggled(section_key, bool(checked))
        )
        self._section_boxes[key] = box
        self._section_state[key] = bool(expanded)
        return box

    def _load_section_state_from_settings(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        raw = getattr(settings, "about_section_state", {}) if settings is not None else {}
        state = dict(self._SECTION_DEFAULTS)
        if isinstance(raw, dict):
            for key in state:
                if key in raw:
                    state[key] = bool(raw[key])
        self._section_state = state
        self._set_sections_from_state(state)

    def _set_sections_from_state(self, state: dict[str, bool]) -> None:
        self._suspend_section_events = True
        try:
            for key, box in self._section_boxes.items():
                checked = bool(state.get(key, self._SECTION_DEFAULTS.get(key, True)))
                if box.toggle_button.isChecked() != checked:
                    box.toggle_button.setChecked(checked)
        finally:
            self._suspend_section_events = False

    def _persist_section_state(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        settings_manager = getattr(self.mw, "settings_manager", None)
        if settings is None:
            return
        settings.about_section_state = dict(self._section_state)
        if settings_manager is not None and hasattr(settings_manager, "save_app_settings"):
            settings_manager.save_app_settings()

    def _on_section_toggled(self, key: str, checked: bool) -> None:
        self._section_state[key] = bool(checked)
        if key in {"shortcuts", "performance"}:
            if checked:
                self._manual_expand_overrides.add(key)
            else:
                self._manual_expand_overrides.discard(key)
        if self._suspend_section_events:
            return
        self._persist_section_state()

    def _apply_perf(self) -> None:
        d = self.spin_debounce.value()
        w = self.spin_wheel.value()
        c = self.spin_cache.value()
        if hasattr(self.mw, "apply_performance_settings"):
            self.mw.apply_performance_settings(d, w, c)

    def _apply_hint_visibility(self, visible: bool) -> None:
        hint_bindings = [
            (self.hint_debounce, self.spin_debounce, tr("hint_debounce")),
            (self.hint_wheel, self.spin_wheel, tr("hint_wheel_debounce")),
            (self.hint_cache, self.spin_cache, tr("hint_cache")),
        ]
        for hint_label, spin_widget, text in hint_bindings:
            hint_label.setVisible(visible)
            spin_widget.setToolTip("" if visible else text)

    def _apply_compact_mode(self, force: bool = False) -> None:
        compact = bool(self._compact_enabled)
        if not force and compact == self._applied_compact_state:
            return
        self._applied_compact_state = compact

        if compact:
            self.root_layout.setContentsMargins(2, 2, 2, 2)
        else:
            self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(3 if compact else 4)
        self.quick_actions_layout.setSpacing(3 if compact else 4)
        self._apply_hint_visibility(not compact)

        if compact:
            next_state = dict(self._section_state)
            for key in ("shortcuts", "performance"):
                if key not in self._manual_expand_overrides:
                    next_state[key] = False
            self._set_sections_from_state(next_state)
        else:
            self._set_sections_from_state(dict(self._section_state))

    def refresh_ui(self) -> None:
        self.btn_manual.setText(tr("btn_manual"))
        self.btn_license.setText(tr("btn_license"))
        self.btn_show_about.setText(tr("btn_show_about_dialog"))
        self.btn_more_actions.setText(tr("about_more_actions"))

        self.btn_open_log.setText(tr("btn_open_log_folder"))
        self.btn_open_shop.setText(tr("btn_open_shop"))
        self.btn_copy_shop_url.setText(tr("btn_copy_url"))
        self.act_open_log.setText(tr("btn_open_log_folder"))
        self.act_open_shop.setText(tr("btn_open_shop"))
        self.act_copy_shop_url.setText(tr("btn_copy_url"))

        self.edition_group.setText(tr("grp_edition"))
        self.system_group.setText(tr("grp_system_info"))
        self.shortcuts_group.setText(tr("grp_shortcuts"))
        self.perf_group.setText(tr("grp_performance"))

        self.label_current_edition.setText(tr("label_current_edition").format(edition="STANDARD"))
        self.label_system_summary.setText(tr("about_system_summary"))
        self.label_shortcuts.setText(tr("label_rescue_shortcuts"))

        self.label_debounce.setText(tr("label_debounce"))
        self.hint_debounce.setText(tr("hint_debounce"))
        self.label_wheel.setText(tr("label_wheel_debounce"))
        self.hint_wheel.setText(tr("hint_wheel_debounce"))
        self.label_cache.setText(tr("label_cache"))
        self.hint_cache.setText(tr("hint_cache"))
        self.btn_apply_perf.setText(tr("btn_apply_perf"))

        self._apply_hint_visibility(not self._compact_enabled)

    def set_compact_mode(self, enabled: bool) -> None:
        next_state = bool(enabled)
        if next_state == self._compact_enabled:
            return
        self._compact_enabled = next_state
        self._apply_compact_mode(force=True)
