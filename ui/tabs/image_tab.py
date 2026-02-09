from functools import partial
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils.translator import tr

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class ImageTab(QWidget):
    """画像管理タブ。MainWindowから分離・クラス化。"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.mw = main_window

        # Forward declaration for Mypy type inference
        self.img_sel_display_combo: Optional[QComboBox] = None

        # 変換タブのインデックス保持用 (旧 mw._img_transform_sel_tab_index)
        self._transform_sel_tab_index = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 1) ヘッダー
        self.btn_add_image_main = QPushButton("+ " + tr("menu_add_image"))
        self.btn_add_image_main.setMinimumHeight(50)
        self.btn_add_image_main.setProperty("class", "large-button")
        self.btn_add_image_main.clicked.connect(self.mw.main_controller.image_actions.add_new_image)
        layout.addWidget(self.btn_add_image_main)

        self.btn_toggle_prop_image = QPushButton(tr("btn_toggle_prop_panel"))
        self.btn_toggle_prop_image.setProperty("class", "toggle")
        self.btn_toggle_prop_image.setCheckable(True)
        self.btn_toggle_prop_image.clicked.connect(self.mw.toggle_property_panel)
        layout.addWidget(self.btn_toggle_prop_image)

        self.img_selected_label = QLabel("")
        self.img_selected_label.setWordWrap(True)
        self.img_selected_label.setProperty("class", "dim small")
        # Note: Qt QSS selector [class~="dim"] support is limited, so we rely on combined class or specific one.
        # For now, let's assume we might update template for "dim small" or just "small".
        # Actually simplest is just "small" and let it rely on default text color or "dim".
        self.img_selected_label.setProperty("class", "dim")  # Use dim for color
        # Manual font size for now if needed, or rely on template.
        # Let's use "dim" and I will ensure "dim" includes small size or create "info".
        self.img_selected_label.setProperty("class", "info-label")
        layout.addWidget(self.img_selected_label)

        # 2) サブタブ
        self.image_subtabs = QTabWidget()
        layout.addWidget(self.image_subtabs)

        # --- Manage ---
        self.image_manage_page = self._build_manage_page()
        self.image_subtabs.addTab(self.image_manage_page, tr("tab_img_manage"))

        # --- Transform ---
        self.transform_page = self._build_transform_page()
        self.image_subtabs.addTab(self.transform_page, tr("tab_img_transform"))

        # --- Playback ---
        self.playback_page = self._build_playback_page()
        self.image_subtabs.addTab(self.playback_page, tr("tab_img_playback"))

        # --- Arrange (Compact) ---
        self.arrange_page = self._build_arrange_page()
        self.image_subtabs.addTab(self.arrange_page, tr("tab_img_arrange"))

        # --- Visibility ---
        self.visibility_page = self._build_visibility_page()
        self.image_subtabs.addTab(self.visibility_page, tr("tab_img_visibility"))

        # --- Danger Area ---
        self.danger_group_img = QGroupBox("")
        danger_layout = QHBoxLayout(self.danger_group_img)
        danger_layout.setContentsMargins(5, 5, 5, 5)

        self.img_btn_sel_close = QPushButton(tr("btn_close_selected_image"))
        self.img_btn_sel_close.setObjectName("ActionBtn")
        self.img_btn_sel_close.clicked.connect(self.mw.main_controller.image_actions.close_selected_image)

        # 初期スタイル適用
        self.update_prop_button_state(self.mw.is_property_panel_active)

        self.btn_close_all_img = QPushButton(tr("btn_close_all_images"))
        self.btn_close_all_img.setObjectName("DangerBtn")
        self.btn_close_all_img.clicked.connect(self.mw.main_controller.bulk_manager.close_all_image_windows)

        danger_layout.addWidget(self.img_btn_sel_close)
        danger_layout.addWidget(self.btn_close_all_img)

        layout.addWidget(self.danger_group_img)
        layout.addStretch()

        # 初期反映
        if hasattr(self.mw, "last_selected_window"):
            self.on_selection_changed(getattr(self.mw, "last_selected_window", None))

    def _build_manage_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        # 作成グループ
        self.img_manage_create_group = QGroupBox(tr("grp_img_manage_create"))
        grid_create = QGridLayout(self.img_manage_create_group)
        grid_create.setContentsMargins(5, 10, 5, 5)

        self.btn_add_image_manage = QPushButton(tr("menu_add_image"))
        self.btn_add_image_manage.setObjectName("ActionBtn")
        self.btn_add_image_manage.clicked.connect(self.mw.main_controller.image_actions.add_new_image)

        grid_create.addWidget(self.btn_add_image_manage, 0, 0, 1, 2)
        layout.addWidget(self.img_manage_create_group)

        # 選択中グループ
        self.img_manage_selected_group = QGroupBox(tr("grp_img_manage_selected"))
        grid_sel = QGridLayout(self.img_manage_selected_group)
        grid_sel.setContentsMargins(5, 10, 5, 5)

        self.img_btn_sel_reselect = QPushButton(tr("menu_reselect_image"))
        self.img_btn_sel_reselect.setObjectName("ActionBtn")
        self.img_btn_sel_reselect.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_manage_action("reselect")
        )

        self.img_btn_sel_clone = QPushButton(tr("menu_clone_image"))
        self.img_btn_sel_clone.setObjectName("ActionBtn")
        self.img_btn_sel_clone.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_manage_action("clone")
        )

        self.img_btn_sel_save_json = QPushButton(tr("menu_save_image_json"))
        self.img_btn_sel_save_json.setObjectName("ActionBtn")
        self.img_btn_sel_save_json.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_manage_action("save_json")
        )

        self.img_btn_sel_load_json = QPushButton(tr("menu_load_json"))
        self.img_btn_sel_load_json.setObjectName("ActionBtn")
        self.img_btn_sel_load_json.clicked.connect(self.mw.file_manager.load_scene_from_json)

        grid_sel.addWidget(self.img_btn_sel_reselect, 0, 0)
        grid_sel.addWidget(self.img_btn_sel_clone, 0, 1)
        grid_sel.addWidget(self.img_btn_sel_save_json, 1, 0)
        grid_sel.addWidget(self.img_btn_sel_load_json, 1, 1)

        layout.addWidget(self.img_manage_selected_group)
        layout.addStretch()
        return page

    def _build_transform_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.transform_selected_group = QGroupBox(tr("anim_target_selected"))
        sel_layout = QVBoxLayout(self.transform_selected_group)
        sel_layout.setContentsMargins(5, 10, 5, 5)

        self.transform_sel_tabs = QTabWidget()
        sel_layout.addWidget(self.transform_sel_tabs)

        # 状態復元
        # 古い mw._img_transform_sel_tab_index があれば優先（移行時のみ）だが、
        # ここでは self._transform_sel_tab_index を使う
        if hasattr(self.mw, "_img_transform_sel_tab_index"):
            self._transform_sel_tab_index = int(self.mw._img_transform_sel_tab_index)
        self.transform_sel_tabs.setCurrentIndex(max(0, self._transform_sel_tab_index))

        self.transform_sel_tabs.currentChanged.connect(self._on_transform_sel_tab_changed)

        # Tab 1: Size / Opacity
        self.size_opacity_page = QWidget()
        so_grid = QGridLayout(self.size_opacity_page)
        self.img_btn_sel_size = QPushButton(tr("btn_img_selected_size_pct"))
        self.img_btn_sel_size.setObjectName("ActionBtn")
        self.img_btn_sel_size.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_transform_action("size")
        )
        self.img_btn_sel_reset_size = QPushButton(tr("btn_img_reset_size"))
        self.img_btn_sel_reset_size.setObjectName("ActionBtn")
        self.img_btn_sel_reset_size.clicked.connect(
            lambda: self.mw.main_controller.image_actions.reset_selected_transform("size")
        )
        self.img_btn_sel_opacity = QPushButton(tr("btn_img_selected_opacity"))
        self.img_btn_sel_opacity.setObjectName("ActionBtn")
        self.img_btn_sel_opacity.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_transform_action("opacity")
        )
        self.img_btn_sel_reset_opacity = QPushButton(tr("btn_img_reset_opacity"))
        self.img_btn_sel_reset_opacity.setObjectName("ActionBtn")
        self.img_btn_sel_reset_opacity.clicked.connect(
            lambda: self.mw.main_controller.image_actions.reset_selected_transform("opacity")
        )
        so_grid.addWidget(self.img_btn_sel_size, 0, 0)
        so_grid.addWidget(self.img_btn_sel_reset_size, 0, 1)
        so_grid.addWidget(self.img_btn_sel_opacity, 1, 0)
        so_grid.addWidget(self.img_btn_sel_reset_opacity, 1, 1)
        self.transform_sel_tabs.addTab(self.size_opacity_page, tr("grp_img_sel_size_opacity"))

        # Tab 2: Rotation
        self.rotation_page = QWidget()
        rot_grid = QGridLayout(self.rotation_page)
        self.img_btn_sel_rotation = QPushButton(tr("btn_img_selected_rotation"))
        self.img_btn_sel_rotation.setObjectName("ActionBtn")
        self.img_btn_sel_rotation.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_transform_action("rotation")
        )
        self.img_btn_sel_reset_rotation = QPushButton(tr("btn_img_reset_rotation"))
        self.img_btn_sel_reset_rotation.setObjectName("ActionBtn")
        self.img_btn_sel_reset_rotation.clicked.connect(
            lambda: self.mw.main_controller.image_actions.reset_selected_transform("rotation")
        )
        self.img_btn_sel_rot_0 = QPushButton("0°")
        self.img_btn_sel_rot_0.setObjectName("ActionBtn")
        self.img_btn_sel_rot_0.clicked.connect(
            lambda: self.mw.main_controller.image_actions.set_selected_rotation_angle(0)
        )
        self.img_btn_sel_rot_90 = QPushButton("90°")
        self.img_btn_sel_rot_90.setObjectName("ActionBtn")
        self.img_btn_sel_rot_90.clicked.connect(
            lambda: self.mw.main_controller.image_actions.set_selected_rotation_angle(90)
        )
        self.img_btn_sel_rot_180 = QPushButton("180°")
        self.img_btn_sel_rot_180.setObjectName("ActionBtn")
        self.img_btn_sel_rot_180.clicked.connect(
            lambda: self.mw.main_controller.image_actions.set_selected_rotation_angle(180)
        )
        self.img_btn_sel_rot_270 = QPushButton("270°")
        self.img_btn_sel_rot_270.setObjectName("ActionBtn")
        self.img_btn_sel_rot_270.clicked.connect(
            lambda: self.mw.main_controller.image_actions.set_selected_rotation_angle(270)
        )
        rot_grid.addWidget(self.img_btn_sel_rotation, 0, 0)
        rot_grid.addWidget(self.img_btn_sel_reset_rotation, 0, 1)
        rot_grid.addWidget(self.img_btn_sel_rot_0, 1, 0)
        rot_grid.addWidget(self.img_btn_sel_rot_90, 1, 1)
        rot_grid.addWidget(self.img_btn_sel_rot_180, 2, 0)
        rot_grid.addWidget(self.img_btn_sel_rot_270, 2, 1)
        self.transform_sel_tabs.addTab(self.rotation_page, tr("grp_img_sel_rotation"))

        # Tab 3: Flip
        self.flip_page = QWidget()
        flip_grid = QGridLayout(self.flip_page)
        self.img_btn_sel_flip_h = QPushButton(tr("btn_img_flip_h"))
        self.img_btn_sel_flip_h.setObjectName("ActionBtn")
        self.img_btn_sel_flip_h.clicked.connect(lambda: self.mw.main_controller.image_actions.flip_selected("h"))
        self.img_btn_sel_flip_v = QPushButton(tr("btn_img_flip_v"))
        self.img_btn_sel_flip_v.setObjectName("ActionBtn")
        self.img_btn_sel_flip_v.clicked.connect(lambda: self.mw.main_controller.image_actions.flip_selected("v"))
        self.img_btn_sel_reset_flips = QPushButton(tr("btn_img_reset_flips"))
        self.img_btn_sel_reset_flips.setObjectName("ActionBtn")
        self.img_btn_sel_reset_flips.clicked.connect(
            lambda: self.mw.main_controller.image_actions.reset_selected_transform("flips")
        )
        flip_grid.addWidget(self.img_btn_sel_flip_h, 0, 0)
        flip_grid.addWidget(self.img_btn_sel_flip_v, 0, 1)
        flip_grid.addWidget(self.img_btn_sel_reset_flips, 1, 0, 1, 2)
        self.transform_sel_tabs.addTab(self.flip_page, tr("grp_img_sel_flip"))

        layout.addWidget(self.transform_selected_group)

        # Bulk (Compact Grid)
        self.adj_group = QGroupBox(tr("grp_bulk_adj"))
        adj_grid = QGridLayout(self.adj_group)
        adj_grid.setContentsMargins(5, 10, 5, 5)

        self.btn_size = QPushButton(tr("btn_set_all_size"))
        self.btn_size.setObjectName("ActionBtn")
        self.btn_size.clicked.connect(self.mw.main_controller.image_actions.set_all_image_size_percentage)

        self.btn_opacity = QPushButton(tr("btn_set_all_opacity"))
        self.btn_opacity.setObjectName("ActionBtn")
        self.btn_opacity.clicked.connect(self.mw.main_controller.image_actions.set_all_image_opacity)

        self.btn_rotate = QPushButton(tr("btn_set_all_rotation"))
        self.btn_rotate.setObjectName("ActionBtn")
        self.btn_rotate.clicked.connect(self.mw.main_controller.image_actions.set_all_image_rotation)

        adj_grid.addWidget(self.btn_size, 0, 0)
        adj_grid.addWidget(self.btn_opacity, 0, 1)
        adj_grid.addWidget(self.btn_rotate, 0, 2)

        layout.addWidget(self.adj_group)
        layout.addStretch()
        return page

    def _on_transform_sel_tab_changed(self, idx: int) -> None:
        self._transform_sel_tab_index = int(idx)
        # 互換性のため mw 側も更新（もし他で参照してれば）
        if hasattr(self.mw, "_img_transform_sel_tab_index"):
            self.mw._img_transform_sel_tab_index = idx

    def _build_playback_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.playback_selected_group = QGroupBox(tr("anim_target_selected"))
        pb_sel_grid = QGridLayout(self.playback_selected_group)
        pb_sel_grid.setContentsMargins(5, 10, 5, 5)

        self.img_btn_sel_anim_toggle = QPushButton(tr("btn_img_selected_gif_toggle"))
        self.img_btn_sel_anim_toggle.setObjectName("ActionBtn")
        self.img_btn_sel_anim_toggle.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_playback_action("toggle")
        )

        self.img_btn_sel_anim_speed = QPushButton(tr("btn_img_selected_gif_speed"))
        self.img_btn_sel_anim_speed.setObjectName("ActionBtn")
        self.img_btn_sel_anim_speed.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_playback_action("speed")
        )

        self.img_btn_sel_anim_reset = QPushButton(tr("btn_img_selected_gif_reset"))
        self.img_btn_sel_anim_reset.setObjectName("ActionBtn")
        self.img_btn_sel_anim_reset.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_playback_action("reset")
        )

        pb_sel_grid.addWidget(self.img_btn_sel_anim_toggle, 0, 0)
        pb_sel_grid.addWidget(self.img_btn_sel_anim_speed, 0, 1)
        pb_sel_grid.addWidget(self.img_btn_sel_anim_reset, 1, 0, 1, 2)
        layout.addWidget(self.playback_selected_group)

        self.playback_group = QGroupBox(tr("grp_img_playback"))
        pb_grid = QGridLayout(self.playback_group)
        pb_grid.setContentsMargins(5, 10, 5, 5)

        self.btn_anim_toggle = QPushButton(tr("btn_img_all_gif_toggle"))
        self.btn_anim_toggle.setObjectName("ActionBtn")
        self.btn_anim_toggle.clicked.connect(self.mw.main_controller.image_actions.toggle_all_image_animation_speed)

        self.btn_set_gif_apng_playback_speed = QPushButton(tr("btn_img_all_gif_speed"))
        self.btn_set_gif_apng_playback_speed.setObjectName("ActionBtn")
        self.btn_set_gif_apng_playback_speed.clicked.connect(
            self.mw.main_controller.image_actions.set_all_gif_apng_playback_speed
        )

        self.btn_reset_gif_apng_playback_speed = QPushButton(tr("btn_img_all_gif_reset"))
        self.btn_reset_gif_apng_playback_speed.setObjectName("ActionBtn")
        self.btn_reset_gif_apng_playback_speed.clicked.connect(
            self.mw.main_controller.image_actions.reset_all_animation_speeds
        )

        pb_grid.addWidget(self.btn_anim_toggle, 0, 0)
        pb_grid.addWidget(self.btn_set_gif_apng_playback_speed, 0, 1)
        pb_grid.addWidget(self.btn_reset_gif_apng_playback_speed, 1, 0, 1, 2)
        layout.addWidget(self.playback_group)
        layout.addStretch()
        return page

    def _build_arrange_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.arrange_subtabs = QTabWidget()
        layout.addWidget(self.arrange_subtabs)

        # --- Arrange > All ---
        self.arrange_all_page = QWidget()
        all_layout = QVBoxLayout(self.arrange_all_page)
        all_layout.setContentsMargins(5, 5, 5, 5)

        self.layout_img_group = QGroupBox(tr("grp_bulk_actions"))
        all_grid = QGridLayout(self.layout_img_group)
        all_grid.setContentsMargins(5, 10, 5, 5)
        all_grid.setSpacing(8)

        self.btn_align = QPushButton(tr("btn_align_images"))
        self.btn_align.clicked.connect(self.mw.open_align_dialog)
        self.btn_reset_flip = QPushButton(tr("btn_reset_flips"))
        self.btn_reset_flip.clicked.connect(self.mw.main_controller.image_actions.reset_all_flips)
        all_grid.addWidget(self.btn_align, 0, 0)
        all_grid.addWidget(self.btn_reset_flip, 0, 1, 1, 2)

        self.btn_img_norm_same_pct = QPushButton(tr("btn_img_norm_same_pct"))
        self.btn_img_norm_same_pct.setObjectName("ActionBtn")
        self.btn_img_norm_same_pct.clicked.connect(
            lambda: self.mw.main_controller.image_actions.normalize_all_images_by_selected("same_pct")
        )

        self.btn_img_norm_same_width = QPushButton(tr("btn_img_norm_same_width"))
        self.btn_img_norm_same_width.setObjectName("ActionBtn")
        self.btn_img_norm_same_width.clicked.connect(
            lambda: self.mw.main_controller.image_actions.normalize_all_images_by_selected("same_width")
        )

        self.btn_img_norm_same_height = QPushButton(tr("btn_img_norm_same_height"))
        self.btn_img_norm_same_height.setObjectName("ActionBtn")
        self.btn_img_norm_same_height.clicked.connect(
            lambda: self.mw.main_controller.image_actions.normalize_all_images_by_selected("same_height")
        )

        all_grid.addWidget(self.btn_img_norm_same_pct, 1, 0)
        all_grid.addWidget(self.btn_img_norm_same_width, 1, 1)
        all_grid.addWidget(self.btn_img_norm_same_height, 1, 2)

        self.btn_img_all_pack_left_top = QPushButton(tr("btn_img_all_pack_left_top"))
        self.btn_img_all_pack_left_top.setObjectName("ActionBtn")
        self.btn_img_all_pack_left_top.clicked.connect(
            lambda: self.mw.img_pack_all_left_top(int(self.img_sel_display_combo.currentData()), space=0)
        )
        self.btn_img_all_pack_center = QPushButton(tr("btn_img_all_pack_center"))
        self.btn_img_all_pack_center.setObjectName("ActionBtn")
        self.btn_img_all_pack_center.clicked.connect(
            lambda: self.mw.img_pack_all_center(int(self.img_sel_display_combo.currentData()), space=0)
        )
        all_grid.addWidget(self.btn_img_all_pack_left_top, 2, 0)
        all_grid.addWidget(self.btn_img_all_pack_center, 2, 1, 1, 2)

        self.img_all_normalize_group = self.layout_img_group
        self.img_all_pack_group = self.layout_img_group

        all_layout.addWidget(self.layout_img_group)
        all_layout.addStretch()
        self.arrange_subtabs.addTab(self.arrange_all_page, tr("tab_img_arrange_all"))

        # --- Arrange > Selected ---
        self.arrange_selected_page = QWidget()
        sel_layout = QVBoxLayout(self.arrange_selected_page)
        sel_layout.setContentsMargins(5, 5, 5, 5)

        self.img_sel_display_group = QGroupBox(tr("grp_img_selected_display_ops"))
        sel_disp_grid = QGridLayout(self.img_sel_display_group)
        sel_disp_grid.setContentsMargins(5, 10, 5, 5)

        self.img_sel_display_label = QLabel(tr("label_select_display"))
        self.img_sel_display_combo = QComboBox()
        try:
            from PySide6.QtGui import QGuiApplication

            screens = QGuiApplication.screens()
            for i, _ in enumerate(screens):
                self.img_sel_display_combo.addItem(f"Screen {i + 1}", i)
        except Exception:
            self.img_sel_display_combo.addItem("Screen 1", 0)

        self.btn_fit_selected_to_display = QPushButton(tr("btn_fit_selected_to_display"))
        self.btn_fit_selected_to_display.setObjectName("ActionBtn")
        self.btn_fit_selected_to_display.clicked.connect(
            lambda: self.mw.main_controller.image_actions.fit_selected_to_display(
                int(self.img_sel_display_combo.currentData())
            )
        )
        self.btn_center_selected_on_display = QPushButton(tr("btn_center_selected_on_display"))
        self.btn_center_selected_on_display.setObjectName("ActionBtn")
        self.btn_center_selected_on_display.clicked.connect(
            lambda: self.mw.main_controller.image_actions.center_selected_on_display(
                int(self.img_sel_display_combo.currentData())
            )
        )

        sel_disp_grid.addWidget(self.img_sel_display_label, 0, 0)
        sel_disp_grid.addWidget(self.img_sel_display_combo, 0, 1)
        sel_disp_grid.addWidget(self.btn_fit_selected_to_display, 1, 0)
        sel_disp_grid.addWidget(self.btn_center_selected_on_display, 1, 1)
        sel_layout.addWidget(self.img_sel_display_group)

        # Snap
        self.img_sel_snap_group = QGroupBox(tr("grp_img_selected_snap_ops"))
        snap_grid = QGridLayout(self.img_sel_snap_group)
        snap_grid.setContentsMargins(5, 10, 5, 5)

        btns = [
            ("btn_snap_left", "left", 0, 0),
            ("btn_snap_top", "top", 0, 1),
            ("btn_snap_bottom", "bottom", 0, 2),
            ("btn_snap_right", "right", 0, 3),
            ("btn_snap_tl", "tl", 1, 0),
            ("btn_snap_tr", "tr", 1, 1),
            ("btn_snap_bl", "bl", 1, 2),
            ("btn_snap_br", "br", 1, 3),
        ]

        for attr, key, r, c in btns:
            btn = QPushButton(tr(attr))
            btn.setObjectName("ActionBtn")

            # 部分適用で関数を生成
            if len(key) > 2:  # corner
                callback = partial(self._snap_wrapper_corner, key)
            else:  # edge
                callback = partial(self._snap_wrapper_edge, key)

            btn.clicked.connect(callback)

            setattr(self, attr, btn)  # 自分の属性として保持
            snap_grid.addWidget(btn, r, c)

        sel_layout.addWidget(self.img_sel_snap_group)
        sel_layout.addStretch()
        self.arrange_subtabs.addTab(self.arrange_selected_page, tr("tab_img_arrange_selected"))

        layout.addWidget(self.arrange_subtabs)
        return page

    def _snap_wrapper_edge(self, key: str) -> None:
        self.mw.main_controller.image_actions.snap_selected_to_display_edge(
            int(self.img_sel_display_combo.currentData()), key
        )

    def _snap_wrapper_corner(self, key: str) -> None:
        self.mw.main_controller.image_actions.snap_selected_to_display_corner(
            int(self.img_sel_display_combo.currentData()), key
        )

    def _build_visibility_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.visibility_selected_group = QGroupBox(tr("anim_target_selected"))
        vis_sel_grid = QGridLayout(self.visibility_selected_group)
        vis_sel_grid.setContentsMargins(5, 10, 5, 5)

        self.img_btn_sel_show = QPushButton(tr("btn_img_selected_show"))
        self.img_btn_sel_show.setObjectName("ActionBtn")
        self.img_btn_sel_show.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_visibility_action("show")
        )

        self.img_btn_sel_hide = QPushButton(tr("btn_img_selected_hide"))
        self.img_btn_sel_hide.setObjectName("ActionBtn")
        self.img_btn_sel_hide.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_visibility_action("hide")
        )

        self.img_btn_sel_frontmost = QPushButton(tr("btn_toggle_front"))
        self.img_btn_sel_frontmost.setProperty("class", "toggle")
        self.img_btn_sel_frontmost.setCheckable(True)
        self.img_btn_sel_frontmost.toggled.connect(
            lambda checked: self.mw.main_controller.image_actions.run_selected_visibility_action("frontmost", checked)
        )

        self.img_btn_sel_click_through = QPushButton(tr("menu_toggle_click_through_image"))
        self.img_btn_sel_click_through.setProperty("class", "toggle")
        self.img_btn_sel_click_through.setCheckable(True)
        self.img_btn_sel_click_through.toggled.connect(
            lambda checked: self.mw.main_controller.image_actions.run_selected_visibility_action(
                "click_through", checked
            )
        )

        vis_sel_grid.addWidget(self.img_btn_sel_show, 0, 0)
        vis_sel_grid.addWidget(self.img_btn_sel_hide, 0, 1)
        vis_sel_grid.addWidget(self.img_btn_sel_frontmost, 1, 0)
        vis_sel_grid.addWidget(self.img_btn_sel_click_through, 1, 1)
        layout.addWidget(self.visibility_selected_group)

        self.visibility_other_images_group = QGroupBox(tr("grp_img_other_images_ops"))
        other_grid = QGridLayout(self.visibility_other_images_group)
        self.img_btn_sel_hide_others = QPushButton(tr("menu_hide_other_images"))
        self.img_btn_sel_hide_others.setObjectName("ActionBtn")
        self.img_btn_sel_hide_others.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_other_images_action("hide_others")
        )

        self.img_btn_sel_show_others = QPushButton(tr("btn_img_show_other_images"))
        self.img_btn_sel_show_others.setObjectName("ActionBtn")
        self.img_btn_sel_show_others.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_other_images_action("show_others")
        )

        self.img_btn_sel_close_others = QPushButton(tr("menu_close_other_images"))
        self.img_btn_sel_close_others.setObjectName("DangerBtn")
        self.img_btn_sel_close_others.clicked.connect(
            lambda: self.mw.main_controller.image_actions.run_selected_other_images_action("close_others")
        )

        other_grid.addWidget(self.img_btn_sel_hide_others, 0, 0, 1, 2)
        other_grid.addWidget(self.img_btn_sel_show_others, 1, 0, 1, 2)
        other_grid.addWidget(self.img_btn_sel_close_others, 2, 0, 1, 2)
        layout.addWidget(self.visibility_other_images_group)

        self.vis_img_group = QGroupBox(tr("grp_visibility_list"))
        vis_img_grid = QGridLayout(self.vis_img_group)
        self.btn_show_all_images = QPushButton(tr("btn_show_all_images"))
        self.btn_show_all_images.clicked.connect(self.mw.main_controller.bulk_manager.show_all_image_windows)
        self.btn_hide_all_images = QPushButton(tr("btn_hide_all_images"))
        self.btn_hide_all_images.clicked.connect(self.mw.main_controller.bulk_manager.hide_all_image_windows)

        vis_img_grid.addWidget(self.btn_show_all_images, 0, 0)
        vis_img_grid.addWidget(self.btn_hide_all_images, 0, 1)
        layout.addWidget(self.vis_img_group)
        layout.addStretch()
        return page

    def update_prop_button_state(self, is_active: bool) -> None:
        """プロパティパネルボタンのトグル状態・スタイル更新。"""
        self.btn_toggle_prop_image.blockSignals(True)
        self.btn_toggle_prop_image.setChecked(is_active)
        self.btn_toggle_prop_image.blockSignals(False)
        # Style is handled by QSS (QPushButton:checked)

    def on_selection_changed(self, window: Optional[Any]) -> None:
        """選択変更時のUI更新"""
        selected_obj = None

        if window is not None:
            # 型チェック
            t_name = type(window).__name__
            if t_name in ("ImageWindow",):
                selected_obj = window

        if selected_obj is None:
            self.img_selected_label.setText(tr("label_anim_selected_none"))

            # 有効無効切り替え
            self._update_enabled_state(None)

            # チェックリセット
            self._reset_toggle_buttons()
            return

        name = type(selected_obj).__name__
        self.img_selected_label.setText(tr("label_anim_selected_fmt").format(name=name))

        # チェック同期
        self._sync_check_states(selected_obj)

        # 有効無効切り替え
        self._update_enabled_state(selected_obj)

    def _reset_toggle_buttons(self) -> None:
        btns = [self.img_btn_sel_frontmost, self.img_btn_sel_click_through]
        for b in btns:
            b.blockSignals(True)
            b.setChecked(False)
            b.blockSignals(False)

    def _sync_check_states(self, obj: Any) -> None:
        from PySide6.QtCore import Qt

        # Frontmost
        is_top = bool(obj.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        self.img_btn_sel_frontmost.blockSignals(True)
        self.img_btn_sel_frontmost.setChecked(is_top)
        self.img_btn_sel_frontmost.blockSignals(False)

        # ClickThrough
        is_ct = bool(obj.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        self.img_btn_sel_click_through.blockSignals(True)
        self.img_btn_sel_click_through.setChecked(is_ct)
        self.img_btn_sel_click_through.blockSignals(False)

    def _update_enabled_state(self, selected_obj: Optional[Any]) -> None:
        enabled = selected_obj is not None

        # Selected系ボタン
        targets = [
            "img_btn_sel_reselect",
            "img_btn_sel_clone",
            "img_btn_sel_save_json",
            "img_btn_sel_load_json",
            "img_btn_sel_size",
            "img_btn_sel_reset_size",
            "img_btn_sel_opacity",
            "img_btn_sel_reset_opacity",
            "img_btn_sel_rotation",
            "img_btn_sel_reset_rotation",
            "img_btn_sel_rot_0",
            "img_btn_sel_rot_90",
            "img_btn_sel_rot_180",
            "img_btn_sel_rot_270",
            "img_btn_sel_flip_h",
            "img_btn_sel_flip_v",
            "img_btn_sel_reset_flips",
            "img_btn_sel_anim_toggle",
            "img_btn_sel_anim_speed",
            "img_btn_sel_anim_reset",
            "btn_fit_selected_to_display",
            "btn_center_selected_on_display",
            "btn_snap_left",
            "btn_snap_top",
            "btn_snap_bottom",
            "btn_snap_right",
            "btn_snap_tl",
            "btn_snap_tr",
            "btn_snap_bl",
            "btn_snap_br",
            "img_btn_sel_show",
            "img_btn_sel_hide",
            "img_btn_sel_frontmost",
            "img_btn_sel_click_through",
            "img_btn_sel_hide_others",
            "img_btn_sel_show_others",
            "img_btn_sel_close_others",
            "img_btn_sel_close",
        ]

        for attr in targets:
            if hasattr(self, attr):
                getattr(self, attr).setEnabled(enabled)

    def refresh_ui(self) -> None:
        """UI文言更新"""
        self.btn_add_image_main.setText("+ " + tr("menu_add_image"))
        self.btn_toggle_prop_image.setText(tr("btn_toggle_prop_panel"))

        self.image_subtabs.setTabText(0, tr("tab_img_manage"))
        self.image_subtabs.setTabText(1, tr("tab_img_transform"))
        self.image_subtabs.setTabText(2, tr("tab_img_playback"))
        self.image_subtabs.setTabText(3, tr("tab_img_arrange"))
        self.image_subtabs.setTabText(4, tr("tab_img_visibility"))

        # Manage
        self.img_manage_create_group.setTitle(tr("grp_img_manage_create"))
        self.btn_add_image_manage.setText(tr("menu_add_image"))

        self.img_manage_selected_group.setTitle(tr("grp_img_manage_selected"))
        self.img_btn_sel_reselect.setText(tr("menu_reselect_image"))
        self.img_btn_sel_clone.setText(tr("menu_clone_image"))
        self.img_btn_sel_save_json.setText(tr("menu_save_image_json"))
        self.img_btn_sel_load_json.setText(tr("menu_load_json"))

        # Transform
        self.transform_selected_group.setTitle(tr("anim_target_selected"))
        self.transform_sel_tabs.setTabText(0, tr("grp_img_sel_size_opacity"))
        self.transform_sel_tabs.setTabText(1, tr("grp_img_sel_rotation"))
        self.transform_sel_tabs.setTabText(2, tr("grp_img_sel_flip"))

        self.img_btn_sel_size.setText(tr("btn_img_selected_size_pct"))
        self.img_btn_sel_reset_size.setText(tr("btn_img_reset_size"))
        self.img_btn_sel_opacity.setText(tr("btn_img_selected_opacity"))
        self.img_btn_sel_reset_opacity.setText(tr("btn_img_reset_opacity"))

        self.img_btn_sel_rotation.setText(tr("btn_img_selected_rotation"))
        self.img_btn_sel_reset_rotation.setText(tr("btn_img_reset_rotation"))

        self.img_btn_sel_flip_h.setText(tr("btn_img_flip_h"))
        self.img_btn_sel_flip_v.setText(tr("btn_img_flip_v"))
        self.img_btn_sel_reset_flips.setText(tr("btn_img_reset_flips"))

        self.adj_group.setTitle(tr("grp_bulk_adj"))
        self.btn_size.setText(tr("btn_set_all_size"))
        self.btn_opacity.setText(tr("btn_set_all_opacity"))
        self.btn_rotate.setText(tr("btn_set_all_rotation"))

        # Playback
        self.playback_selected_group.setTitle(tr("anim_target_selected"))
        self.img_btn_sel_anim_toggle.setText(tr("btn_img_selected_gif_toggle"))
        self.img_btn_sel_anim_speed.setText(tr("btn_img_selected_gif_speed"))
        self.img_btn_sel_anim_reset.setText(tr("btn_img_selected_gif_reset"))

        self.playback_group.setTitle(tr("grp_img_playback"))
        self.btn_anim_toggle.setText(tr("btn_img_all_gif_toggle"))
        self.btn_set_gif_apng_playback_speed.setText(tr("btn_img_all_gif_speed"))
        self.btn_reset_gif_apng_playback_speed.setText(tr("btn_img_all_gif_reset"))

        # Arrange
        self.arrange_subtabs.setTabText(0, tr("tab_img_arrange_all"))
        self.arrange_subtabs.setTabText(1, tr("tab_img_arrange_selected"))

        self.layout_img_group.setTitle(tr("grp_bulk_actions"))
        self.btn_align.setText(tr("btn_align_images"))
        self.btn_reset_flip.setText(tr("btn_reset_flips"))

        self.btn_img_norm_same_pct.setText(tr("btn_img_norm_same_pct"))
        self.btn_img_norm_same_width.setText(tr("btn_img_norm_same_width"))
        self.btn_img_norm_same_height.setText(tr("btn_img_norm_same_height"))

        self.btn_img_all_pack_left_top.setText(tr("btn_img_all_pack_left_top"))
        self.btn_img_all_pack_center.setText(tr("btn_img_all_pack_center"))

        self.img_sel_display_group.setTitle(tr("grp_img_selected_display_ops"))
        self.img_sel_display_label.setText(tr("label_select_display"))
        self.btn_fit_selected_to_display.setText(tr("btn_fit_selected_to_display"))
        self.btn_center_selected_on_display.setText(tr("btn_center_selected_on_display"))

        self.img_sel_snap_group.setTitle(tr("grp_img_selected_snap_ops"))
        self.btn_snap_left.setText(tr("btn_snap_left"))
        self.btn_snap_top.setText(tr("btn_snap_top"))
        self.btn_snap_bottom.setText(tr("btn_snap_bottom"))
        self.btn_snap_right.setText(tr("btn_snap_right"))
        self.btn_snap_tl.setText(tr("btn_snap_tl"))
        self.btn_snap_tr.setText(tr("btn_snap_tr"))
        self.btn_snap_bl.setText(tr("btn_snap_bl"))
        self.btn_snap_br.setText(tr("btn_snap_br"))

        # Visibility
        self.visibility_selected_group.setTitle(tr("anim_target_selected"))
        self.img_btn_sel_show.setText(tr("btn_img_selected_show"))
        self.img_btn_sel_hide.setText(tr("btn_img_selected_hide"))
        self.img_btn_sel_frontmost.setText(tr("btn_toggle_front"))
        self.img_btn_sel_click_through.setText(tr("menu_toggle_click_through_image"))

        self.visibility_other_images_group.setTitle(tr("grp_img_other_images_ops"))
        self.img_btn_sel_hide_others.setText(tr("menu_hide_other_images"))
        self.img_btn_sel_show_others.setText(tr("btn_img_show_other_images"))
        self.img_btn_sel_close_others.setText(tr("menu_close_other_images"))

        self.vis_img_group.setTitle(tr("grp_visibility_list"))
        self.btn_show_all_images.setText(tr("btn_show_all_images"))
        self.btn_hide_all_images.setText(tr("btn_hide_all_images"))

        # Danger
        self.img_btn_sel_close.setText(tr("btn_close_selected_image"))
        self.btn_close_all_img.setText(tr("btn_close_all_images"))
