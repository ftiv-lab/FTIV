from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from managers.info_index_manager import InfoIndexManager, InfoQuery, InfoStats, NoteIndexItem, TaskIndexItem
from utils.translator import tr


class InfoTab(QWidget):
    """タスク/ノートを横断表示する情報管理タブ。"""

    def __init__(self, main_window: Any):
        super().__init__()
        self.mw = main_window
        self.index_manager = InfoIndexManager()

        self._current_selected_uuid: str = ""
        self._is_refreshing = False
        self._smart_view = "all"
        self._smart_view_buttons: dict[str, QPushButton] = {}

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._refresh_now)

        self._setup_ui()
        self.refresh_data(immediate=True)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.filter_group = QGroupBox(tr("grp_info_filters"))
        filter_layout = QGridLayout(self.filter_group)

        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText(tr("info_search_placeholder"))
        self.edit_search.textChanged.connect(self.refresh_data)

        self.edit_tag_filter = QLineEdit()
        self.edit_tag_filter.setPlaceholderText(tr("info_tag_placeholder"))
        self.edit_tag_filter.textChanged.connect(self.refresh_data)

        self.chk_open_only = QCheckBox(tr("info_open_tasks_only"))
        self.chk_open_only.toggled.connect(self.refresh_data)

        self.chk_star_only = QCheckBox(tr("info_star_only"))
        self.chk_star_only.toggled.connect(self.refresh_data)

        self._smart_view_group = QButtonGroup(self)
        self._smart_view_group.setExclusive(True)
        smart_view_row = QWidget()
        smart_view_layout = QHBoxLayout(smart_view_row)
        smart_view_layout.setContentsMargins(0, 0, 0, 0)
        smart_view_layout.setSpacing(4)
        for key, text_key in [
            ("all", "info_view_all"),
            ("open", "info_view_open"),
            ("today", "info_view_today"),
            ("overdue", "info_view_overdue"),
            ("starred", "info_view_starred"),
        ]:
            btn = QPushButton(tr(text_key))
            btn.setCheckable(True)
            btn.setProperty("class", "toggle")
            btn.clicked.connect(lambda checked, view_key=key: self._set_smart_view(view_key) if checked else None)
            self._smart_view_group.addButton(btn)
            self._smart_view_buttons[key] = btn
            smart_view_layout.addWidget(btn)
        self._set_smart_view("all")

        self.cmb_sort_by = QComboBox()
        self._reload_sort_combo_items()
        self.cmb_sort_by.currentIndexChanged.connect(self.refresh_data)

        self.btn_sort_desc = QPushButton(tr("info_sort_desc"))
        self.btn_sort_desc.setCheckable(True)
        self.btn_sort_desc.setChecked(True)
        self.btn_sort_desc.setProperty("class", "toggle")
        self.btn_sort_desc.toggled.connect(self.refresh_data)

        sort_row = QWidget()
        sort_layout = QHBoxLayout(sort_row)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        sort_layout.setSpacing(4)
        sort_layout.addWidget(QLabel(tr("info_sort_label")))
        sort_layout.addWidget(self.cmb_sort_by, 1)
        sort_layout.addWidget(self.btn_sort_desc)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setProperty("class", "info-label")

        self.btn_refresh = QPushButton(tr("info_refresh"))
        self.btn_refresh.setObjectName("ActionBtn")
        self.btn_refresh.clicked.connect(lambda: self.refresh_data(immediate=True))

        filter_layout.addWidget(self.edit_search, 0, 0, 1, 3)
        filter_layout.addWidget(self.edit_tag_filter, 1, 0, 1, 3)
        filter_layout.addWidget(self.chk_open_only, 2, 0)
        filter_layout.addWidget(self.chk_star_only, 2, 1)
        filter_layout.addWidget(self.btn_refresh, 2, 2)
        filter_layout.addWidget(smart_view_row, 3, 0, 1, 3)
        filter_layout.addWidget(sort_row, 4, 0, 1, 3)
        filter_layout.addWidget(self.lbl_stats, 5, 0, 1, 3)

        layout.addWidget(self.filter_group)

        self.subtabs = QTabWidget()

        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        self.tasks_list = QListWidget()
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tasks_list.itemChanged.connect(self._on_task_item_changed)
        self.tasks_list.itemDoubleClicked.connect(self._on_task_item_activated)
        tasks_layout.addWidget(self.tasks_list)
        self.subtabs.addTab(self.tasks_tab, tr("info_tasks_tab"))

        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)

        self.notes_list = QListWidget()
        self.notes_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.notes_list.itemChanged.connect(self._on_note_item_changed)
        self.notes_list.itemDoubleClicked.connect(self._on_note_item_activated)
        notes_layout.addWidget(self.notes_list)

        notes_btn_row = QHBoxLayout()
        self.btn_toggle_star = QPushButton(tr("info_toggle_star"))
        self.btn_toggle_star.setObjectName("ActionBtn")
        self.btn_toggle_star.clicked.connect(self._toggle_selected_note_star)
        notes_btn_row.addWidget(self.btn_toggle_star)
        notes_btn_row.addStretch()
        notes_layout.addLayout(notes_btn_row)

        self.subtabs.addTab(self.notes_tab, tr("info_notes_tab"))
        layout.addWidget(self.subtabs)

        bulk_row = QHBoxLayout()
        self.btn_complete_selected = QPushButton(tr("info_bulk_complete_selected"))
        self.btn_complete_selected.setObjectName("ActionBtn")
        self.btn_complete_selected.clicked.connect(lambda: self._apply_bulk_task_done(True))
        bulk_row.addWidget(self.btn_complete_selected)

        self.btn_uncomplete_selected = QPushButton(tr("info_bulk_uncomplete_selected"))
        self.btn_uncomplete_selected.setObjectName("ActionBtn")
        self.btn_uncomplete_selected.clicked.connect(lambda: self._apply_bulk_task_done(False))
        bulk_row.addWidget(self.btn_uncomplete_selected)

        self.btn_archive_selected = QPushButton(tr("info_bulk_archive_selected"))
        self.btn_archive_selected.setObjectName("ActionBtn")
        self.btn_archive_selected.clicked.connect(self._archive_selected)
        bulk_row.addWidget(self.btn_archive_selected)

        bulk_row.addStretch()
        layout.addLayout(bulk_row)
        layout.addStretch()

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

    def _set_smart_view(self, view_key: str) -> None:
        normalized = str(view_key or "").strip().lower()
        if normalized not in self._smart_view_buttons:
            normalized = "all"
        self._smart_view = normalized
        for key, btn in self._smart_view_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(key == normalized)
            btn.blockSignals(False)
        self.refresh_data()

    def _build_query(self) -> InfoQuery:
        due_filter = "all"
        open_only = self.chk_open_only.isChecked()
        starred_only = self.chk_star_only.isChecked()

        if self._smart_view == "open":
            open_only = True
        elif self._smart_view == "today":
            due_filter = "today"
        elif self._smart_view == "overdue":
            due_filter = "overdue"
            open_only = True
        elif self._smart_view == "starred":
            starred_only = True

        sort_by = str(self.cmb_sort_by.currentData() or "updated")

        return InfoQuery(
            text=self.edit_search.text().strip(),
            tag=self.edit_tag_filter.text().strip(),
            starred_only=starred_only,
            open_tasks_only=open_only,
            include_archived=False,
            due_filter=due_filter,
            mode_filter="all",
            sort_by=sort_by,
            sort_desc=self.btn_sort_desc.isChecked(),
        )

    def _iter_text_windows(self) -> list[Any]:
        wm = getattr(self.mw, "window_manager", None)
        if wm is None:
            return []
        return list(getattr(wm, "text_windows", []) or [])

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
            task_items, note_items = self.index_manager.build_index(self._iter_text_windows())
            query = self._build_query()
            filtered_tasks = self.index_manager.query_tasks(task_items, query)
            filtered_notes = self.index_manager.query_notes(note_items, query)
            stats = self.index_manager.build_stats(filtered_tasks, filtered_notes)

            self._populate_tasks(filtered_tasks)
            self._populate_notes(filtered_notes)
            self._update_stats(stats)
        finally:
            self._is_refreshing = False

    @staticmethod
    def _due_label_text(due_at: str) -> str:
        raw = str(due_at or "").strip()
        if not raw:
            return ""
        try:
            return datetime.fromisoformat(raw).date().isoformat()
        except Exception:
            return raw

    def _populate_tasks(self, items: list[TaskIndexItem]) -> None:
        self.tasks_list.blockSignals(True)
        try:
            self.tasks_list.clear()
            if not items:
                empty = QListWidgetItem(tr("info_list_empty"))
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                self.tasks_list.addItem(empty)
                return

            for item in items:
                text = tr("info_task_item_fmt").format(title=item.title, text=item.text)
                due_text = self._due_label_text(item.due_at)
                if due_text:
                    text = f"{text}  ({tr('info_due_short_fmt').format(date=due_text)})"

                lw_item = QListWidgetItem(text)
                lw_item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                )
                lw_item.setCheckState(Qt.CheckState.Checked if item.done else Qt.CheckState.Unchecked)
                lw_item.setData(Qt.ItemDataRole.UserRole, item.item_key)
                lw_item.setData(Qt.ItemDataRole.UserRole + 1, bool(item.done))
                lw_item.setData(Qt.ItemDataRole.UserRole + 2, item.window_uuid)
                self.tasks_list.addItem(lw_item)
        finally:
            self.tasks_list.blockSignals(False)

    def _populate_notes(self, items: list[NoteIndexItem]) -> None:
        self.notes_list.blockSignals(True)
        try:
            self.notes_list.clear()
            if not items:
                empty = QListWidgetItem(tr("info_list_empty"))
                empty.setFlags(Qt.ItemFlag.NoItemFlags)
                self.notes_list.addItem(empty)
                return

            for item in items:
                mode_text = (
                    tr("label_content_mode_task") if item.content_mode == "task" else tr("label_content_mode_note")
                )
                line = tr("info_note_item_fmt").format(
                    title=item.title,
                    mode=mode_text,
                    first_line=item.first_line,
                )
                due_text = self._due_label_text(item.due_at)
                if due_text:
                    line = f"{line}  ({tr('info_due_short_fmt').format(date=due_text)})"

                lw_item = QListWidgetItem(line)
                lw_item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
                )
                lw_item.setCheckState(Qt.CheckState.Checked if item.is_starred else Qt.CheckState.Unchecked)
                lw_item.setData(Qt.ItemDataRole.UserRole, item.window_uuid)
                lw_item.setData(Qt.ItemDataRole.UserRole + 1, bool(item.is_starred))
                self.notes_list.addItem(lw_item)

                if item.window_uuid and item.window_uuid == self._current_selected_uuid:
                    lw_item.setSelected(True)
        finally:
            self.notes_list.blockSignals(False)

    def _update_stats(self, stats: InfoStats) -> None:
        self.lbl_stats.setText(
            tr("info_stats_fmt").format(
                open=stats.open_tasks,
                done=stats.done_tasks,
                overdue=stats.overdue_tasks,
                starred=stats.starred_notes,
            )
        )

    def _on_task_item_changed(self, item: QListWidgetItem) -> None:
        if self._is_refreshing:
            return
        item_key = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if ":" not in item_key:
            return

        prev_done = bool(item.data(Qt.ItemDataRole.UserRole + 1))
        next_done = item.checkState() == Qt.CheckState.Checked
        if prev_done == next_done:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.toggle_task(item_key)
            return

        # Fallback: no action handler
        self.refresh_data(immediate=True)

    def _on_task_item_activated(self, item: QListWidgetItem) -> None:
        window_uuid = str(item.data(Qt.ItemDataRole.UserRole + 2) or "")
        if not window_uuid:
            item_key = str(item.data(Qt.ItemDataRole.UserRole) or "")
            if ":" in item_key:
                window_uuid = item_key.rsplit(":", 1)[0]
        if not window_uuid:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.focus_window(window_uuid)

    def _on_note_item_changed(self, item: QListWidgetItem) -> None:
        if self._is_refreshing:
            return
        window_uuid = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        prev_star = bool(item.data(Qt.ItemDataRole.UserRole + 1))
        next_star = item.checkState() == Qt.CheckState.Checked
        if prev_star == next_star:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.set_star(window_uuid, next_star)
            return

        # Fallback: no action handler
        self.refresh_data(immediate=True)

    def _on_note_item_activated(self, item: QListWidgetItem) -> None:
        window_uuid = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.focus_window(window_uuid)

    def _toggle_selected_note_star(self) -> None:
        item = self.notes_list.currentItem()
        if item is None:
            return
        window_uuid = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not window_uuid:
            return
        current = item.checkState() == Qt.CheckState.Checked

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.set_star(window_uuid, not current)
        self.refresh_data(immediate=True)

    def _selected_task_item_keys(self) -> list[str]:
        keys: list[str] = []
        for item in self.tasks_list.selectedItems():
            item_key = str(item.data(Qt.ItemDataRole.UserRole) or "")
            if ":" in item_key:
                keys.append(item_key)
        return keys

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
        uuids: set[str] = set()

        for item in self.notes_list.selectedItems():
            window_uuid = str(item.data(Qt.ItemDataRole.UserRole) or "")
            if window_uuid:
                uuids.add(window_uuid)

        for item in self.tasks_list.selectedItems():
            window_uuid = str(item.data(Qt.ItemDataRole.UserRole + 2) or "")
            if not window_uuid:
                item_key = str(item.data(Qt.ItemDataRole.UserRole) or "")
                if ":" in item_key:
                    window_uuid = item_key.rsplit(":", 1)[0]
            if window_uuid:
                uuids.add(window_uuid)

        if not uuids:
            return

        actions = getattr(self.mw.main_controller, "info_actions", None)
        if actions is not None:
            actions.bulk_archive(sorted(uuids), True)
            return
        self.refresh_data(immediate=True)

    def on_selection_changed(self, window: Optional[Any]) -> None:
        self._current_selected_uuid = str(getattr(window, "uuid", "") or "") if window is not None else ""
        if not self._current_selected_uuid:
            return
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if not item:
                continue
            selected = str(item.data(Qt.ItemDataRole.UserRole) or "") == self._current_selected_uuid
            item.setSelected(selected)
            if selected:
                self.notes_list.scrollToItem(item)

    def refresh_ui(self) -> None:
        self.filter_group.setTitle(tr("grp_info_filters"))
        self.edit_search.setPlaceholderText(tr("info_search_placeholder"))
        self.edit_tag_filter.setPlaceholderText(tr("info_tag_placeholder"))
        self.chk_open_only.setText(tr("info_open_tasks_only"))
        self.chk_star_only.setText(tr("info_star_only"))
        self.btn_refresh.setText(tr("info_refresh"))
        self.btn_toggle_star.setText(tr("info_toggle_star"))
        self.btn_complete_selected.setText(tr("info_bulk_complete_selected"))
        self.btn_uncomplete_selected.setText(tr("info_bulk_uncomplete_selected"))
        self.btn_archive_selected.setText(tr("info_bulk_archive_selected"))
        self.btn_sort_desc.setText(tr("info_sort_desc"))

        for key, text_key in [
            ("all", "info_view_all"),
            ("open", "info_view_open"),
            ("today", "info_view_today"),
            ("overdue", "info_view_overdue"),
            ("starred", "info_view_starred"),
        ]:
            btn = self._smart_view_buttons.get(key)
            if btn is not None:
                btn.setText(tr(text_key))

        self._reload_sort_combo_items()

        self.subtabs.setTabText(0, tr("info_tasks_tab"))
        self.subtabs.setTabText(1, tr("info_notes_tab"))
        self.refresh_data(immediate=True)
