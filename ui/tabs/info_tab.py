from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from managers.info_index_manager import InfoIndexManager, InfoQuery, InfoStats, NoteIndexItem, TaskIndexItem
from ui.dialogs import BulkTagEditDialog
from ui.widgets import CollapsibleBox
from utils.due_date import classify_due, format_due_for_display
from utils.translator import tr


@dataclass(frozen=True)
class ViewPreset:
    preset_id: str
    name: str
    filters: dict[str, Any]
    smart_view: str = "custom"


class InfoOperationsDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("info_recent_operations"))
        self.resize(560, 360)

        layout = QVBoxLayout(self)
        self.operations_list = QListWidget()
        self.operations_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.operations_list, 1)

        self.btn_clear = QPushButton(tr("info_clear_operations"))
        self.btn_clear.setObjectName("ActionBtn")
        self.btn_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btn_close.rejected.connect(self.reject)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addWidget(self.btn_clear)
        button_row.addStretch(1)
        button_row.addWidget(self.btn_close)
        layout.addLayout(button_row)

    def set_entries(self, entries: list[str]) -> None:
        self.operations_list.clear()
        if not entries:
            empty = QListWidgetItem(tr("info_operation_empty"))
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self.operations_list.addItem(empty)
            return
        for line in entries:
            self.operations_list.addItem(QListWidgetItem(str(line)))

    def refresh_ui(self) -> None:
        self.setWindowTitle(tr("info_recent_operations"))
        self.btn_clear.setText(tr("info_clear_operations"))


