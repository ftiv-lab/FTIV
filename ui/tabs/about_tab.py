from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from utils.translator import tr


class AboutTab(QWidget):
    """情報（About）タブ。

    エディション情報、ライセンス、ログ、バージョン情報などを集約する。
    """

    def __init__(self, main_window: Any):
        super().__init__()
        self.mw = main_window
        self._setup_ui()
        self._inject_compatibility_attributes()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # ------------------------------------------------
        # 1. エディション・ライセンス
        # ------------------------------------------------
        self.edition_group = QGroupBox(tr("grp_edition"))
        edition_layout = QGridLayout(self.edition_group)

        # 現在のエディション表示
        from utils.edition import get_edition

        current_ed = get_edition(self.mw, getattr(self.mw, "base_directory", None))
        self.label_current_edition = QLabel(tr("label_current_edition").format(edition=current_ed.value.upper()))
        self.label_current_edition.setStyleSheet("font-weight: bold; color: #aaa; font-size: 14px;")

        # ショップボタン
        self.btn_open_shop = QPushButton(tr("btn_open_shop"))
        self.btn_open_shop.setObjectName("ActionBtn")
        self.btn_open_shop.clicked.connect(self.mw.open_shop_page)

        self.btn_copy_shop_url = QPushButton(tr("btn_copy_url"))
        self.btn_copy_shop_url.setObjectName("ActionBtn")
        self.btn_copy_shop_url.clicked.connect(self.mw.copy_shop_url)

        edition_layout.addWidget(self.label_current_edition, 0, 0, 1, 2)
        edition_layout.addWidget(self.btn_open_shop, 1, 0)
        edition_layout.addWidget(self.btn_copy_shop_url, 1, 1)

        layout.addWidget(self.edition_group)

        # ------------------------------------------------
        # 2. システム・情報 (ログ、バージョンなど)
        # ------------------------------------------------
        self.system_group = QGroupBox(tr("grp_system_info"))
        system_layout = QGridLayout(self.system_group)
        system_layout.setSpacing(10)

        # ログフォルダを開く
        self.btn_open_log = QPushButton(tr("btn_open_log_folder"))
        self.btn_open_log.setObjectName("ActionBtn")
        self.btn_open_log.clicked.connect(self.mw.open_log_folder)

        # バージョン情報
        self.btn_show_about = QPushButton(tr("btn_show_about_dialog"))
        self.btn_show_about.setObjectName("ActionBtn")
        self.btn_show_about.clicked.connect(self.mw.show_about_dialog)

        # 説明書ボタン
        self.btn_manual = QPushButton(tr("btn_manual"))
        self.btn_manual.clicked.connect(self.mw.show_manual_dialog)

        # ライセンスボタン
        self.btn_license = QPushButton(tr("btn_license"))
        self.btn_license.clicked.connect(self.mw.show_license_dialog)

        # 配置 (2列 x 2行)
        system_layout.addWidget(self.btn_manual, 0, 0)
        system_layout.addWidget(self.btn_license, 0, 1)
        system_layout.addWidget(self.btn_open_log, 1, 0)
        system_layout.addWidget(self.btn_show_about, 1, 1)

        layout.addWidget(self.system_group)

        # ------------------------------------------------
        # 3. 緊急ショートカット
        # ------------------------------------------------
        self.shortcuts_group = QGroupBox(tr("grp_shortcuts"))
        shortcuts_layout = QVBoxLayout(self.shortcuts_group)

        self.label_shortcuts = QLabel(tr("label_rescue_shortcuts"))
        self.label_shortcuts.setStyleSheet("color: #ccc; font-family: Consolas, Monospace; line-height: 1.4;")
        self.label_shortcuts.setTextInteractionFlags(Qt.TextSelectableByMouse)  # コピーできるようにする

        shortcuts_layout.addWidget(self.label_shortcuts)
        layout.addWidget(self.shortcuts_group)

        # ------------------------------------------------
        # 4. パフォーマンスチューニング
        # ------------------------------------------------
        self.perf_group = QGroupBox(tr("grp_performance"))
        perf_layout = QGridLayout(self.perf_group)

        # 現在値の取得
        cur_debounce = getattr(self.mw.app_settings, "render_debounce_ms", 50)
        cur_wheel = getattr(self.mw.app_settings, "wheel_debounce_ms", 80)
        cur_cache = getattr(self.mw.app_settings, "glyph_cache_size", 512)

        # --- Debounce ---
        self.label_debounce = QLabel(tr("label_debounce"))
        self.spin_debounce = QSpinBox()
        self.spin_debounce.setRange(0, 500)
        self.spin_debounce.setSingleStep(10)
        self.spin_debounce.setValue(int(cur_debounce))

        self.hint_debounce = QLabel(tr("hint_debounce"))
        self.hint_debounce.setStyleSheet("color: #888; font-size: 11px;")
        self.hint_debounce.setWordWrap(True)

        # --- Debounce (Wheel) ---
        self.label_wheel = QLabel(tr("label_wheel_debounce"))
        self.spin_wheel = QSpinBox()
        self.spin_wheel.setRange(0, 500)
        self.spin_wheel.setSingleStep(10)
        self.spin_wheel.setValue(int(cur_wheel))

        self.hint_wheel = QLabel(tr("hint_wheel_debounce"))
        self.hint_wheel.setStyleSheet("color: #888; font-size: 11px;")
        self.hint_wheel.setWordWrap(True)

        # --- Cache ---
        self.label_cache = QLabel(tr("label_cache"))
        self.spin_cache = QSpinBox()
        self.spin_cache.setRange(0, 4096)
        self.spin_cache.setSingleStep(128)
        self.spin_cache.setValue(int(cur_cache))

        self.hint_cache = QLabel(tr("hint_cache"))
        self.hint_cache.setStyleSheet("color: #888; font-size: 11px;")
        self.hint_cache.setWordWrap(True)

        # Apply Button
        self.btn_apply_perf = QPushButton(tr("btn_apply_perf"))
        self.btn_apply_perf.setObjectName("ActionBtn")
        self.btn_apply_perf.clicked.connect(self._apply_perf)

        # 配置 (行番号をずらす)
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

        layout.addWidget(self.perf_group)
        layout.addStretch()

    def _inject_compatibility_attributes(self) -> None:
        """mw に属性を注入して互換性を維持"""
        attrs = [
            "edition_group",
            "label_current_edition",
            "btn_open_shop",
            "btn_copy_shop_url",
            "system_group",
            "btn_open_log",
            "btn_show_about",
            "btn_manual",
            "btn_license",
            "shortcuts_group",
            "label_shortcuts",
            "perf_group",
            "label_debounce",
            "spin_debounce",
            "hint_debounce",
            "label_wheel",
            "spin_wheel",
            "hint_wheel",
            "label_cache",
            "spin_cache",
            "hint_cache",
            "btn_apply_perf",
        ]
        for attr in attrs:
            if hasattr(self, attr):
                setattr(self.mw, attr, getattr(self, attr))

    def _apply_perf(self) -> None:
        """パフォーマンス設定を適用"""
        d = self.spin_debounce.value()
        w = self.spin_wheel.value()
        c = self.spin_cache.value()
        if hasattr(self.mw, "apply_performance_settings"):
            self.mw.apply_performance_settings(d, w, c)

    def refresh_ui(self) -> None:
        """多言語対応のためのテキスト更新"""
        # エディション・ライセンス
        self.edition_group.setTitle(tr("grp_edition"))

        from utils.edition import get_edition

        ed = get_edition(self.mw, getattr(self.mw, "base_directory", None))
        self.label_current_edition.setText(tr("label_current_edition").format(edition=ed.value.upper()))

        self.btn_open_shop.setText(tr("btn_open_shop"))
        self.btn_copy_shop_url.setText(tr("btn_copy_url"))

        # システム・情報
        self.system_group.setTitle(tr("grp_system_info"))
        self.btn_open_log.setText(tr("btn_open_log_folder"))
        self.btn_show_about.setText(tr("btn_show_about_dialog"))
        self.btn_manual.setText(tr("btn_manual"))
        self.btn_license.setText(tr("btn_license"))

        # ショートカット
        self.shortcuts_group.setTitle(tr("grp_shortcuts"))
        self.label_shortcuts.setText(tr("label_rescue_shortcuts"))

        # パフォーマンスチューニング
        self.perf_group.setTitle(tr("grp_performance"))
        self.label_debounce.setText(tr("label_debounce"))
        self.hint_debounce.setText(tr("hint_debounce"))
        self.label_wheel.setText(tr("label_wheel_debounce"))
        self.hint_wheel.setText(tr("hint_wheel_debounce"))
        self.label_cache.setText(tr("label_cache"))
        self.hint_cache.setText(tr("hint_cache"))
        self.btn_apply_perf.setText(tr("btn_apply_perf"))
