from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class SceneTab(QWidget):
    """シーン・カテゴリ管理タブ。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.scene_group = QGroupBox(tr("grp_scene_list"))
        group_layout = QVBoxLayout(self.scene_group)
        group_layout.setContentsMargins(10, 15, 10, 10)

        self.scene_category_tabs = QTabWidget()
        group_layout.addWidget(self.scene_category_tabs)

        layout.addWidget(self.scene_group)

        btn_layout = QGridLayout()
        btn_layout.setSpacing(10)

        # ボタン定義: (text_key, slot, r, c, rs, cs)
        # text_key は tr() で解決
        scene_btns_def = [
            ("btn_add_category", self.mw.main_controller.scene_actions.add_new_category, 0, 0, 1, 2),
            ("btn_add_scene", self.mw.main_controller.scene_actions.add_new_scene, 1, 0, 1, 2),
            ("btn_load_scene", self.mw.main_controller.scene_actions.load_selected_scene, 2, 0, 1, 1),
            ("btn_update_scene", self.mw.main_controller.scene_actions.update_selected_scene, 2, 1, 1, 1),
            ("btn_close_scene", self.mw.main_controller.bulk_manager.close_all_everything, 3, 0, 1, 2),
            ("btn_delete_scene", self.mw.main_controller.scene_actions.delete_selected_item, 4, 0, 1, 2),
        ]

        self.btn_map = {}  # 互換性のため保持

        for key, slot, r, c, rs, cs in scene_btns_def:
            text = tr(key)
            btn = QPushButton(text)
            btn.setObjectName("DangerBtn" if key == "btn_delete_scene" else "ActionBtn")
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn, r, c, rs, cs)

            # 各ボタンを特定するためのマッピング
            self.btn_map[key] = btn

        layout.addLayout(btn_layout)

        # ヒント
        self.scene_hint_label = QLabel(tr("hint_scene_tab_usage"))
        self.scene_hint_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        self.scene_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.scene_hint_label)

        layout.addStretch()

    def refresh_ui(self) -> None:
        """UI文言更新"""
        self.scene_group.setTitle(tr("grp_scene_list"))

        if "btn_add_category" in self.btn_map:
            self.btn_map["btn_add_category"].setText(tr("btn_add_category"))
        if "btn_add_scene" in self.btn_map:
            self.btn_map["btn_add_scene"].setText(tr("btn_add_scene"))
        if "btn_load_scene" in self.btn_map:
            self.btn_map["btn_load_scene"].setText(tr("btn_load_scene"))
        if "btn_update_scene" in self.btn_map:
            self.btn_map["btn_update_scene"].setText(tr("btn_update_scene"))
        if "btn_close_scene" in self.btn_map:
            self.btn_map["btn_close_scene"].setText(tr("btn_close_scene"))
        if "btn_delete_scene" in self.btn_map:
            self.btn_map["btn_delete_scene"].setText(tr("btn_delete_scene"))

        self.scene_hint_label.setText(tr("hint_scene_tab_usage"))

    def get_current_category(self) -> str:
        """現在選択中のカテゴリー名を取得。"""
        idx = self.scene_category_tabs.currentIndex()
        if idx < 0:
            return ""
        return self.scene_category_tabs.tabText(idx)

    def get_current_scene(self) -> str:
        """現在選択中のシーン名を取得。"""
        current_list = self.scene_category_tabs.currentWidget()
        if not current_list:
            return ""
        # QListWidget 前提
        item = current_list.currentItem()
        if not item:
            return ""
        return item.text()

    def refresh_category_list(self) -> None:
        """カテゴリリスト（タブ）を再構築。"""
        if hasattr(self.mw, "refresh_scene_tabs"):
            self.mw.refresh_scene_tabs()

    def refresh_scene_list(self) -> None:
        """シーンリストを更新。"""
        # カテゴリ内リストだけ更新するのが理想だが、簡易実装として全体リフレッシュ
        if hasattr(self.mw, "refresh_scene_tabs"):
            self.mw.refresh_scene_tabs()


class ConnectionsTab(QWidget):
    """コネクタ(Line/Label)管理タブ。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # =========================
        # Selected
        # =========================
        self.conn_grp_selected = QGroupBox(tr("anim_target_selected"))
        grid_sel = QGridLayout(self.conn_grp_selected)

        self.conn_selected_label = QLabel(tr("label_anim_selected_none"))
        self.conn_selected_label.setWordWrap(True)
        grid_sel.addWidget(self.conn_selected_label, 0, 0, 1, 2)

        # --- Line操作 ---
        self.conn_btn_sel_delete = QPushButton(tr("menu_delete_line"))
        self.conn_btn_sel_delete.setObjectName("DangerBtn")
        self.conn_btn_sel_delete.setEnabled(False)
        self.conn_btn_sel_delete.clicked.connect(self.delete_selected)

        self.conn_btn_sel_color = QPushButton(tr("menu_line_color"))
        self.conn_btn_sel_color.setObjectName("ActionBtn")
        self.conn_btn_sel_color.setEnabled(False)
        self.conn_btn_sel_color.clicked.connect(self.change_color_selected)

        self.conn_btn_sel_width = QPushButton(tr("menu_line_width"))
        self.conn_btn_sel_width.setObjectName("ActionBtn")
        self.conn_btn_sel_width.setEnabled(False)
        self.conn_btn_sel_width.clicked.connect(self.open_width_dialog_selected)

        self.conn_btn_sel_opacity = QPushButton(tr("menu_line_opacity"))
        self.conn_btn_sel_opacity.setObjectName("ActionBtn")
        self.conn_btn_sel_opacity.setEnabled(False)
        self.conn_btn_sel_opacity.clicked.connect(self.open_opacity_dialog_selected)

        grid_sel.addWidget(self.conn_btn_sel_color, 1, 0)
        grid_sel.addWidget(self.conn_btn_sel_width, 1, 1)
        grid_sel.addWidget(self.conn_btn_sel_opacity, 2, 0)
        grid_sel.addWidget(self.conn_btn_sel_delete, 2, 1)

        # --- Label操作 ---
        self.conn_btn_label_edit = QPushButton(tr("menu_add_label"))
        self.conn_btn_label_edit.setObjectName("ActionBtn")
        self.conn_btn_label_edit.setEnabled(False)
        self.conn_btn_label_edit.clicked.connect(lambda: self.label_action_selected("edit"))

        self.conn_btn_label_toggle = QPushButton(tr("menu_toggle_label"))
        self.conn_btn_label_toggle.setObjectName("ActionBtn")
        self.conn_btn_label_toggle.setEnabled(False)
        self.conn_btn_label_toggle.clicked.connect(lambda: self.label_action_selected("toggle"))

        grid_sel.addWidget(self.conn_btn_label_edit, 3, 0)
        grid_sel.addWidget(self.conn_btn_label_toggle, 3, 1)

        # --- ArrowStyle ---
        self.conn_btn_arrow_none = QPushButton(tr("menu_arrow_none"))
        self.conn_btn_arrow_none.setObjectName("ActionBtn")
        self.conn_btn_arrow_none.setCheckable(True)
        self.conn_btn_arrow_none.setEnabled(False)
        self.conn_btn_arrow_none.clicked.connect(lambda: self.set_arrow_style_selected("none"))

        self.conn_btn_arrow_start = QPushButton(tr("menu_arrow_start"))
        self.conn_btn_arrow_start.setObjectName("ActionBtn")
        self.conn_btn_arrow_start.setCheckable(True)
        self.conn_btn_arrow_start.setEnabled(False)
        self.conn_btn_arrow_start.clicked.connect(lambda: self.set_arrow_style_selected("start"))

        self.conn_btn_arrow_end = QPushButton(tr("menu_arrow_end"))
        self.conn_btn_arrow_end.setObjectName("ActionBtn")
        self.conn_btn_arrow_end.setCheckable(True)
        self.conn_btn_arrow_end.setEnabled(False)
        self.conn_btn_arrow_end.clicked.connect(lambda: self.set_arrow_style_selected("end"))

        self.conn_btn_arrow_both = QPushButton(tr("menu_arrow_both"))
        self.conn_btn_arrow_both.setObjectName("ActionBtn")
        self.conn_btn_arrow_both.setCheckable(True)
        self.conn_btn_arrow_both.setEnabled(False)
        self.conn_btn_arrow_both.clicked.connect(lambda: self.set_arrow_style_selected("both"))

        self.conn_arrow_group = QButtonGroup(self)
        self.conn_arrow_group.setExclusive(True)
        self.conn_arrow_group.addButton(self.conn_btn_arrow_none)
        self.conn_arrow_group.addButton(self.conn_btn_arrow_start)
        self.conn_arrow_group.addButton(self.conn_btn_arrow_end)
        self.conn_arrow_group.addButton(self.conn_btn_arrow_both)

        grid_sel.addWidget(self.conn_btn_arrow_none, 4, 0)
        grid_sel.addWidget(self.conn_btn_arrow_start, 4, 1)
        grid_sel.addWidget(self.conn_btn_arrow_end, 5, 0)
        grid_sel.addWidget(self.conn_btn_arrow_both, 5, 1)

        layout.addWidget(self.conn_grp_selected)

        # =========================
        # Bulk（All Connectors）
        # =========================
        self.conn_grp_bulk = QGroupBox(tr("grp_connector_settings"))
        grid_bulk = QGridLayout(self.conn_grp_bulk)

        self.conn_btn_bulk_color = QPushButton(tr("menu_line_color"))
        self.conn_btn_bulk_color.setObjectName("ActionBtn")
        self.conn_btn_bulk_color.clicked.connect(self.bulk_change_color)

        self.conn_btn_bulk_width = QPushButton(tr("menu_line_width"))
        self.conn_btn_bulk_width.setObjectName("ActionBtn")
        self.conn_btn_bulk_width.clicked.connect(self.bulk_open_width_dialog)

        self.conn_btn_bulk_opacity = QPushButton(tr("menu_line_opacity"))
        self.conn_btn_bulk_opacity.setObjectName("ActionBtn")
        self.conn_btn_bulk_opacity.clicked.connect(self.bulk_open_opacity_dialog)

        grid_bulk.addWidget(self.conn_btn_bulk_color, 0, 0)
        grid_bulk.addWidget(self.conn_btn_bulk_width, 0, 1)
        grid_bulk.addWidget(self.conn_btn_bulk_opacity, 1, 0, 1, 2)

        layout.addWidget(self.conn_grp_bulk)

        layout.addStretch()

    def refresh_ui(self) -> None:
        """UI文言更新"""
        self.conn_grp_selected.setTitle(tr("anim_target_selected"))
        self.conn_btn_sel_delete.setText(tr("menu_delete_line"))
        self.conn_btn_sel_color.setText(tr("menu_line_color"))
        self.conn_btn_sel_width.setText(tr("menu_line_width"))
        self.conn_btn_sel_opacity.setText(tr("menu_line_opacity"))
        self.conn_btn_label_edit.setText(tr("menu_add_label"))
        self.conn_btn_label_toggle.setText(tr("menu_toggle_label"))

        self.conn_btn_arrow_none.setText(tr("menu_arrow_none"))
        self.conn_btn_arrow_start.setText(tr("menu_arrow_start"))
        self.conn_btn_arrow_end.setText(tr("menu_arrow_end"))
        self.conn_btn_arrow_both.setText(tr("menu_arrow_both"))

        self.conn_grp_bulk.setTitle(tr("grp_connector_settings"))
        self.conn_btn_bulk_color.setText(tr("menu_line_color"))
        self.conn_btn_bulk_width.setText(tr("menu_line_width"))
        self.conn_btn_bulk_opacity.setText(tr("menu_line_opacity"))

    def on_selection_changed(self, obj: Optional[Any]) -> None:
        """
        Selected 表示を更新する。
        - ConnectorLine が選択されたら、その線を Selected として表示
        - ConnectorLabel が選択されたら、その親 ConnectorLine を Selected として表示
        """
        selected_line = None
        selected_label = None

        if obj is not None:
            try:
                from windows.connector import ConnectorLabel, ConnectorLine

                if isinstance(obj, ConnectorLine):
                    selected_line = obj
                elif isinstance(obj, ConnectorLabel):
                    selected_label = obj
                    selected_line = getattr(obj, "connector", None)
            except Exception:
                tname = type(obj).__name__
                if tname == "ConnectorLine":
                    selected_line = obj
                elif tname == "ConnectorLabel":
                    selected_label = obj
                    selected_line = getattr(obj, "connector", None)

        # 表示名を作る
        if selected_line is None:
            self.conn_selected_label.setText(tr("label_anim_selected_none"))
            # self.mw.last_selected_connector = None # これを変更すべきかは要検討だが、MainWindow側で管理しているならいじらない方が無難？
            # -> ConnectorActionsがmw.last_selected_connectorを見るので、本来は合わせるべき。
            # しかし on_selection_changed は選択が変わった後に呼ばれるので、すでに mw.last_selected_window 等は更新されているはず。
            # mw.last_selected_connector は ConnectorActions 専用のキャッシュに近い。更新しておく。
            if hasattr(self.mw, "last_selected_connector"):
                self.mw.last_selected_connector = None

            self._refresh_enabled_state(obj)

            # Arrowチェックも落とす
            for btn in (
                self.conn_btn_arrow_none,
                self.conn_btn_arrow_start,
                self.conn_btn_arrow_end,
                self.conn_btn_arrow_both,
            ):
                try:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                finally:
                    btn.blockSignals(False)

            return

        # 端点情報を可能なら付ける
        extra = ""
        try:
            sw = getattr(selected_line, "start_window", None)
            ew = getattr(selected_line, "end_window", None)

            def _name_for_window(w: Any) -> str:
                if w is None:
                    return "?"
                if hasattr(w, "get_filename"):
                    return str(w.get_filename())
                if hasattr(w, "text"):
                    s = str(getattr(w, "text", "") or "").split("\n")[0].strip()
                    if s:
                        return (s[:20] + "...") if len(s) > 20 else s
                if hasattr(w, "uuid"):
                    u = str(getattr(w, "uuid", "") or "")
                    return u[:8] if u else type(w).__name__
                return type(w).__name__

            extra = f" ({_name_for_window(sw)} -> {_name_for_window(ew)})"
        except Exception:
            extra = ""

        base_name = "Connector"
        if selected_label is not None:
            base_name = "Label / Connector"

        self.conn_selected_label.setText(tr("label_anim_selected_fmt").format(name=base_name + extra))

        if hasattr(self.mw, "last_selected_connector"):
            self.mw.last_selected_connector = selected_line

        self._refresh_enabled_state(obj)

        # -------------------------
        # ArrowStyle のチェック同期
        # -------------------------
        try:
            from models.enums import ArrowStyle

            current = getattr(selected_line, "arrow_style", ArrowStyle.NONE)

            mapping = {
                self.conn_btn_arrow_none: ArrowStyle.NONE,
                self.conn_btn_arrow_start: ArrowStyle.START,
                self.conn_btn_arrow_end: ArrowStyle.END,
                self.conn_btn_arrow_both: ArrowStyle.BOTH,
            }

            for btn, style in mapping.items():
                btn.blockSignals(True)
                btn.setChecked(current == style)
                btn.blockSignals(False)
        except Exception:
            # Fallback
            try:
                s = str(getattr(selected_line, "arrow_style", ""))

                def _endswith(name: str) -> bool:
                    return s.endswith(name) or (name in s)

                checks = {
                    self.conn_btn_arrow_none: _endswith("NONE"),
                    self.conn_btn_arrow_start: _endswith("START"),
                    self.conn_btn_arrow_end: _endswith("END"),
                    self.conn_btn_arrow_both: _endswith("BOTH"),
                }

                for btn, on in checks.items():
                    btn.blockSignals(True)
                    btn.setChecked(bool(on))
                    btn.blockSignals(False)
            except Exception:
                pass

    def _refresh_enabled_state(self, obj: Optional[Any]) -> None:
        """ボタンの有効/無効を更新"""
        enabled = False
        if obj is not None:
            try:
                from windows.connector import ConnectorLabel, ConnectorLine

                enabled = isinstance(obj, (ConnectorLine, ConnectorLabel))
            except Exception:
                enabled = type(obj).__name__ in ("ConnectorLine", "ConnectorLabel")

        for btn in (
            self.conn_btn_sel_delete,
            self.conn_btn_sel_color,
            self.conn_btn_sel_width,
            self.conn_btn_sel_opacity,
            self.conn_btn_label_edit,
            self.conn_btn_label_toggle,
            self.conn_btn_arrow_none,
            self.conn_btn_arrow_start,
            self.conn_btn_arrow_end,
            self.conn_btn_arrow_both,
        ):
            btn.setEnabled(bool(enabled))

    # 各種アクションは Controller へ委譲
    def delete_selected(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.delete_selected()

    def change_color_selected(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.change_color_selected()

    def open_width_dialog_selected(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.open_width_dialog_selected()

    def open_opacity_dialog_selected(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.open_opacity_dialog_selected()

    def label_action_selected(self, action: str) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.label_action_selected(action)

    def set_arrow_style_selected(self, style_key: str) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.set_arrow_style_selected(style_key)

    def bulk_change_color(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.bulk_change_color()

    def bulk_open_width_dialog(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.bulk_open_width_dialog()

    def bulk_open_opacity_dialog(self) -> None:
        if hasattr(self.mw.main_controller, "connector_actions"):
            self.mw.main_controller.connector_actions.bulk_open_opacity_dialog()
