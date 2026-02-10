from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from managers.info_index_manager import InfoIndexManager, InfoQuery, NoteIndexItem, TaskIndexItem
from utils.translator import tr


class InfoTab(QWidget):
    """タスク/ノートを横断表示する情報管理タブ。"""

    def __init__(self, main_window: Any):
        super().__init__()
        self.mw = main_window
        self.index_manager = InfoIndexManager()

        self._current_selected_uuid: str = ""
        self._is_refreshing = False
        self._setup_ui()
        self.refresh_data()

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

        self.btn_refresh = QPushButton(tr("info_refresh"))
        self.btn_refresh.setObjectName("ActionBtn")
        self.btn_refresh.clicked.connect(self.refresh_data)

        filter_layout.addWidget(self.edit_search, 0, 0, 1, 2)
        filter_layout.addWidget(self.edit_tag_filter, 1, 0, 1, 2)
        filter_layout.addWidget(self.chk_open_only, 2, 0)
        filter_layout.addWidget(self.chk_star_only, 2, 1)
        filter_layout.addWidget(self.btn_refresh, 3, 0, 1, 2)

        layout.addWidget(self.filter_group)

        self.subtabs = QTabWidget()

        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        self.tasks_list = QListWidget()
        self.tasks_list.itemChanged.connect(self._on_task_item_changed)
        self.tasks_list.itemDoubleClicked.connect(self._on_task_item_activated)
        tasks_layout.addWidget(self.tasks_list)
        self.subtabs.addTab(self.tasks_tab, tr("info_tasks_tab"))

        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)

        self.notes_list = QListWidget()
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

        layout.addStretch()

    def _build_query(self) -> InfoQuery:
        return InfoQuery(
            text=self.edit_search.text().strip(),
            tag=self.edit_tag_filter.text().strip(),
            starred_only=self.chk_star_only.isChecked(),
            open_tasks_only=self.chk_open_only.isChecked(),
            include_archived=False,
        )

    def _iter_text_windows(self) -> list[Any]:
        wm = getattr(self.mw, "window_manager", None)
        if wm is None:
            return []
        return list(getattr(wm, "text_windows", []) or [])

    def refresh_data(self) -> None:
        if self._is_refreshing:
            return

        self._is_refreshing = True
        try:
            task_items, note_items = self.index_manager.build_index(self._iter_text_windows())
            query = self._build_query()
            filtered_tasks = self.index_manager.query_tasks(task_items, query)
            filtered_notes = self.index_manager.query_notes(note_items, query)

            self._populate_tasks(filtered_tasks)
            self._populate_notes(filtered_notes)
        finally:
            self._is_refreshing = False

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

    def _on_task_item_changed(self, item: QListWidgetItem) -> None:
        if self._is_refreshing:
            return
        item_key = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not item_key:
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
        self.refresh_data()

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
        self.refresh_data()

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
        self.refresh_data()

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

        self.subtabs.setTabText(0, tr("info_tasks_tab"))
        self.subtabs.setTabText(1, tr("info_notes_tab"))
        self.refresh_data()