class InfoTab(QWidget):
    """タスク/ノートを横断表示する情報管理タブ。"""

    _DUE_FILTER_VALUES = ("all", "today", "overdue", "upcoming", "dated", "undated")
    _MODE_FILTER_VALUES = ("all", "task", "note")
    _ITEM_SCOPE_VALUES = ("all", "tasks", "notes")
    _ARCHIVE_SCOPE_VALUES = ("active", "archived", "all")
    _SORT_BY_VALUES = ("updated", "due", "created", "title")
    _SMART_VIEW_KEYS = ("all", "open", "today", "overdue", "starred", "archived")
    _LAYOUT_MODE_VALUES = ("auto", "compact", "regular")

    def __init__(self, main_window: Any):
        super().__init__()
        self.mw = main_window
        self.index_manager = InfoIndexManager()

        self._current_selected_uuid: str = ""
        self._is_refreshing = False
        self._smart_view = "all"
        self._smart_view_buttons: dict[str, QPushButton] = {}
        self._view_presets: dict[str, ViewPreset] = {}
        self._user_preset_ids: list[str] = []
        self._current_preset_id: str = "builtin:all"
        self._next_user_preset_number = 1
        self._block_filter_events = False
        self._block_preset_events = False
        self._block_smart_view_events = False
        self._block_layout_mode_events = False
        self._suspend_ui_state_persist = False
        self._layout_mode = "auto"
        self._effective_layout_mode = "regular"
        self._operations_dialog: Optional[InfoOperationsDialog] = None
        self._operation_log_lines: list[str] = []
        self._index_cache_signature: Optional[tuple[Any, ...]] = None
        self._index_cache_task_items: list[TaskIndexItem] = []
        self._index_cache_note_items: list[NoteIndexItem] = []
        self._last_task_rows_signature: Optional[tuple[Any, ...]] = None
        self._last_note_rows_signature: Optional[tuple[Any, ...]] = None
        self._last_operation_logs_signature: Optional[tuple[Any, ...]] = None

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._refresh_now)

        self._setup_ui()
        self._load_ui_state_from_settings()
        self._load_presets_from_settings()
        self._reload_view_preset_combo_items()
        self._restore_last_preset()
        self._apply_layout_mode(force=True)
        self.refresh_data(immediate=True)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.filter_group = QWidget()
        self.filter_group.setObjectName("InfoFilterArea")
        filter_layout = QVBoxLayout(self.filter_group)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(4)

        quick_search_row = QWidget()
        quick_search_layout = QHBoxLayout(quick_search_row)
        quick_search_layout.setContentsMargins(0, 0, 0, 0)
        quick_search_layout.setSpacing(4)
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText(tr("info_search_placeholder"))
        self.edit_search.textChanged.connect(self._on_filter_controls_changed)
        quick_search_layout.addWidget(self.edit_search, 1)
        self.btn_refresh = QPushButton(tr("info_refresh"))
        self.btn_refresh.setObjectName("ActionBtn")
        self.btn_refresh.clicked.connect(lambda: self.refresh_data(immediate=True))
        quick_search_layout.addWidget(self.btn_refresh)
        filter_layout.addWidget(quick_search_row)

        quick_view_row = QWidget()
        quick_view_layout = QHBoxLayout(quick_view_row)
        quick_view_layout.setContentsMargins(0, 0, 0, 0)
        quick_view_layout.setSpacing(4)

        self.lbl_preset = QLabel(tr("info_view_preset_label"))
        self.lbl_preset.setVisible(False)
        self.cmb_view_preset = QComboBox()
        self.cmb_view_preset.setToolTip(tr("info_view_preset_label"))
        self.cmb_view_preset.currentIndexChanged.connect(self._on_view_preset_changed)
        quick_view_layout.addWidget(self.cmb_view_preset, 2)

        self.btn_preset_actions = QToolButton()
        self.btn_preset_actions.setObjectName("ActionBtn")
        self.btn_preset_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_preset_actions = QMenu(self.btn_preset_actions)
        self.btn_view_save = QAction(tr("info_view_save"), self)
        self.btn_view_save.triggered.connect(self._save_new_view_preset)
        self.menu_preset_actions.addAction(self.btn_view_save)
        self.btn_view_update = QAction(tr("info_view_update"), self)
        self.btn_view_update.triggered.connect(self._update_current_view_preset)
        self.menu_preset_actions.addAction(self.btn_view_update)
        self.btn_view_delete = QAction(tr("info_view_delete"), self)
        self.btn_view_delete.triggered.connect(self._delete_current_view_preset)
        self.menu_preset_actions.addAction(self.btn_view_delete)
        self.btn_preset_actions.setMenu(self.menu_preset_actions)
        quick_view_layout.addWidget(self.btn_preset_actions)

        self.lbl_smart_view = QLabel(tr("info_smart_view_label"))
        self.lbl_smart_view.setVisible(False)
        self.cmb_smart_view = QComboBox()
        self.cmb_smart_view.setToolTip(tr("info_smart_view_label"))
        self._reload_smart_view_combo_items()
        self.cmb_smart_view.currentIndexChanged.connect(self._on_smart_view_combo_changed)
        quick_view_layout.addWidget(self.cmb_smart_view, 1)

        self.lbl_archive_scope = QLabel(tr("info_archive_scope_label"))
        self.lbl_archive_scope.setVisible(False)
        self.cmb_archive_scope = QComboBox()
        self.cmb_archive_scope.setToolTip(tr("info_archive_scope_label"))
        self._reload_archive_scope_combo_items()
        self.cmb_archive_scope.currentIndexChanged.connect(self._on_filter_controls_changed)
        quick_view_layout.addWidget(self.cmb_archive_scope, 1)

        filter_layout.addWidget(quick_view_row)

        self.advanced_filters_box = CollapsibleBox(tr("info_advanced_filters"))
        self.advanced_filters_box.toggle_button.toggled.connect(self._on_advanced_filters_toggled)
        advanced_layout = QGridLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setHorizontalSpacing(4)
        advanced_layout.setVerticalSpacing(4)

        self.edit_tag_filter = QLineEdit()
        self.edit_tag_filter.setPlaceholderText(tr("info_tag_placeholder"))
        self.edit_tag_filter.textChanged.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.edit_tag_filter, 0, 0, 1, 5)

        self.chk_open_only = QCheckBox(tr("info_open_tasks_only"))
        self.chk_open_only.toggled.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.chk_open_only, 1, 0)
        self.chk_star_only = QCheckBox(tr("info_star_only"))
        self.chk_star_only.toggled.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.chk_star_only, 1, 1)

        self.lbl_mode = QLabel(tr("info_mode_label"))
        advanced_layout.addWidget(self.lbl_mode, 2, 0)
        self.cmb_mode_filter = QComboBox()
        self._reload_mode_combo_items()
        self.cmb_mode_filter.currentIndexChanged.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.cmb_mode_filter, 2, 1)

        self.lbl_due_filter = QLabel(tr("info_due_filter_label"))
        advanced_layout.addWidget(self.lbl_due_filter, 2, 2)
        self.cmb_due_filter = QComboBox()
        self._reload_due_combo_items()
        self.cmb_due_filter.currentIndexChanged.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.cmb_due_filter, 2, 3)

        self.lbl_sort = QLabel(tr("info_sort_label"))
        advanced_layout.addWidget(self.lbl_sort, 3, 0)
        self.cmb_sort_by = QComboBox()
        self._reload_sort_combo_items()
        self.cmb_sort_by.currentIndexChanged.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.cmb_sort_by, 3, 1, 1, 2)

        self.btn_sort_desc = QPushButton(tr("info_sort_desc"))
        self.btn_sort_desc.setCheckable(True)
        self.btn_sort_desc.setChecked(True)
        self.btn_sort_desc.setProperty("class", "toggle")
        self.btn_sort_desc.toggled.connect(self._on_filter_controls_changed)
        advanced_layout.addWidget(self.btn_sort_desc, 3, 3)

        self.lbl_layout_mode = QLabel(tr("info_layout_mode_label"))
        advanced_layout.addWidget(self.lbl_layout_mode, 4, 0)
        self.cmb_layout_mode = QComboBox()
        self._reload_layout_mode_combo_items()
        self.cmb_layout_mode.currentIndexChanged.connect(self._on_layout_mode_changed)
        advanced_layout.addWidget(self.cmb_layout_mode, 4, 1)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setProperty("class", "info-label")
        advanced_layout.addWidget(self.lbl_stats, 5, 0, 1, 5)
        self.advanced_filters_box.setContentLayout(advanced_layout)
        filter_layout.addWidget(self.advanced_filters_box)
        layout.addWidget(self.filter_group)

        self.subtabs = QTabWidget()

        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        self.tasks_tree = QTreeWidget()
        self.tasks_tree.setHeaderHidden(True)
        self.tasks_tree.setColumnCount(1)
        self.tasks_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tasks_tree.setRootIsDecorated(False)
        self.tasks_tree.setIndentation(16)
        self.tasks_tree.itemChanged.connect(self._on_task_item_changed)
        self.tasks_tree.itemDoubleClicked.connect(self._on_task_item_activated)
        self.tasks_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tasks_tree.customContextMenuRequested.connect(
            lambda pos: self._show_bulk_context_menu(self.tasks_tree, pos)
        )
        tasks_layout.addWidget(self.tasks_tree)
        self.subtabs.addTab(self.tasks_tab, tr("info_tasks_tab"))

        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        self.notes_tree = QTreeWidget()
        self.notes_tree.setHeaderHidden(True)
        self.notes_tree.setColumnCount(1)
        self.notes_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.notes_tree.setRootIsDecorated(False)
        self.notes_tree.setIndentation(16)
        self.notes_tree.itemChanged.connect(self._on_note_item_changed)
        self.notes_tree.itemDoubleClicked.connect(self._on_note_item_activated)
        self.notes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_tree.customContextMenuRequested.connect(
            lambda pos: self._show_bulk_context_menu(self.notes_tree, pos)
        )
        notes_layout.addWidget(self.notes_tree)

        notes_btn_row = QHBoxLayout()
        self.btn_toggle_star = QPushButton(tr("info_toggle_star"))
        self.btn_toggle_star.setObjectName("ActionBtn")
        self.btn_toggle_star.clicked.connect(self._toggle_selected_note_star)
        notes_btn_row.addWidget(self.btn_toggle_star)
        notes_btn_row.addStretch(1)
        notes_layout.addLayout(notes_btn_row)

        self.subtabs.addTab(self.notes_tab, tr("info_notes_tab"))
        layout.addWidget(self.subtabs, 1)

        self.empty_state_row = QWidget()
        empty_layout = QVBoxLayout(self.empty_state_row)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(4)
        self.lbl_empty_state_hint = QLabel("")
        self.lbl_empty_state_hint.setProperty("class", "info-label")
        self.lbl_empty_state_hint.setWordWrap(True)
        self.lbl_empty_state_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.lbl_empty_state_hint)
        self.btn_empty_add_text = QPushButton(tr("menu_add_text"))
        self.btn_empty_add_text.setObjectName("ActionBtn")
        self.btn_empty_add_text.clicked.connect(self._add_text_from_empty_state)
        empty_layout.addWidget(self.btn_empty_add_text, 0, Qt.AlignmentFlag.AlignHCenter)
        self.empty_state_row.setVisible(False)
        layout.addWidget(self.empty_state_row)

        self.btn_bulk_actions = QToolButton()
        self.btn_bulk_actions.setObjectName("ActionBtn")
        self.btn_bulk_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_bulk_actions = QMenu(self.btn_bulk_actions)
        self.btn_complete_selected = QAction(tr("info_bulk_complete_selected"), self)
        self.btn_complete_selected.triggered.connect(lambda: self._apply_bulk_task_done(True))
        self.menu_bulk_actions.addAction(self.btn_complete_selected)
        self.btn_uncomplete_selected = QAction(tr("info_bulk_uncomplete_selected"), self)
        self.btn_uncomplete_selected.triggered.connect(lambda: self._apply_bulk_task_done(False))
        self.menu_bulk_actions.addAction(self.btn_uncomplete_selected)
        self.btn_archive_selected = QAction(tr("info_bulk_archive_selected"), self)
        self.btn_archive_selected.triggered.connect(self._archive_selected)
        self.menu_bulk_actions.addAction(self.btn_archive_selected)
        self.btn_restore_selected = QAction(tr("info_bulk_restore_selected"), self)
        self.btn_restore_selected.triggered.connect(self._restore_selected)
        self.menu_bulk_actions.addAction(self.btn_restore_selected)
        self.btn_star_selected = QAction(tr("info_bulk_star_selected"), self)
        self.btn_star_selected.triggered.connect(lambda: self._apply_bulk_star(True))
        self.menu_bulk_actions.addAction(self.btn_star_selected)
        self.btn_unstar_selected = QAction(tr("info_bulk_unstar_selected"), self)
        self.btn_unstar_selected.triggered.connect(lambda: self._apply_bulk_star(False))
        self.menu_bulk_actions.addAction(self.btn_unstar_selected)
        self.btn_edit_tags_selected = QAction(tr("info_bulk_edit_tags_selected"), self)
        self.btn_edit_tags_selected.triggered.connect(self._edit_tags_selected)
        self.menu_bulk_actions.addAction(self.btn_edit_tags_selected)
        self.btn_bulk_actions.setMenu(self.menu_bulk_actions)
        self.subtabs.setCornerWidget(self.btn_bulk_actions, Qt.Corner.TopRightCorner)

        self.operation_summary_row = QWidget()
        summary_layout = QHBoxLayout(self.operation_summary_row)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(4)
        self.lbl_operation_summary = QLabel(tr("info_operation_empty"))
        self.lbl_operation_summary.setProperty("class", "info-label")
        summary_layout.addWidget(self.lbl_operation_summary, 1)
        self.btn_open_operations = QPushButton(tr("info_recent_operations_open"))
        self.btn_open_operations.setObjectName("ActionBtn")
        self.btn_open_operations.clicked.connect(self._open_operations_dialog)
        summary_layout.addWidget(self.btn_open_operations)
        layout.addWidget(self.operation_summary_row)

    @staticmethod
    def _derive_item_scope_from_mode(mode_filter: str) -> str:
        mode = str(mode_filter or "").strip().lower()
        if mode == "task":
            return "tasks"
        if mode == "note":
            return "notes"
        return "all"

    @staticmethod
    def _derive_mode_from_scope(item_scope: str, content_mode_filter: str = "all") -> str:
        scope = str(item_scope or "").strip().lower()
        if scope == "tasks":
            return "task"
        if scope == "notes":
            return "note"
        mode = str(content_mode_filter or "").strip().lower()
        if mode in {"task", "note"}:
            return mode
        return "all"

    @staticmethod
    def _default_filters() -> dict[str, Any]:
        return {
            "text": "",
            "tag": "",
            "starred_only": False,
            "open_tasks_only": False,
            "archive_scope": "active",
            "due_filter": "all",
            "item_scope": "all",
            "content_mode_filter": "all",
            "sort_by": "updated",
            "sort_desc": True,
        }

    def _build_builtin_presets(self) -> dict[str, ViewPreset]:
        defaults = self._default_filters()
        return {
            "builtin:all": ViewPreset(
                preset_id="builtin:all",
                name=tr("info_view_all"),
                filters=dict(defaults),
                smart_view="all",
            ),
            "builtin:open": ViewPreset(
                preset_id="builtin:open",
                name=tr("info_view_open"),
                filters={**dict(defaults), "open_tasks_only": True},
                smart_view="open",
            ),
            "builtin:today": ViewPreset(
                preset_id="builtin:today",
                name=tr("info_view_today"),
                filters={**dict(defaults), "due_filter": "today", "sort_by": "due", "sort_desc": False},
                smart_view="today",
            ),
            "builtin:overdue": ViewPreset(
                preset_id="builtin:overdue",
                name=tr("info_view_overdue"),
                filters={
                    **dict(defaults),
                    "open_tasks_only": True,
                    "due_filter": "overdue",
                    "sort_by": "due",
                    "sort_desc": False,
                },
                smart_view="overdue",
            ),
            "builtin:starred": ViewPreset(
                preset_id="builtin:starred",
                name=tr("info_view_starred"),
                filters={**dict(defaults), "starred_only": True},
                smart_view="starred",
            ),
            "builtin:archived": ViewPreset(
                preset_id="builtin:archived",
                name=tr("info_view_archived"),
                filters={**dict(defaults), "archive_scope": "archived", "sort_by": "updated", "sort_desc": True},
                smart_view="archived",
            ),
        }

    def _sanitize_filters(self, raw: Any) -> dict[str, Any]:
        defaults = self._default_filters()
        if not isinstance(raw, dict):
            return defaults

        out = dict(defaults)
        out["text"] = str(raw.get("text", defaults["text"]) or "").strip()
        out["tag"] = str(raw.get("tag", defaults["tag"]) or "").strip()
        out["starred_only"] = bool(raw.get("starred_only", defaults["starred_only"]))
        out["open_tasks_only"] = bool(raw.get("open_tasks_only", defaults["open_tasks_only"]))

        archive_scope = str(raw.get("archive_scope", defaults["archive_scope"]) or "").strip().lower()
        out["archive_scope"] = (
            archive_scope if archive_scope in self._ARCHIVE_SCOPE_VALUES else defaults["archive_scope"]
        )

        due_filter = str(raw.get("due_filter", defaults["due_filter"]) or "").strip().lower()
        out["due_filter"] = due_filter if due_filter in self._DUE_FILTER_VALUES else defaults["due_filter"]

        item_scope = str(raw.get("item_scope", defaults["item_scope"]) or "").strip().lower()
        if item_scope not in self._ITEM_SCOPE_VALUES:
            item_scope = defaults["item_scope"]
        out["item_scope"] = item_scope

        content_mode_filter = str(raw.get("content_mode_filter", defaults["content_mode_filter"]) or "").strip().lower()
        if content_mode_filter not in self._MODE_FILTER_VALUES:
            # Migration boundary is in AppSettings sanitize-load.
            if item_scope == "tasks":
                content_mode_filter = "task"
            elif item_scope == "notes":
                content_mode_filter = "note"
            else:
                content_mode_filter = "all"
        elif content_mode_filter == "all":
            if item_scope == "tasks":
                content_mode_filter = "task"
            elif item_scope == "notes":
                content_mode_filter = "note"
        out["content_mode_filter"] = content_mode_filter

        sort_by = str(raw.get("sort_by", defaults["sort_by"]) or "").strip().lower()
        out["sort_by"] = sort_by if sort_by in self._SORT_BY_VALUES else defaults["sort_by"]
        out["sort_desc"] = bool(raw.get("sort_desc", defaults["sort_desc"]))
        return out

    def _sanitize_user_preset(self, raw: Any) -> Optional[ViewPreset]:
        if not isinstance(raw, dict):
            return None
        preset_id = str(raw.get("id", "") or "").strip()
        if not preset_id.startswith("user:"):
            return None
        name = str(raw.get("name", "") or "").strip()[:32]
        if not name:
            name = preset_id.replace("user:", "", 1) or tr("info_view_user_prefix")
        filters = self._sanitize_filters(raw.get("filters", {}))
        return ViewPreset(preset_id=preset_id, name=name, filters=filters, smart_view="custom")

    def _serialize_filters_for_preset(self, filters: dict[str, Any]) -> dict[str, Any]:
        return dict(self._sanitize_filters(filters))

    def _load_presets_from_settings(self) -> None:
        self._view_presets = self._build_builtin_presets()
        self._user_preset_ids.clear()

        settings = getattr(self.mw, "app_settings", None)
        raw_user_presets = list(getattr(settings, "info_view_presets", []) or []) if settings is not None else []
        sanitized_for_save: list[dict[str, Any]] = []
        max_numeric = 0

        for raw in raw_user_presets:
            preset = self._sanitize_user_preset(raw)
            if preset is None or preset.preset_id in self._view_presets:
                continue
            self._view_presets[preset.preset_id] = preset
            self._user_preset_ids.append(preset.preset_id)
            sanitized_for_save.append(
                {
                    "id": preset.preset_id,
                    "name": preset.name,
                    "filters": self._serialize_filters_for_preset(preset.filters),
                }
            )
            suffix = preset.preset_id.replace("user:", "", 1)
            if suffix.isdigit():
                max_numeric = max(max_numeric, int(suffix))

        self._next_user_preset_number = max(1, max_numeric + 1)
        if settings is not None:
            settings.info_view_presets = sanitized_for_save

    def _persist_presets_to_settings(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        settings_manager = getattr(self.mw, "settings_manager", None)
        if settings is None:
            return

        serialized_user: list[dict[str, Any]] = []
        for preset_id in list(self._user_preset_ids):
            preset = self._view_presets.get(preset_id)
            if preset is None:
                continue
            serialized_user.append(
                {
                    "id": preset.preset_id,
                    "name": preset.name,
                    "filters": self._serialize_filters_for_preset(preset.filters),
                }
            )

        settings.info_view_presets = serialized_user
        settings.info_last_view_preset_id = self._current_preset_id or "builtin:all"
        if settings_manager is not None and hasattr(settings_manager, "save_app_settings"):
            settings_manager.save_app_settings()

    def _restore_last_preset(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        last_id = str(getattr(settings, "info_last_view_preset_id", "") or "builtin:all")
        if last_id not in self._view_presets:
            last_id = "builtin:all"
        self._apply_preset_by_id(last_id, refresh=False, persist_last=False)

    def _load_ui_state_from_settings(self) -> None:
        settings = getattr(self.mw, "app_settings", None)
        mode = str(getattr(settings, "info_layout_mode", "auto") or "auto").strip().lower()
        if mode not in self._LAYOUT_MODE_VALUES:
            mode = "auto"
        advanced_expanded = bool(getattr(settings, "info_advanced_filters_expanded", False))
        if mode in {"auto", "compact"}:
            advanced_expanded = False

        self._suspend_ui_state_persist = True
        try:
            self._layout_mode = mode
            self._reload_layout_mode_combo_items()
            self._set_combo_data(self.cmb_layout_mode, mode)
            self.advanced_filters_box.toggle_button.setChecked(advanced_expanded)
        finally:
            self._suspend_ui_state_persist = False

    def _persist_ui_state_to_settings(self) -> None:
        if self._suspend_ui_state_persist:
            return
        settings = getattr(self.mw, "app_settings", None)
        settings_manager = getattr(self.mw, "settings_manager", None)
        if settings is None:
            return

        settings.info_layout_mode = self._layout_mode
        settings.info_advanced_filters_expanded = bool(self.advanced_filters_box.toggle_button.isChecked())
        if settings_manager is not None and hasattr(settings_manager, "save_app_settings"):
            settings_manager.save_app_settings()

    def _on_advanced_filters_toggled(self, _: bool) -> None:
        self._persist_ui_state_to_settings()

    def _reload_layout_mode_combo_items(self) -> None:
        selected_data = str(self.cmb_layout_mode.currentData() or self._layout_mode or "auto")
        self._block_layout_mode_events = True
        self.cmb_layout_mode.blockSignals(True)
        self.cmb_layout_mode.clear()
        self.cmb_layout_mode.addItem(tr("info_layout_mode_auto"), "auto")
        self.cmb_layout_mode.addItem(tr("info_layout_mode_compact"), "compact")
        self.cmb_layout_mode.addItem(tr("info_layout_mode_regular"), "regular")
        idx = self.cmb_layout_mode.findData(selected_data)
        self.cmb_layout_mode.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_layout_mode.blockSignals(False)
        self._block_layout_mode_events = False

    def _reload_smart_view_combo_items(self) -> None:
        selected_data = str(self.cmb_smart_view.currentData() or self._smart_view or "all")
        self._block_smart_view_events = True
        self.cmb_smart_view.blockSignals(True)
        self.cmb_smart_view.clear()
        entries = [
            ("all", "info_view_all", "info_view_tip_all"),
            ("open", "info_view_open", "info_view_tip_open"),
            ("today", "info_view_today", "info_view_tip_today"),
            ("overdue", "info_view_overdue", "info_view_tip_overdue"),
            ("starred", "info_view_starred", "info_view_tip_starred"),
            ("archived", "info_view_archived", "info_view_tip_archived"),
            ("custom", "info_view_custom", "info_view_tip_custom"),
        ]
        for value, text_key, tip_key in entries:
            self.cmb_smart_view.addItem(tr(text_key), value)
            idx = self.cmb_smart_view.count() - 1
            self.cmb_smart_view.setItemData(idx, tr(tip_key), Qt.ItemDataRole.ToolTipRole)
        idx = self.cmb_smart_view.findData(selected_data)
        self.cmb_smart_view.setCurrentIndex(idx if idx >= 0 else self.cmb_smart_view.findData("custom"))
        self.cmb_smart_view.blockSignals(False)
        self._block_smart_view_events = False

    def _on_smart_view_combo_changed(self, *_: Any) -> None:
        if self._block_smart_view_events:
            return
        view_key = str(self.cmb_smart_view.currentData() or "custom")
        if view_key in self._SMART_VIEW_KEYS:
            self._on_smart_view_clicked(view_key, True)
            return
        if self._smart_view != "custom":
            self._set_smart_view_indicator("custom")

    def _on_layout_mode_changed(self, *_: Any) -> None:
        if self._block_layout_mode_events:
            return
        mode = str(self.cmb_layout_mode.currentData() or "auto").strip().lower()
        if mode not in self._LAYOUT_MODE_VALUES:
            mode = "auto"
        self._layout_mode = mode
        self._apply_layout_mode(force=True)
        self._persist_ui_state_to_settings()

    def _apply_layout_mode(self, force: bool = False) -> None:
        effective = self._layout_mode
        if effective == "auto":
            effective = "compact" if self.width() < 360 else "regular"
        if not force and effective == self._effective_layout_mode:
            return
        self._effective_layout_mode = effective
        compact = effective == "compact"

        self.btn_refresh.setText(tr("info_refresh_short") if compact else tr("info_refresh"))
        self.btn_refresh.setToolTip(tr("info_refresh"))
        self.lbl_layout_mode.setText(tr("info_layout_mode_label_short") if compact else tr("info_layout_mode_label"))
        self.lbl_preset.setText(tr("info_view_preset_label_short") if compact else tr("info_view_preset_label"))
        self.lbl_smart_view.setText(tr("info_smart_view_label_short") if compact else tr("info_smart_view_label"))
        self.lbl_archive_scope.setText(
            tr("info_archive_scope_label_short") if compact else tr("info_archive_scope_label")
        )
        self.btn_preset_actions.setText(tr("info_view_actions_short") if compact else tr("info_view_actions"))
        self.btn_preset_actions.setToolTip(tr("info_view_actions"))
        self.btn_bulk_actions.setText(tr("info_bulk_actions_short") if compact else tr("info_bulk_actions_menu"))
        self.btn_bulk_actions.setToolTip(tr("info_bulk_actions_menu"))
        self.btn_open_operations.setText(
            tr("info_recent_operations_open_short") if compact else tr("info_recent_operations_open")
        )
        self.btn_open_operations.setToolTip(tr("info_recent_operations_open"))

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if self._layout_mode == "auto":
            self._apply_layout_mode()

    def set_compact_mode(self, enabled: bool) -> None:
        _ = enabled
        if self._layout_mode == "auto":
            self._apply_layout_mode(force=True)

    def _reload_mode_combo_items(self) -> None:
        selected_data = str(self.cmb_mode_filter.currentData() or "all") if hasattr(self, "cmb_mode_filter") else "all"
        self.cmb_mode_filter.blockSignals(True)
        self.cmb_mode_filter.clear()
        self.cmb_mode_filter.addItem(tr("info_mode_all"), "all")
        self.cmb_mode_filter.addItem(tr("info_mode_task"), "task")
        self.cmb_mode_filter.addItem(tr("info_mode_note"), "note")
        idx = self.cmb_mode_filter.findData(selected_data)
        self.cmb_mode_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_mode_filter.blockSignals(False)

    def _reload_due_combo_items(self) -> None:
        selected_data = str(self.cmb_due_filter.currentData() or "all") if hasattr(self, "cmb_due_filter") else "all"
        self.cmb_due_filter.blockSignals(True)
        self.cmb_due_filter.clear()
        self.cmb_due_filter.addItem(tr("info_due_all"), "all")
        self.cmb_due_filter.addItem(tr("info_due_today"), "today")
        self.cmb_due_filter.addItem(tr("info_due_overdue"), "overdue")
        self.cmb_due_filter.addItem(tr("info_due_upcoming"), "upcoming")
        self.cmb_due_filter.addItem(tr("info_due_dated"), "dated")
        self.cmb_due_filter.addItem(tr("info_due_undated"), "undated")
        idx = self.cmb_due_filter.findData(selected_data)
        self.cmb_due_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_due_filter.blockSignals(False)

    def _reload_archive_scope_combo_items(self) -> None:
        selected_data = (
            str(self.cmb_archive_scope.currentData() or "active") if hasattr(self, "cmb_archive_scope") else "active"
        )
        self.cmb_archive_scope.blockSignals(True)
        self.cmb_archive_scope.clear()
        self.cmb_archive_scope.addItem(tr("info_archive_scope_active"), "active")
        self.cmb_archive_scope.addItem(tr("info_archive_scope_archived"), "archived")
        self.cmb_archive_scope.addItem(tr("info_archive_scope_all"), "all")
        idx = self.cmb_archive_scope.findData(selected_data)
        self.cmb_archive_scope.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_archive_scope.blockSignals(False)

    def _reload_sort_combo_items(self) -> None:
        selected_data = str(self.cmb_sort_by.currentData() or "updated") if hasattr(self, "cmb_sort_by") else "updated"
        self.cmb_sort_by.blockSignals(True)
        self.cmb_sort_by.clear()
        self.cmb_sort_by.addItem(tr("info_sort_updated"), "updated")
        self.cmb_sort_by.addItem(tr("info_sort_due"), "due")
        self.cmb_sort_by.addItem(tr("info_sort_created"), "created")
        self.cmb_sort_by.addItem(tr("info_sort_title"), "title")
        idx = self.cmb_sort_by.findData(selected_data)
        self.cmb_sort_by.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_sort_by.blockSignals(False)

    def _reload_view_preset_combo_items(self) -> None:
        selected_id = self._current_preset_id
        self._block_preset_events = True
        self.cmb_view_preset.blockSignals(True)
        self.cmb_view_preset.clear()

        for preset_id in [
            "builtin:all",
            "builtin:open",
            "builtin:today",
            "builtin:overdue",
            "builtin:starred",
            "builtin:archived",
        ]:
            preset = self._view_presets.get(preset_id)
            if preset is not None:
                self.cmb_view_preset.addItem(preset.name, preset.preset_id)
        for preset_id in self._user_preset_ids:
            preset = self._view_presets.get(preset_id)
            if preset is not None:
                self.cmb_view_preset.addItem(preset.name, preset.preset_id)

        idx = self.cmb_view_preset.findData(selected_id)
        self.cmb_view_preset.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_view_preset.blockSignals(False)
        self._block_preset_events = False

    def _on_smart_view_clicked(self, view_key: str, checked: bool) -> None:
        if not checked:
            if self._smart_view != "custom":
                self._set_smart_view_indicator("custom")
            return
        self._apply_preset_by_id(f"builtin:{view_key}")

    def _set_smart_view_indicator(self, view_key: str) -> None:
        normalized = str(view_key or "").strip().lower()
        if normalized not in self._SMART_VIEW_KEYS:
            normalized = "custom"
        self._smart_view = normalized
        if hasattr(self, "cmb_smart_view"):
            self._block_smart_view_events = True
            self.cmb_smart_view.blockSignals(True)
            idx = self.cmb_smart_view.findData(normalized)
            self.cmb_smart_view.setCurrentIndex(idx if idx >= 0 else self.cmb_smart_view.findData("custom"))
            self.cmb_smart_view.blockSignals(False)
            self._block_smart_view_events = False
        for key, btn in self._smart_view_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(normalized == key)
            btn.blockSignals(False)

    def _set_combo_data(self, combo: QComboBox, data: str) -> None:
        idx = combo.findData(data)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _apply_filters_to_controls(self, filters: dict[str, Any]) -> None:
        sanitized = self._sanitize_filters(filters)
        mode_filter = self._derive_mode_from_scope(
            str(sanitized.get("item_scope", "all")),
            str(sanitized.get("content_mode_filter", "all")),
        )
        self._block_filter_events = True
        try:
            self.edit_search.setText(str(sanitized["text"]))
            self.edit_tag_filter.setText(str(sanitized["tag"]))
            self.chk_star_only.setChecked(bool(sanitized["starred_only"]))
            self.chk_open_only.setChecked(bool(sanitized["open_tasks_only"]))
            self._set_combo_data(self.cmb_archive_scope, str(sanitized["archive_scope"]))
            self._set_combo_data(self.cmb_due_filter, str(sanitized["due_filter"]))
            self._set_combo_data(self.cmb_mode_filter, mode_filter)
            self._set_combo_data(self.cmb_sort_by, str(sanitized["sort_by"]))
            self.btn_sort_desc.setChecked(bool(sanitized["sort_desc"]))
        finally:
            self._block_filter_events = False

    def _apply_preset_by_id(self, preset_id: str, refresh: bool = True, persist_last: bool = True) -> None:
        target_id = str(preset_id or "").strip()
        if target_id not in self._view_presets:
            target_id = "builtin:all"
        preset = self._view_presets[target_id]

        self._apply_filters_to_controls(preset.filters)
        self._set_smart_view_indicator(preset.smart_view)
        self._current_preset_id = preset.preset_id

        idx = self.cmb_view_preset.findData(preset.preset_id)
        self._block_preset_events = True
        self.cmb_view_preset.blockSignals(True)
        self.cmb_view_preset.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_view_preset.blockSignals(False)
        self._block_preset_events = False

        if persist_last:
            self._persist_presets_to_settings()
        if refresh:
            self.refresh_data()

    def _collect_filter_state(self) -> dict[str, Any]:
        mode_filter = str(self.cmb_mode_filter.currentData() or "all")
        item_scope = self._derive_item_scope_from_mode(mode_filter)
        content_mode_filter = mode_filter if mode_filter in {"task", "note"} else "all"
        return self._sanitize_filters(
            {
                "text": self.edit_search.text().strip(),
                "tag": self.edit_tag_filter.text().strip(),
                "starred_only": self.chk_star_only.isChecked(),
                "open_tasks_only": self.chk_open_only.isChecked(),
                "archive_scope": str(self.cmb_archive_scope.currentData() or "active"),
                "due_filter": str(self.cmb_due_filter.currentData() or "all"),
                "item_scope": item_scope,
                "content_mode_filter": content_mode_filter,
                "sort_by": str(self.cmb_sort_by.currentData() or "updated"),
                "sort_desc": self.btn_sort_desc.isChecked(),
            }
        )

    def _on_filter_controls_changed(self, *_: Any) -> None:
        if self._block_filter_events:
            return
        self._set_smart_view_indicator("custom")
        self.refresh_data()

    def _on_view_preset_changed(self, *_: Any) -> None:
        if self._block_preset_events:
            return
        preset_id = str(self.cmb_view_preset.currentData() or "")
        if preset_id:
            self._apply_preset_by_id(preset_id)

    def _generate_next_user_preset_identity(self) -> tuple[str, str]:
        while True:
            num = self._next_user_preset_number
            self._next_user_preset_number += 1
            preset_id = f"user:{num}"
            if preset_id in self._view_presets:
                continue
            return preset_id, f"{tr('info_view_user_prefix')} {num}"

    def _save_new_view_preset(self) -> None:
        filters = self._collect_filter_state()
        preset_id, name = self._generate_next_user_preset_identity()
        preset = ViewPreset(preset_id=preset_id, name=name[:32], filters=filters, smart_view="custom")
        self._view_presets[preset_id] = preset
        self._user_preset_ids.append(preset_id)
        self._current_preset_id = preset_id
        self._reload_view_preset_combo_items()
        self._apply_preset_by_id(preset_id, refresh=False, persist_last=True)
        self.refresh_data()

    def _update_current_view_preset(self) -> None:
        preset_id = self._current_preset_id
        if not preset_id.startswith("user:") or preset_id not in self._view_presets:
            self._save_new_view_preset()
            return
        current = self._view_presets[preset_id]
        self._view_presets[preset_id] = ViewPreset(
            preset_id=current.preset_id,
            name=current.name,
            filters=self._collect_filter_state(),
            smart_view="custom",
        )
        self._persist_presets_to_settings()
        self.refresh_data()

    def _delete_current_view_preset(self) -> None:
        preset_id = self._current_preset_id
        if not preset_id.startswith("user:"):
            return
        if preset_id in self._view_presets:
            del self._view_presets[preset_id]
        self._user_preset_ids = [pid for pid in self._user_preset_ids if pid != preset_id]
        self._current_preset_id = "builtin:all"
        self._reload_view_preset_combo_items()
        self._apply_preset_by_id("builtin:all", refresh=True, persist_last=True)

    def _build_query(self) -> InfoQuery:
        selected_mode = str(self.cmb_mode_filter.currentData() or "all")
        item_scope = self._derive_item_scope_from_mode(selected_mode)
        content_mode_filter = selected_mode if selected_mode in {"task", "note"} else "all"
        return InfoQuery(
            text=self.edit_search.text().strip(),
            tag=self.edit_tag_filter.text().strip(),
            starred_only=self.chk_star_only.isChecked(),
            open_tasks_only=self.chk_open_only.isChecked(),
            include_archived=False,
            archive_scope=str(self.cmb_archive_scope.currentData() or "active"),
            due_filter=str(self.cmb_due_filter.currentData() or "all"),
            item_scope=item_scope,
            content_mode_filter=content_mode_filter,
            sort_by=str(self.cmb_sort_by.currentData() or "updated"),
            sort_desc=self.btn_sort_desc.isChecked(),
        )

    def _iter_text_windows(self) -> list[Any]:
        wm = getattr(self.mw, "window_manager", None)
        if wm is None:
            return []
        return list(getattr(wm, "text_windows", []) or [])

    @staticmethod
    def _normalize_signature_tags(raw_tags: Any) -> tuple[str, ...]:
        if not isinstance(raw_tags, list):
            return ()
        tags: list[str] = []
        for raw in raw_tags:
            tag = str(raw or "").strip().lower()
            if tag:
                tags.append(tag)
        return tuple(tags)

    @staticmethod
    def _task_state_signature(raw_states: Any) -> tuple[int, int]:
        if not isinstance(raw_states, list):
            return (0, 0)
        normalized = tuple(bool(v) for v in raw_states)
        return (len(normalized), hash(normalized))

    def _build_index_signature(self, windows: list[Any]) -> tuple[Any, ...]:
        signatures: list[tuple[Any, ...]] = []
        for window in windows:
            if window is None:
                continue
            text = str(getattr(window, "text", "") or "")
            signatures.append(
                (
                    str(getattr(window, "uuid", "") or ""),
                    str(getattr(window, "updated_at", "") or ""),
                    str(getattr(window, "content_mode", "note") or "note").strip().lower(),
                    bool(getattr(window, "is_archived", False)),
                    bool(getattr(window, "is_starred", False)),
                    str(getattr(window, "title", "") or ""),
                    self._normalize_signature_tags(getattr(window, "tags", [])),
                    str(getattr(window, "due_at", "") or ""),
                    str(getattr(window, "due_time", "") or ""),
                    str(getattr(window, "due_timezone", "") or ""),
                    str(getattr(window, "due_precision", "date") or "date").strip().lower(),
                    len(text),
                    hash(text),
                    self._task_state_signature(getattr(window, "task_states", [])),
                )
            )
        return tuple(signatures)

    @staticmethod
    def _make_task_rows_signature(items: list[TaskIndexItem]) -> tuple[Any, ...]:
        return tuple(
            (
                item.item_key,
                bool(item.done),
                bool(item.is_archived),
                bool(item.is_starred),
                item.title,
                item.text,
                item.updated_at,
                item.created_at,
                item.due_at,
                item.due_time,
                item.due_timezone,
                item.due_precision,
            )
            for item in items
        )

    @staticmethod
    def _make_note_rows_signature(items: list[NoteIndexItem]) -> tuple[Any, ...]:
        return tuple(
            (
                item.window_uuid,
                bool(item.is_starred),
                bool(item.is_archived),
                item.title,
                item.first_line,
                item.content_mode,
                item.updated_at,
                item.created_at,
                item.due_at,
                item.due_time,
                item.due_timezone,
                item.due_precision,
            )
            for item in items
        )

    @staticmethod
    def _make_operation_logs_signature(entries: list[dict[str, Any]]) -> tuple[Any, ...]:
        return tuple(
            (
                str(entry.get("at", "") or ""),
                str(entry.get("action", "") or ""),
                int(entry.get("target_count", 0) or 0),
                str(entry.get("detail", "") or ""),
            )
            for entry in entries
        )

    def _invalidate_refresh_signatures(self) -> None:
        self._last_task_rows_signature = None
        self._last_note_rows_signature = None
        self._last_operation_logs_signature = None

    def _get_index_items(self, windows: list[Any]) -> tuple[list[TaskIndexItem], list[NoteIndexItem]]:
        signature = self._build_index_signature(windows)
        if signature == self._index_cache_signature:
            return self._index_cache_task_items, self._index_cache_note_items
        task_items, note_items = self.index_manager.build_index(windows)
        self._index_cache_signature = signature
        self._index_cache_task_items = task_items
        self._index_cache_note_items = note_items
        self._invalidate_refresh_signatures()
        return task_items, note_items

    def refresh_data(self, immediate: bool = False) -> None:
        if immediate:
            if self._refresh_timer.isActive():
                self._refresh_timer.stop()
            self._refresh_now()
            return
        self._refresh_timer.start(100)

    def _refresh_now(self) -> None:
        if self._is_refreshing:
            return

        self._is_refreshing = True
        try:
            windows = self._iter_text_windows()
            task_items, note_items = self._get_index_items(windows)
            query = self._build_query()
            filtered_tasks = self.index_manager.query_tasks(task_items, query)
            filtered_notes = self.index_manager.query_notes(note_items, query)
            stats = self.index_manager.build_stats(filtered_tasks, filtered_notes)

            task_sig = self._make_task_rows_signature(filtered_tasks)
            if task_sig != self._last_task_rows_signature:
                task_groups = self.index_manager.group_tasks_smart(filtered_tasks)
                self._populate_tasks_grouped(task_groups, filtered_tasks)
                self._last_task_rows_signature = task_sig

            note_sig = self._make_note_rows_signature(filtered_notes)
            if note_sig != self._last_note_rows_signature:
                note_groups = self.index_manager.group_notes_smart(filtered_notes)
                self._populate_notes_grouped(note_groups, filtered_notes)
                self._last_note_rows_signature = note_sig

            self._update_empty_state_hint(len(task_items) + len(note_items), len(filtered_tasks) + len(filtered_notes))
            self._update_stats(stats)
            self._populate_operation_logs()
        finally:
            self._is_refreshing = False

    def _add_text_from_empty_state(self) -> None:
        main_controller = getattr(self.mw, "main_controller", None)
        txt_actions = getattr(main_controller, "txt_actions", None)
        if txt_actions is not None and hasattr(txt_actions, "add_new_text_window"):
            txt_actions.add_new_text_window()

    def _update_empty_state_hint(self, total_count: int, filtered_count: int) -> None:
        total = max(int(total_count), 0)
        filtered = max(int(filtered_count), 0)
        if total == 0:
            self.empty_state_row.setVisible(True)
            self.lbl_empty_state_hint.setText(tr("info_empty_state_first_time"))
            self.btn_empty_add_text.setVisible(True)
            return
        if filtered == 0:
            self.empty_state_row.setVisible(True)
            self.lbl_empty_state_hint.setText(tr("info_empty_state_filtered"))
            self.btn_empty_add_text.setVisible(False)
            return
        self.empty_state_row.setVisible(False)

    def _build_due_badges(self, due_state: str, is_archived: bool = False, is_done_task: bool = False) -> list[str]:
        badges: list[str] = []
        if is_archived:
            badges.append(f"[{tr('info_badge_archived')}]")
        if is_done_task:
            return badges
        if due_state == "today":
            badges.append(f"[{tr('info_badge_today')}]")
        if due_state == "overdue":
            badges.append(f"[{tr('info_badge_overdue')}]")
        return badges

    @staticmethod
    def _item_color(due_state: str, is_archived: bool) -> Optional[QColor]:
        if is_archived:
            return QColor("#a0a0a0")
        if due_state == "today":
            return QColor("#f5c16c")
        if due_state == "overdue":
            return QColor("#ff9a9a")
        return None

    @staticmethod
    def _format_tags_badge(tags: tuple[str, ...]) -> str:
        if not tags:
            return ""
        return " ".join(f"[{tag}]" for tag in tags)

    def _build_task_item_text(
        self,
        item: TaskIndexItem,
        due_text_cache: dict[tuple[str, str, str, str], str],
        due_state_cache: dict[tuple[str, str, str, str], str],
    ) -> tuple[str, str]:
        """タスクアイテムの表示テキストと期限状態を返す。"""
        text = tr("info_task_item_fmt").format(title=item.title, text=item.text)
        tag_badge = self._format_tags_badge(item.tags)
        if tag_badge:
            text = f"{text}  {tag_badge}"
        due_key = (
            str(item.due_at or ""),
            str(item.due_time or ""),
            str(item.due_timezone or ""),
            str(item.due_precision or "date"),
        )
        due_text = due_text_cache.get(due_key)
        if due_text is None:
            due_text = format_due_for_display(
                item.due_at,
                due_time=item.due_time,
                due_timezone=item.due_timezone,
                due_precision=item.due_precision,
            )
            due_text_cache[due_key] = due_text
        due_state = due_state_cache.get(due_key)
        if due_state is None:
            due_state = classify_due(
                item.due_at,
                due_time=item.due_time,
                due_timezone=item.due_timezone,
                due_precision=item.due_precision,
            )
            due_state_cache[due_key] = due_state
        badges = self._build_due_badges(due_state, is_archived=bool(item.is_archived), is_done_task=bool(item.done))
        if due_text:
            text = f"{text}  ({tr('info_due_short_fmt').format(date=due_text)})"
        if badges:
            text = f"{text} {' '.join(badges)}"
        return text, due_state

    def _populate_tasks_grouped(
        self,
        groups: list[Any],
        all_items: list[TaskIndexItem],
    ) -> None:
        from managers.info_index_manager import GroupedTasks

        due_text_cache: dict[tuple[str, str, str, str], str] = {}
        due_state_cache: dict[tuple[str, str, str, str], str] = {}
        self.tasks_tree.blockSignals(True)
        try:
            self.tasks_tree.clear()
            if not all_items:
                empty = QTreeWidgetItem(self.tasks_tree)
                empty.setText(0, tr("info_list_empty"))
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                return

            has_multiple_groups = len(groups) > 1 or (len(groups) == 1 and groups[0].group_key != "other")
            if not has_multiple_groups:
                # グループが1つだけ（other のみ）の場合はフラット表示
                items = groups[0].items if groups else all_items
                for item in items:
                    text, due_state = self._build_task_item_text(item, due_text_cache, due_state_cache)
                    tw_item = QTreeWidgetItem(self.tasks_tree)
                    tw_item.setText(0, text)
                    tw_item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    tw_item.setCheckState(0, Qt.CheckState.Checked if item.done else Qt.CheckState.Unchecked)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole, item.item_key)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(item.done))
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 2, item.window_uuid)
                    color = self._item_color(due_state, bool(item.is_archived))
                    if color is not None:
                        tw_item.setForeground(0, QBrush(color))
                return

            for group in groups:
                if not isinstance(group, GroupedTasks) or not group.items:
                    continue
                header = QTreeWidgetItem(self.tasks_tree)
                header.setText(0, f"──── {group.label} ────")
                header.setFlags(Qt.ItemFlag.ItemIsEnabled)
                header.setData(0, Qt.ItemDataRole.UserRole, "")
                font = header.font(0)
                font.setBold(True)
                header.setFont(0, font)
                _GROUP_HEADER_COLORS = {
                    "overdue": QColor("#ff9a9a"),
                    "today": QColor("#f5c16c"),
                    "starred": QColor("#ffd700"),
                }
                group_color = _GROUP_HEADER_COLORS.get(group.group_key)
                if group_color is not None:
                    header.setForeground(0, QBrush(group_color))

                for item in group.items:
                    text, due_state = self._build_task_item_text(item, due_text_cache, due_state_cache)
                    tw_item = QTreeWidgetItem(header)
                    tw_item.setText(0, text)
                    tw_item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    tw_item.setCheckState(0, Qt.CheckState.Checked if item.done else Qt.CheckState.Unchecked)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole, item.item_key)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(item.done))
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 2, item.window_uuid)
                    color = self._item_color(due_state, bool(item.is_archived))
                    if color is not None:
                        tw_item.setForeground(0, QBrush(color))

                header.setExpanded(True)
        finally:
            self.tasks_tree.blockSignals(False)

    def _build_note_item_text(
        self,
        item: NoteIndexItem,
        due_text_cache: dict[tuple[str, str, str, str], str],
        due_state_cache: dict[tuple[str, str, str, str], str],
    ) -> tuple[str, str]:
        """ノートアイテムの表示テキストと期限状態を返す。"""
        mode_text = tr("label_content_mode_task") if item.content_mode == "task" else tr("label_content_mode_note")
        line = tr("info_note_item_fmt").format(
            title=item.title,
            mode=mode_text,
            first_line=item.first_line,
        )
        tag_badge = self._format_tags_badge(item.tags)
        if tag_badge:
            line = f"{line}  {tag_badge}"
        due_key = (
            str(item.due_at or ""),
            str(item.due_time or ""),
            str(item.due_timezone or ""),
            str(item.due_precision or "date"),
        )
        due_text = due_text_cache.get(due_key)
        if due_text is None:
            due_text = format_due_for_display(
                item.due_at,
                due_time=item.due_time,
                due_timezone=item.due_timezone,
                due_precision=item.due_precision,
            )
            due_text_cache[due_key] = due_text
        due_state = due_state_cache.get(due_key)
        if due_state is None:
            due_state = classify_due(
                item.due_at,
                due_time=item.due_time,
                due_timezone=item.due_timezone,
                due_precision=item.due_precision,
            )
            due_state_cache[due_key] = due_state
        badges = self._build_due_badges(due_state, is_archived=bool(item.is_archived))
        if due_text:
            line = f"{line}  ({tr('info_due_short_fmt').format(date=due_text)})"
        if badges:
            line = f"{line} {' '.join(badges)}"
        return line, due_state

    def _populate_notes_grouped(
        self,
        groups: list[Any],
        all_items: list[NoteIndexItem],
    ) -> None:
        from managers.info_index_manager import GroupedNotes

        due_text_cache: dict[tuple[str, str, str, str], str] = {}
        due_state_cache: dict[tuple[str, str, str, str], str] = {}
        self.notes_tree.blockSignals(True)
        try:
            self.notes_tree.clear()
            if not all_items:
                empty = QTreeWidgetItem(self.notes_tree)
                empty.setText(0, tr("info_list_empty"))
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                return

            has_multiple_groups = len(groups) > 1 or (len(groups) == 1 and groups[0].group_key != "other")
            if not has_multiple_groups:
                items = groups[0].items if groups else all_items
                for item in items:
                    line, due_state = self._build_note_item_text(item, due_text_cache, due_state_cache)
                    tw_item = QTreeWidgetItem(self.notes_tree)
                    tw_item.setText(0, line)
                    tw_item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    tw_item.setCheckState(0, Qt.CheckState.Checked if item.is_starred else Qt.CheckState.Unchecked)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole, item.window_uuid)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(item.is_starred))
                    color = self._item_color(due_state, bool(item.is_archived))
                    if color is not None:
                        tw_item.setForeground(0, QBrush(color))
                    if item.window_uuid and item.window_uuid == self._current_selected_uuid:
                        tw_item.setSelected(True)
                return

            for group in groups:
                if not isinstance(group, GroupedNotes) or not group.items:
                    continue
                header = QTreeWidgetItem(self.notes_tree)
                header.setText(0, f"──── {group.label} ────")
                header.setFlags(Qt.ItemFlag.ItemIsEnabled)
                header.setData(0, Qt.ItemDataRole.UserRole, "")
                font = header.font(0)
                font.setBold(True)
                header.setFont(0, font)
                if group.group_key == "starred":
                    header.setForeground(0, QBrush(QColor("#ffd700")))

                for item in group.items:
                    line, due_state = self._build_note_item_text(item, due_text_cache, due_state_cache)
                    tw_item = QTreeWidgetItem(header)
                    tw_item.setText(0, line)
                    tw_item.setFlags(
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    tw_item.setCheckState(0, Qt.CheckState.Checked if item.is_starred else Qt.CheckState.Unchecked)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole, item.window_uuid)
                    tw_item.setData(0, Qt.ItemDataRole.UserRole + 1, bool(item.is_starred))
                    color = self._item_color(due_state, bool(item.is_archived))
                    if color is not None:
                        tw_item.setForeground(0, QBrush(color))
                    if item.window_uuid and item.window_uuid == self._current_selected_uuid:
                        tw_item.setSelected(True)

                header.setExpanded(True)
        finally:
            self.notes_tree.blockSignals(False)

    def _update_stats(self, stats: InfoStats) -> None:
        self.lbl_stats.setText(
            tr("info_stats_fmt").format(
                open=stats.open_tasks,
                done=stats.done_tasks,
                overdue=stats.overdue_tasks,
                starred=stats.starred_notes,
            )
        )

    @staticmethod
    def _log_action_label(action: str) -> str:
        mapping = {
            "bulk_complete": "info_log_action_bulk_complete",
            "bulk_uncomplete": "info_log_action_bulk_uncomplete",
            "bulk_archive": "info_log_action_bulk_archive",
            "bulk_restore": "info_log_action_bulk_restore",
            "bulk_star": "info_log_action_bulk_star",
            "bulk_unstar": "info_log_action_bulk_unstar",
            "bulk_tags_merge": "info_log_action_bulk_tags_merge",
        }
        text_key = mapping.get(str(action or "").strip().lower())
        return tr(text_key) if text_key else str(action or "").strip()

    def _format_operation_entry(self, entry: dict[str, Any]) -> str:
        at = str(entry.get("at", "") or "").strip()
        action = self._log_action_label(str(entry.get("action", "") or ""))
        count = int(entry.get("target_count", 0) or 0)
        detail = str(entry.get("detail", "") or "").strip()
        line = tr("info_operation_item_fmt").format(at=at, action=action, count=count)
        if detail:
            line = f"{line} - {detail}"
        return line

    def _populate_operation_logs(self) -> None:
        main_controller = getattr(self.mw, "main_controller", None)
        actions = getattr(main_controller, "info_actions", None)
        logs = actions.get_operation_logs(limit=10) if actions is not None else []
        entries = [dict(entry) for entry in list(logs or [])]
        signature = self._make_operation_logs_signature(entries)
        if signature == self._last_operation_logs_signature:
            return
        self._last_operation_logs_signature = signature

        if not entries:
            summary = tr("info_operation_empty")
            self._operation_log_lines = []
            self.lbl_operation_summary.setText(summary)
            self.lbl_operation_summary.setToolTip(summary)
            return

        lines = [self._format_operation_entry(entry) for entry in reversed(entries)]
        self._operation_log_lines = lines
        latest_line = lines[0] if lines else tr("info_operation_empty")
        summary = tr("info_operation_summary_fmt").format(text=latest_line)
        self.lbl_operation_summary.setText(summary)
        self.lbl_operation_summary.setToolTip(latest_line)

    def _show_bulk_context_menu(self, source: QTreeWidget, pos: Any) -> None:
        global_pos = source.viewport().mapToGlobal(pos)
        self.menu_bulk_actions.exec(global_pos)

    def _open_operations_dialog(self) -> None:
        if self._operations_dialog is None:
            self._operations_dialog = InfoOperationsDialog(self)
            self._operations_dialog.btn_clear.clicked.connect(self._clear_operation_logs)
        self._operations_dialog.set_entries(list(self._operation_log_lines))
        self._operations_dialog.refresh_ui()
        self._operations_dialog.exec()

    def _on_task_item_changed(self, item: QTreeWidgetItem, column: int = 0) -> None:
        if self._is_refreshing:
            return
        item_key = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if ":" not in item_key:
            return

        prev_done = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
        next_done = item.checkState(0) == Qt.CheckState.Checked
        if prev_done == next_done:
            return

        # Defer action to next event loop tick so that setCheckState() finishes
        # before the tree is cleared/repopulated (prevents C++ access violation).
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            QTimer.singleShot(0, lambda _k=item_key: actions.toggle_task(_k))
            return

        QTimer.singleShot(0, lambda: self.refresh_data(immediate=True))

    def _on_task_item_activated(self, item: QTreeWidgetItem, column: int = 0) -> None:
        window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole + 2) or "")
        if not window_uuid:
            item_key = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            if ":" in item_key:
                window_uuid = item_key.rsplit(":", 1)[0]
        if not window_uuid:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.focus_window(window_uuid)

    def _on_note_item_changed(self, item: QTreeWidgetItem, column: int = 0) -> None:
        if self._is_refreshing:
            return
        window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        prev_star = bool(item.data(0, Qt.ItemDataRole.UserRole + 1))
        next_star = item.checkState(0) == Qt.CheckState.Checked
        if prev_star == next_star:
            return

        # Defer action to next event loop tick so that setCheckState() finishes
        # before the tree is cleared/repopulated (prevents C++ access violation).
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            QTimer.singleShot(0, lambda _u=window_uuid, _s=next_star: actions.set_star(_u, _s))
            return

        QTimer.singleShot(0, lambda: self.refresh_data(immediate=True))

    def _on_note_item_activated(self, item: QTreeWidgetItem, column: int = 0) -> None:
        window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.focus_window(window_uuid)

    def _toggle_selected_note_star(self) -> None:
        item = self.notes_tree.currentItem()
        if item is None:
            return
        window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        current = item.checkState(0) == Qt.CheckState.Checked

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.set_star(window_uuid, not current)
        self.refresh_data(immediate=True)

    def _selected_task_item_keys(self) -> list[str]:
        keys: list[str] = []
        for item in self.tasks_tree.selectedItems():
            item_key = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            if ":" in item_key:
                keys.append(item_key)
        return keys

    def _selected_window_uuids(self) -> list[str]:
        uuids: set[str] = set()
        for item in self.notes_tree.selectedItems():
            window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            if window_uuid:
                uuids.add(window_uuid)

        for item in self.tasks_tree.selectedItems():
            window_uuid = str(item.data(0, Qt.ItemDataRole.UserRole + 2) or "")
            if not window_uuid:
                item_key = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
                if ":" in item_key:
                    window_uuid = item_key.rsplit(":", 1)[0]
            if window_uuid:
                uuids.add(window_uuid)
        return sorted(uuids)

    def _apply_bulk_task_done(self, done: bool) -> None:
        keys = self._selected_task_item_keys()
        if not keys:
            return
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_set_task_done(keys, bool(done))
            return
        self.refresh_data(immediate=True)

    def _archive_selected(self) -> None:
        uuids = self._selected_window_uuids()
        if not uuids:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_archive(uuids, True)
            return
        self.refresh_data(immediate=True)

    def _restore_selected(self) -> None:
        uuids = self._selected_window_uuids()
        if not uuids:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_archive(uuids, False)
            return
        self.refresh_data(immediate=True)

    def _apply_bulk_star(self, starred: bool) -> None:
        uuids = self._selected_window_uuids()
        if not uuids:
            return
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_set_star(uuids, bool(starred))
            return
        self.refresh_data(immediate=True)

    def _edit_tags_selected(self) -> None:
        uuids = self._selected_window_uuids()
        if not uuids:
            return
        values = BulkTagEditDialog.ask(self)
        if values is None:
            return
        add_tags, remove_tags = values
        if not add_tags and not remove_tags:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_merge_tags(uuids, add_tags, remove_tags)
            return
        self.refresh_data(immediate=True)

    def _clear_operation_logs(self) -> None:
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None and hasattr(actions, "clear_operation_logs"):
            actions.clear_operation_logs()
            if self._operations_dialog is not None:
                self._operations_dialog.set_entries([])
            return
        self.refresh_data(immediate=True)

    def on_selection_changed(self, window: Optional[Any]) -> None:
        self._current_selected_uuid = str(getattr(window, "uuid", "") or "") if window is not None else ""
        if not self._current_selected_uuid:
            return
        self._select_note_by_uuid(self._current_selected_uuid)

    def _select_note_by_uuid(self, target_uuid: str) -> None:
        """ノートツリー内の指定UUIDのアイテムを選択してスクロールする。"""
        iterator = self._iter_tree_items(self.notes_tree)
        for item in iterator:
            uuid = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            is_match = uuid == target_uuid
            item.setSelected(is_match)
            if is_match:
                self.notes_tree.scrollToItem(item)

    @staticmethod
    def _iter_tree_items(tree: QTreeWidget) -> list[QTreeWidgetItem]:
        """QTreeWidget内の全アイテム（ヘッダー含む）をフラットに列挙する。"""
        result: list[QTreeWidgetItem] = []
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            if top is None:
                continue
            result.append(top)
            for j in range(top.childCount()):
                child = top.child(j)
                if child is not None:
                    result.append(child)
        return result

    def refresh_ui(self) -> None:
        self.lbl_layout_mode.setText(tr("info_layout_mode_label"))
        self.edit_search.setPlaceholderText(tr("info_search_placeholder"))
        self.edit_tag_filter.setPlaceholderText(tr("info_tag_placeholder"))
        self.chk_open_only.setText(tr("info_open_tasks_only"))
        self.chk_star_only.setText(tr("info_star_only"))
        self.btn_refresh.setText(tr("info_refresh"))
        self.btn_toggle_star.setText(tr("info_toggle_star"))
        self.lbl_mode.setText(tr("info_mode_label"))
        self.lbl_due_filter.setText(tr("info_due_filter_label"))
        self.lbl_sort.setText(tr("info_sort_label"))
        self.advanced_filters_box.setText(tr("info_advanced_filters"))
        self.btn_complete_selected.setText(tr("info_bulk_complete_selected"))
        self.btn_uncomplete_selected.setText(tr("info_bulk_uncomplete_selected"))
        self.btn_archive_selected.setText(tr("info_bulk_archive_selected"))
        self.btn_restore_selected.setText(tr("info_bulk_restore_selected"))
        self.btn_star_selected.setText(tr("info_bulk_star_selected"))
        self.btn_unstar_selected.setText(tr("info_bulk_unstar_selected"))
        self.btn_edit_tags_selected.setText(tr("info_bulk_edit_tags_selected"))
        self.btn_sort_desc.setText(tr("info_sort_desc"))
        self.lbl_preset.setText(tr("info_view_preset_label"))
        self.lbl_smart_view.setText(tr("info_smart_view_label"))
        self.lbl_archive_scope.setText(tr("info_archive_scope_label"))
        self.btn_preset_actions.setText(tr("info_view_actions"))
        self.btn_bulk_actions.setText(tr("info_bulk_actions_menu"))
        self.btn_view_save.setText(tr("info_view_save"))
        self.btn_view_update.setText(tr("info_view_update"))
        self.btn_view_delete.setText(tr("info_view_delete"))
        self.btn_open_operations.setText(tr("info_recent_operations_open"))
        self.btn_empty_add_text.setText(tr("menu_add_text"))
        if self._operations_dialog is not None:
            self._operations_dialog.refresh_ui()

        builtin_presets = self._build_builtin_presets()
        for preset_id, preset in builtin_presets.items():
            self._view_presets[preset_id] = preset

        for key, text_key in [
            ("all", "info_view_all"),
            ("open", "info_view_open"),
            ("today", "info_view_today"),
            ("overdue", "info_view_overdue"),
            ("starred", "info_view_starred"),
            ("archived", "info_view_archived"),
        ]:
            btn = self._smart_view_buttons.get(key)
            if btn is not None:
                btn.setText(tr(text_key))

        self._reload_mode_combo_items()
        self._reload_due_combo_items()
        self._reload_archive_scope_combo_items()
        self._reload_sort_combo_items()
        self._reload_layout_mode_combo_items()
        self._set_combo_data(self.cmb_layout_mode, self._layout_mode)
        self._reload_smart_view_combo_items()
        self._reload_view_preset_combo_items()
        self._apply_preset_by_id(self._current_preset_id, refresh=False, persist_last=False)
        self._apply_layout_mode(force=True)

        self.subtabs.setTabText(0, tr("info_tasks_tab"))
        self.subtabs.setTabText(1, tr("info_notes_tab"))
        self._invalidate_refresh_signatures()
        self.refresh_data(immediate=True)
