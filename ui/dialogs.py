# ui/dialogs.py

import json
import os
import traceback
from typing import Any, Callable, Dict, Optional, Tuple

from PySide6.QtCore import QEvent, QPoint, QSignalBlocker, QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QGuiApplication, QIcon, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.translator import tr

from .widgets import Gradient


class BaseTranslatableDialog(QDialog):
    """languageChanged の接続/切断を共通化したダイアログ基底。

    ルール:
        - refresh_ui_text() をサブクラスで実装する（翻訳更新）
        - close/accept/reject のどの経路でも必ず切断する
        - connect は重複しない

    Notes:
        これにより「ダイアログ破棄後に languageChanged が残ってクラッシュ/二重更新」
        を防げる。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """BaseTranslatableDialog を初期化する。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        self._lang_conn: bool = False

    def refresh_ui_text(self) -> None:
        """言語切替時にUI文言を更新する（サブクラスで実装）。"""
        return

    def _connect_language_changed(self) -> None:
        """翻訳シグナルへ接続する（重複接続防止つき）。"""
        if self._lang_conn:
            return

        try:
            from utils.translator import _translator

            _translator.languageChanged.connect(self.refresh_ui_text)
            self._lang_conn = True
        except Exception:
            self._lang_conn = False

    def _disconnect_language_changed(self) -> None:
        """翻訳シグナルから切断する（安全に）。"""
        if not self._lang_conn:
            return

        try:
            from utils.translator import _translator

            _translator.languageChanged.disconnect(self.refresh_ui_text)
        except Exception:
            pass
        finally:
            self._lang_conn = False

    def closeEvent(self, event: QEvent) -> None:
        """ダイアログ破棄時に languageChanged を確実に切断する。

        Args:
            event (QEvent): close event
        """
        self._disconnect_language_changed()
        super().closeEvent(event)

    def accept(self) -> None:
        """確定時に languageChanged を切断して閉じる。"""
        self._disconnect_language_changed()
        super().accept()

    def reject(self) -> None:
        """キャンセル時に languageChanged を切断して閉じる。"""
        self._disconnect_language_changed()
        super().reject()


class SliderSpinDialog(QDialog):
    """スライダーとスピンボックスを同期させて値を変更する汎用ダイアログ。

    Attributes:
        callback (Callable): 値が変更された際に実行される関数。
        initial_val (float): ダイアログを開いた時の初期値。
        multiplier (int): 小数をスライダー(int)で扱うための倍率。
    """

    def __init__(
        self,
        title: str,
        label: str,
        min_val: float,
        max_val: float,
        initial_val: float,
        callback: Callable[[float], None],
        parent: Optional[QWidget] = None,
        suffix: str = "",
        decimals: int = 0,
    ) -> None:
        """SliderSpinDialogを初期化する。"""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.callback = callback
        self.initial_val = initial_val
        self.multiplier = 10**decimals

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label))

        container = QHBoxLayout()

        # スライダー設定
        self.slider = QSlider(Qt.Horizontal)
        slider_min = int(min_val * self.multiplier)
        slider_max = int(max_val * self.multiplier)
        slider_val = int(initial_val * self.multiplier)
        self.slider.setRange(slider_min, slider_max)
        self.slider.setValue(slider_val)
        # 追加：スライダーの1ステップ/ページステップを明示（大きく動きすぎるのを防ぐ）
        try:
            step: int = max(1, int(1 * self.multiplier))
            self.slider.setSingleStep(step)
            self.slider.setPageStep(step)
        except Exception:
            pass

        # スピンボックス設定
        if decimals > 0:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setDecimals(decimals)
            self.spinbox.setRange(min_val, max_val)
        else:
            self.spinbox = QSpinBox()
            self.spinbox.setRange(int(min_val), int(max_val))

        self.spinbox.setValue(initial_val)
        self.spinbox.setSuffix(suffix)

        container.addWidget(self.slider)
        container.addWidget(self.spinbox)
        layout.addLayout(container)

        # 信号の接続
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setMinimumWidth(300)

    def on_slider_changed(self, val: int) -> None:
        """スライダーの値が変更された際にスピンボックスを更新する。"""
        real_val = val / self.multiplier
        with QSignalBlocker(self.spinbox):
            self.spinbox.setValue(real_val)
        if self.callback is not None:
            self.callback(real_val)

    def on_spinbox_changed(self, val: float) -> None:
        """スピンボックスの値が変更された際にスライダーを更新する。"""
        slider_val = int(val * self.multiplier)
        with QSignalBlocker(self.slider):
            self.slider.setValue(slider_val)
        if self.callback is not None:
            self.callback(val)

    def reject(self) -> None:
        """キャンセル時は値を初期値に戻して終了する。"""
        if self.callback is not None:
            self.callback(self.initial_val)
        super().reject()


class PreviewCommitDialog(QDialog):
    """プレビュー中は反映するが Undo を積まない、OK確定で1回だけコミットするダイアログ。

    - on_preview: 値変更中のプレビュー反映（Undoなし）
    - on_commit: OK確定時の反映（Undoを積む側で実装する）
    - on_cancel: Cancel時に元の値へ戻す（Undoなし）

    Attributes:
        _initial (float): 初期値（Cancel復帰用）
    """

    def __init__(
        self,
        title: str,
        label: str,
        min_val: float,
        max_val: float,
        initial_val: float,
        on_preview: Callable[[float], None],
        on_commit: Callable[[float], None],
        parent: Optional[QWidget] = None,
        suffix: str = "",
        decimals: int = 0,
    ) -> None:
        """PreviewCommitDialog を初期化する。

        Args:
            title (str): タイトル
            label (str): ラベル
            min_val (float): 最小
            max_val (float): 最大
            initial_val (float): 初期値
            on_preview (Callable[[float], None]): プレビュー反映（Undoなし）
            on_commit (Callable[[float], None]): 確定反映（Undoあり想定）
            parent (Optional[QWidget]): 親
            suffix (str): サフィックス
            decimals (int): 小数桁
        """
        super().__init__(parent)
        self.setWindowTitle(title)

        self._initial: float = float(initial_val)
        self._on_preview: Callable[[float], None] = on_preview
        self._on_commit: Callable[[float], None] = on_commit

        self._multiplier: int = 10 ** int(decimals)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label))

        row = QHBoxLayout()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(min_val * self._multiplier), int(max_val * self._multiplier))
        self.slider.setValue(int(initial_val * self._multiplier))
        try:
            step: int = max(1, int(1 * self._multiplier))
            self.slider.setSingleStep(step)
            self.slider.setPageStep(step)
        except Exception:
            pass

        if decimals > 0:
            self.spin = QDoubleSpinBox()
            self.spin.setDecimals(int(decimals))
            self.spin.setRange(float(min_val), float(max_val))
            self.spin.setValue(float(initial_val))
        else:
            self.spin = QSpinBox()
            self.spin.setRange(int(min_val), int(max_val))
            self.spin.setValue(int(initial_val))

        self.spin.setSuffix(suffix)

        row.addWidget(self.slider)
        row.addWidget(self.spin)
        layout.addLayout(row)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spin.valueChanged.connect(self._on_spin_changed)

        self.setMinimumWidth(320)

        # 初回プレビューをかけたい場合は呼ぶ（欲しければ）
        try:
            self._on_preview(float(initial_val))
        except Exception:
            pass

    def _current_value(self) -> float:
        """現在値を float で返す。"""
        try:
            return float(self.slider.value()) / float(self._multiplier)
        except Exception:
            return self._initial

    def _on_slider_changed(self, v: int) -> None:
        """スライダー変更 → スピン同期 → プレビュー反映。"""
        val: float = float(v) / float(self._multiplier)
        with QSignalBlocker(self.spin):
            self.spin.setValue(val)
        try:
            self._on_preview(val)
        except Exception:
            pass

    def _on_spin_changed(self, v: float) -> None:
        """スピン変更 → スライダー同期 → プレビュー反映。"""
        val: float = float(v)
        with QSignalBlocker(self.slider):
            self.slider.setValue(int(val * self._multiplier))
        try:
            self._on_preview(val)
        except Exception:
            pass

    def accept(self) -> None:
        """OK確定：コミット反映を1回だけ呼ぶ。"""
        val: float = self._current_value()
        try:
            self._on_commit(val)
        except Exception:
            pass
        super().accept()

    def reject(self) -> None:
        """Cancel：初期値へ戻す（Undoなし）。"""
        try:
            self._on_preview(self._initial)
        except Exception:
            pass
        super().reject()


class TextInputDialog(BaseTranslatableDialog):
    """テキスト入力用ダイアログ。フォント設定や設定の保存機能を備える。

    Attributes:
        callback (Optional[Callable[[str], None]]): テキスト変更時にリアルタイムで呼ばれる関数。
        current_font (QFont): 現在適用されているフォント。
    """

    def __init__(
        self,
        initial_text: str,
        parent: Optional[QWidget] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """TextInputDialogを初期化する。

        Args:
            initial_text (str): 初期表示テキスト。
            parent (Optional[QWidget]): 親。
            callback (Optional[Callable[[str], None]]): リアルタイム更新コールバック。
        """
        super().__init__(parent)
        self.setWindowTitle(tr("title_input_text"))
        self.callback: Optional[Callable[[str], None]] = callback

        layout: QVBoxLayout = QVBoxLayout(self)

        self.hint_label: QLabel = QLabel(tr("label_text_edit_hint"))
        self.hint_label.setProperty("class", "hint-text")
        layout.addWidget(self.hint_label)

        self.text_edit: QTextEdit = QTextEdit(self)
        self.text_edit.setText(initial_text)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.selectAll()
        layout.addWidget(self.text_edit)

        settings: Dict[str, Any] = self.load_settings()
        self.current_font: QFont = QFont(
            str(settings.get("family", "Arial")),
            int(settings.get("point_size", 20)),
        )
        self.dialog_size: QSize = QSize(
            int(settings.get("width", 500)),
            int(settings.get("height", 500)),
        )

        try:
            self.resize(self.dialog_size)
        except Exception:
            pass

        self.apply_font_to_text(self.current_font)

        self.font_button: QPushButton = QPushButton(tr("btn_change_font_input"), self)
        self.font_button.clicked.connect(self.change_font)
        layout.addWidget(self.font_button)

        button_layout: QVBoxLayout = QVBoxLayout()
        ok_button: QPushButton = QPushButton(tr("btn_ok"), self)
        cancel_button: QPushButton = QPushButton(tr("btn_cancel"), self)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.text_edit.installEventFilter(self)

        # 言語切替追従
        self._connect_language_changed()

    def refresh_ui_text(self) -> None:
        """言語切替時に、ダイアログ内テキストを更新します。"""
        self.setWindowTitle(tr("title_input_text"))
        if hasattr(self, "hint_label"):
            self.hint_label.setText(tr("label_text_edit_hint"))
        if hasattr(self, "font_button"):
            self.font_button.setText(tr("btn_change_font_input"))

    def eventFilter(self, obj: Any, event: QEvent) -> bool:
        """Ctrl+Enterでの確定を検知するイベントフィルタ。

        Args:
            obj (Any): イベント対象。
            event (QEvent): イベント。

        Returns:
            bool: ハンドルしたなら True。
        """
        if obj == self.text_edit and event.type() == QEvent.KeyPress:
            try:
                if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                    self.accept()
                    return True
            except Exception:
                pass
        return super().eventFilter(obj, event)

    def on_text_changed(self) -> None:
        """テキストが変更された際のコールバック通知。"""
        if self.callback:
            try:
                self.callback(self.text_edit.toPlainText())
            except Exception:
                # リアルタイムプレビューで落ちない
                pass

    def change_font(self) -> None:
        """フォント選択ダイアログを表示してフォントを更新する。"""
        font_dialog: QFontDialog = QFontDialog(self)
        font_dialog.setCurrentFont(self.current_font)
        if font_dialog.exec() == QFontDialog.Accepted:
            font = font_dialog.selectedFont()
            if isinstance(font, QFont):
                self.current_font = font
                self.apply_font_to_text(self.current_font)
                try:
                    self.save_settings()
                except Exception:
                    pass

    def apply_font_to_text(self, font: QFont) -> None:
        """QTextEditのフォントを更新する（Windows向け：絵文字/記号が化けない表示を優先）。

        Args:
            font (QFont): 希望フォント（設定保存用）。表示用にはフォールバックを優先する。
        """
        try:
            effective: QFont = QFont("Segoe UI", font.pointSize())
            effective_emoji: QFont = QFont("Segoe UI Emoji", font.pointSize())

            try:
                self.text_edit.setFont(effective_emoji)
            except Exception:
                self.text_edit.setFont(effective)

            cursor: QTextCursor = self.text_edit.textCursor()
            cursor.select(QTextCursor.Document)
            fmt = cursor.charFormat()
            fmt.setFont(self.text_edit.font())
            cursor.setCharFormat(fmt)

        except Exception:
            try:
                self.text_edit.setFont(font)
            except Exception:
                pass

    def get_text(self) -> str:
        """編集中のテキストを取得する。

        Returns:
            str: 現在の入力内容。
        """
        return self.text_edit.toPlainText()

    def get_settings_path(self) -> str:
        """設定保存用のJSONファイルパスを取得する。

        Returns:
            str: 設定ファイルパス。
        """
        from utils.paths import get_base_dir

        base_dir = get_base_dir()
        json_dir: str = os.path.join(base_dir, "json")
        os.makedirs(json_dir, exist_ok=True)
        return os.path.join(json_dir, "dialog_settings.json")

    def save_settings(self) -> None:
        """現在のフォントとウィンドウサイズを保存する。

        Notes:
            ここは高頻度で呼ばれる可能性があるため、保存失敗でもアプリを落とさない。
            （販売版で通知方針を決めるなら、ここを QMessageBox.warning にする）
        """
        settings_data: Dict[str, Any] = {
            "family": self.current_font.family(),
            "point_size": int(self.current_font.pointSize()),
            "width": int(self.size().width()),
            "height": int(self.size().height()),
        }
        try:
            with open(self.get_settings_path(), "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
        except Exception:
            # 保存失敗は致命ではないので握る
            pass

    def load_settings(self) -> Dict[str, Any]:
        """保存された設定を読み込む。失敗した場合はデフォルトを返す。

        Returns:
            Dict[str, Any]: 設定dict。
        """
        path: str = self.get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data: Any = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {"family": "Arial", "point_size": 20, "width": 500, "height": 500}

    def accept(self) -> None:
        """確定時に設定保存して閉じる（languageChanged切断は基底が行う）。"""
        try:
            self.save_settings()
        except Exception:
            pass
        super().accept()


class MarginRatioDialog(QDialog):
    """余白比率を数値入力で設定するダイアログ。"""

    def __init__(self, title: str, label: str, initial_value: float, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel(label))

        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setRange(0.0, 1.0)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.setValue(initial_value)

        hlayout.addWidget(self.spin_box)
        layout.addLayout(hlayout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_value(self) -> float:
        """入力された値を取得する。"""
        return self.spin_box.value()


class ShadowOffsetDialog(QDialog):
    """シャドウのオフセット（X, Y）をスライダーとスピンボックスで調整する。"""

    def __init__(
        self,
        title: str,
        initial_x: float,
        initial_y: float,
        callback: Optional[Callable[[float, float], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.callback = callback
        self.initial_x = initial_x
        self.initial_y = initial_y

        layout = QVBoxLayout(self)

        # X方向の設定
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel(tr("label_shadow_offset_x"), self))
        self.x_slider = QSlider(Qt.Horizontal, self)
        self.x_slider.setRange(-100, 100)
        self.x_slider.setValue(int(initial_x * 100))
        x_layout.addWidget(self.x_slider)

        self.x_spin_box = QDoubleSpinBox(self)
        self.x_spin_box.setRange(-10.0, 10.0)
        self.x_spin_box.setSingleStep(0.01)
        self.x_spin_box.setDecimals(2)
        self.x_spin_box.setValue(initial_x)
        x_layout.addWidget(self.x_spin_box)
        layout.addLayout(x_layout)

        # Y方向の設定
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel(tr("label_shadow_offset_y"), self))
        self.y_slider = QSlider(Qt.Horizontal, self)
        self.y_slider.setRange(-100, 100)
        self.y_slider.setValue(int(initial_y * 100))
        y_layout.addWidget(self.y_slider)

        self.y_spin_box = QDoubleSpinBox(self)
        self.y_spin_box.setRange(-10.0, 10.0)
        self.y_spin_box.setSingleStep(0.01)
        self.y_spin_box.setDecimals(2)
        self.y_spin_box.setValue(initial_y)
        y_layout.addWidget(self.y_spin_box)
        layout.addLayout(y_layout)

        self.x_slider.valueChanged.connect(self.sync_x_spin_box)
        self.x_spin_box.valueChanged.connect(self.sync_x_slider)
        self.y_slider.valueChanged.connect(self.sync_y_spin_box)
        self.y_spin_box.valueChanged.connect(self.sync_y_slider)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def trigger_callback(self) -> None:
        if self.callback:
            self.callback(self.x_spin_box.value(), self.y_spin_box.value())

    def sync_x_spin_box(self, value: int) -> None:
        with QSignalBlocker(self.x_spin_box):
            self.x_spin_box.setValue(value / 100.0)
        self.trigger_callback()

    def sync_x_slider(self, value: float) -> None:
        with QSignalBlocker(self.x_slider):
            self.x_slider.setValue(int(value * 100))
        self.trigger_callback()

    def sync_y_spin_box(self, value: int) -> None:
        with QSignalBlocker(self.y_spin_box):
            self.y_spin_box.setValue(value / 100.0)
        self.trigger_callback()

    def sync_y_slider(self, value: float) -> None:
        with QSignalBlocker(self.y_slider):
            self.y_slider.setValue(int(value * 100))
        self.trigger_callback()

    def get_offsets(self) -> Tuple[float, float]:
        """設定されたX, Yオフセットを返す。"""
        return self.x_spin_box.value(), self.y_spin_box.value()

    def reject(self) -> None:
        if self.callback:
            self.callback(self.initial_x, self.initial_y)
        super().reject()


class ShadowScaleDialog(QDialog):
    """シャドウのスケール比率を調整するダイアログ。"""

    def __init__(self, initial_value: float, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("title_change_shadow_scale"))
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setRange(0.01, 10.0)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.setValue(initial_value)
        form_layout.addRow(tr("label_shadow_scale"), self.spin_box)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_value(self) -> float:
        return self.spin_box.value()


class GradientEditorDialog(BaseTranslatableDialog):
    """グラデーションの色と角度を編集するダイアログ。"""

    def __init__(
        self,
        initial_gradient: Optional[Any] = None,
        initial_angle: int = 0,
        parent: Optional[QWidget] = None,
    ) -> None:
        """グラデーションの色と角度を編集するダイアログ（v1.1）。

        改善点:
            - Stopは色付きで表示（Gradient側）
            - 右パネルに Stop番号/位置%/HEX を表示
            - 操作ヒントを表示
            - 言語切替を即時反映

        Args:
            initial_gradient (Optional[Any]): 初期グラデーション（[(pos, "#RRGGBB"), ...]）。
            initial_angle (int): 初期角度（0-360）。
            parent (Optional[QWidget]): 親ウィジェット。
        """
        super().__init__(parent)
        self.setWindowTitle(tr("title_gradient_editor"))
        self.setModal(True)

        try:
            self.resize(720, 540)
        except Exception:
            pass

        layout: QVBoxLayout = QVBoxLayout(self)

        # =========================
        # Main row: Left (editor) / Right (selected stop)
        # =========================
        main_row: QHBoxLayout = QHBoxLayout()
        layout.addLayout(main_row)

        left_col: QVBoxLayout = QVBoxLayout()
        right_col: QVBoxLayout = QVBoxLayout()

        main_row.addLayout(left_col, 3)
        main_row.addLayout(right_col, 2)

        # --- Gradient widget (left) ---
        self.gradient_widget: Gradient = Gradient(angle=int(initial_angle))
        self.gradient_widget.setFocusPolicy(Qt.StrongFocus)

        if initial_gradient:
            try:
                self.gradient_widget.setGradient(initial_gradient)
            except Exception:
                pass

        left_col.addWidget(self.gradient_widget, stretch=1)

        # --- Angle controls (left) ---
        angle_layout: QHBoxLayout = QHBoxLayout()
        angle_layout.addWidget(QLabel(tr("label_gradient_angle")))

        self.angle_slider: QSlider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(0, 360)
        self.angle_slider.setValue(int(initial_angle))
        angle_layout.addWidget(self.angle_slider)

        self.angle_spin_box: QSpinBox = QSpinBox()
        self.angle_spin_box.setRange(0, 360)
        self.angle_spin_box.setValue(int(initial_angle))
        angle_layout.addWidget(self.angle_spin_box)

        self.angle_slider.valueChanged.connect(self.angle_spin_box.setValue)
        self.angle_spin_box.valueChanged.connect(self.angle_slider.setValue)
        self.angle_slider.valueChanged.connect(self.update_gradient_angle)

        left_col.addLayout(angle_layout)

        # --- Hint (v1.1) ---
        self.lbl_hint: QLabel = QLabel(tr("hint_gradient_editor_ops"))
        self.lbl_hint.setProperty("class", "hint-text")
        self.lbl_hint.setWordWrap(True)
        left_col.addWidget(self.lbl_hint)

        # =========================
        # Right panel: Selected Stop
        # =========================
        self.grp_selected_stop: QGroupBox = QGroupBox(tr("grp_gradient_selected_stop"))
        self.grp_selected_stop.setEnabled(False)
        right_col.addWidget(self.grp_selected_stop)

        sel_layout: QFormLayout = QFormLayout(self.grp_selected_stop)

        # Position row: [spin] [value label]
        pos_row: QWidget = QWidget()
        pos_row_layout: QHBoxLayout = QHBoxLayout(pos_row)
        pos_row_layout.setContentsMargins(0, 0, 0, 0)

        self.spin_stop_pos: QSpinBox = QSpinBox()
        self.spin_stop_pos.setRange(0, 1000)
        self.spin_stop_pos.setSingleStep(1)
        self.spin_stop_pos.valueChanged.connect(self._apply_selected_stop_position)

        self.lbl_stop_pos_value: QLabel = QLabel("")
        self.lbl_stop_pos_value.setProperty("class", "hint-text")

        pos_row_layout.addWidget(self.spin_stop_pos, 1)
        pos_row_layout.addWidget(self.lbl_stop_pos_value, 1)

        sel_layout.addRow(tr("label_gradient_stop_pos"), pos_row)

        # Color button（背景色＋HEX表示）
        self.btn_stop_color: QPushButton = QPushButton(tr("btn_gradient_stop_color"))
        self.btn_stop_color.setObjectName("ActionBtn")
        self.btn_stop_color.clicked.connect(self._change_selected_stop_color)
        self.btn_stop_color.setToolTip(tr("tip_gradient_stop_color"))
        sel_layout.addRow("", self.btn_stop_color)

        # Add/Delete row
        row_btns: QHBoxLayout = QHBoxLayout()

        self.btn_add_stop: QPushButton = QPushButton(tr("btn_gradient_add_stop"))
        self.btn_add_stop.setObjectName("ActionBtn")
        self.btn_add_stop.clicked.connect(self._add_stop)

        self.btn_delete_stop: QPushButton = QPushButton(tr("btn_gradient_delete_stop"))
        self.btn_delete_stop.setObjectName("DangerBtn")
        self.btn_delete_stop.clicked.connect(self._delete_stop)

        row_btns.addWidget(self.btn_add_stop)
        row_btns.addWidget(self.btn_delete_stop)
        sel_layout.addRow("", row_btns)

        right_col.addStretch(1)

        # =========================
        # Signal wiring (selection sync)
        # =========================
        try:
            if hasattr(self.gradient_widget, "selectedStopChanged"):
                self.gradient_widget.selectedStopChanged.connect(self._on_selected_stop_changed)
            if hasattr(self.gradient_widget, "gradientChanged"):
                self.gradient_widget.gradientChanged.connect(self._sync_selected_stop_ui)
        except Exception:
            pass

        # 言語切替追従
        self._connect_language_changed()

        # 初回同期
        self._sync_selected_stop_ui()

        # 最初はグラデ側にフォーカス
        try:
            self.gradient_widget.setFocus()
        except Exception:
            pass

        # =========================
        # OK / Cancel
        # =========================
        self.button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def refresh_ui_text(self) -> None:
        """言語切替時に、ダイアログ内テキストを更新します。"""
        self.setWindowTitle(tr("title_gradient_editor"))

        if hasattr(self, "lbl_hint"):
            self.lbl_hint.setText(tr("hint_gradient_editor_ops"))

        if hasattr(self, "btn_stop_color"):
            self.btn_stop_color.setToolTip(tr("tip_gradient_stop_color"))

        if hasattr(self, "btn_add_stop"):
            self.btn_add_stop.setText(tr("btn_gradient_add_stop"))
        if hasattr(self, "btn_delete_stop"):
            self.btn_delete_stop.setText(tr("btn_gradient_delete_stop"))

        # GroupBoxタイトル等は選択状態に依存するので同期に寄せる
        self._sync_selected_stop_ui()

    def update_gradient_angle(self, value: int) -> None:
        """角度変更をグラデに反映する。

        Args:
            value (int): 角度（0..360）
        """
        self.gradient_widget.setAngle(int(value))

    def _on_selected_stop_changed(self, index: int) -> None:
        """Gradientウィジェット側の選択変更を右パネルへ反映する。

        Args:
            index (int): 選択されたストップインデックス。
        """
        _ = index
        self._sync_selected_stop_ui()

    def _sync_selected_stop_ui(self) -> None:
        """選択中ストップの位置/色を右パネルに反映する。"""
        try:
            if not hasattr(self, "gradient_widget"):
                return

            idx: Optional[int] = None
            if hasattr(self.gradient_widget, "selected_index"):
                idx = self.gradient_widget.selected_index()

            grad: Any = self.gradient_widget.gradient()
            if idx is None or not isinstance(grad, list) or idx < 0 or idx >= len(grad):
                if hasattr(self, "grp_selected_stop"):
                    self.grp_selected_stop.setEnabled(False)
                    self.grp_selected_stop.setTitle(tr("grp_gradient_selected_stop"))
                if hasattr(self, "lbl_stop_pos_value"):
                    self.lbl_stop_pos_value.setText("")
                return

            # 有効化＋タイトル（1-based表示）
            if hasattr(self, "grp_selected_stop"):
                self.grp_selected_stop.setEnabled(True)
                self.grp_selected_stop.setTitle(tr("grp_gradient_selected_stop_fmt").format(n=int(idx) + 1))

            pos, col = grad[int(idx)]
            pos_f: float = float(pos)
            pos_1000: int = int(round(pos_f * 1000.0))
            pos_pct: float = pos_f * 100.0

            # spin
            if hasattr(self, "spin_stop_pos"):
                self.spin_stop_pos.blockSignals(True)
                self.spin_stop_pos.setValue(pos_1000)
                self.spin_stop_pos.blockSignals(False)

            # 値表示（%併記）
            if hasattr(self, "lbl_stop_pos_value"):
                self.lbl_stop_pos_value.setText(
                    tr("label_gradient_stop_pos_value_fmt").format(v=int(pos_1000), pct=float(pos_pct))
                )

            # 色ボタン（HEX表示＋背景色）
            if hasattr(self, "btn_stop_color"):
                col_str: str = str(col)
                self._set_color_button_style(self.btn_stop_color, col_str)
                self.btn_stop_color.setText(col_str.upper())

            # Deleteボタンの有効/無効（端stopは不可）
            try:
                end_stops: list[int] = list(getattr(self.gradient_widget, "_end_stops"))
            except Exception:
                end_stops = []

            if hasattr(self, "btn_delete_stop"):
                self.btn_delete_stop.setEnabled(int(idx) not in end_stops)

        except Exception:
            pass

    def _set_color_button_style(self, btn: QPushButton, color_str: str) -> None:
        """色ボタンの背景を更新する。

        Args:
            btn (QPushButton): 対象ボタン
            color_str (str): "#RRGGBB" 等
        """
        try:
            c = QColor(color_str)
            if not c.isValid():
                c = QColor("#ffffff")
            lum = c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114
            text_color = "black" if lum > 128 else "white"
            btn.setStyleSheet(f"background-color: {c.name()}; color: {text_color};")
        except Exception:
            pass

    def _apply_selected_stop_position(self, v: int) -> None:
        """選択中ストップの位置（0..1000）を反映する。

        Args:
            v (int): 0..1000（内部は 0.0..1.0）
        """
        try:
            if not hasattr(self, "gradient_widget") or not hasattr(self.gradient_widget, "selected_index"):
                return

            idx = self.gradient_widget.selected_index()
            if idx is None:
                return

            pos = max(0.0, min(1.0, float(int(v)) / 1000.0))
            grad = self.gradient_widget.gradient()
            if idx < 0 or idx >= len(grad):
                return

            _old_pos, col = grad[idx]
            grad[idx] = (pos, col)

            # setGradient は内部でソート＆更新する想定
            self.gradient_widget.setGradient(grad)
            if hasattr(self.gradient_widget, "set_selected_index"):
                self.gradient_widget.set_selected_index(int(idx))

        except Exception:
            pass

    def _change_selected_stop_color(self) -> None:
        """選択中ストップの色を変更する。"""
        try:
            if not hasattr(self, "gradient_widget") or not hasattr(self.gradient_widget, "selected_index"):
                return

            idx = self.gradient_widget.selected_index()
            if idx is None:
                return

            grad = self.gradient_widget.gradient()
            if idx < 0 or idx >= len(grad):
                return

            pos, col = grad[idx]
            current = QColor(str(col))
            color = QColorDialog.getColor(current, self, tr("btn_gradient_stop_color"))
            if not color.isValid():
                return

            grad[idx] = (pos, color.name())
            self.gradient_widget.setGradient(grad)
            if hasattr(self.gradient_widget, "set_selected_index"):
                self.gradient_widget.set_selected_index(int(idx))

        except Exception:
            pass

    def _add_stop(self) -> None:
        """ストップを追加して選択する（v1では中央 0.5 に追加）。"""
        try:
            if not hasattr(self, "gradient_widget"):
                return

            if hasattr(self.gradient_widget, "addStop"):
                self.gradient_widget.addStop(0.5)

            grad = self.gradient_widget.gradient()

            # 0.5に一番近いストップを選ぶ
            best_i = 0
            best_d = 999.0
            for i, (s, _c) in enumerate(grad):
                d = abs(float(s) - 0.5)
                if d < best_d:
                    best_d = d
                    best_i = i

            if hasattr(self.gradient_widget, "set_selected_index"):
                self.gradient_widget.set_selected_index(int(best_i))

        except Exception:
            pass

    def _delete_stop(self) -> None:
        """選択中ストップを削除する（両端は不可）。"""
        try:
            if not hasattr(self, "gradient_widget") or not hasattr(self.gradient_widget, "selected_index"):
                return

            idx = self.gradient_widget.selected_index()
            if idx is None:
                return

            end_stops: list[int]
            try:
                end_stops = list(getattr(self.gradient_widget, "_end_stops"))
            except Exception:
                end_stops = []

            if idx in end_stops:
                QMessageBox.information(self, tr("msg_info"), tr("msg_gradient_cannot_delete_end_stops"))
                return

            if hasattr(self.gradient_widget, "removeStopAtPosition"):
                self.gradient_widget.removeStopAtPosition(int(idx))

            grad = self.gradient_widget.gradient()
            if not grad:
                if hasattr(self, "grp_selected_stop"):
                    self.grp_selected_stop.setEnabled(False)
                return

            new_idx = min(int(idx), len(grad) - 1)
            if hasattr(self.gradient_widget, "set_selected_index"):
                self.gradient_widget.set_selected_index(int(new_idx))

        except Exception:
            pass

    def get_gradient(self) -> Any:
        """現在のグラデーションを返す。"""
        return self.gradient_widget.gradient()

    def get_angle(self) -> int:
        """現在の角度を返す。"""
        return int(self.gradient_widget.angle())


class AlignImagesDialog(QDialog):
    """画像を整列させるためのパラメータ入力ダイアログ。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("title_align_images"))
        self.setModal(True)

        layout = QFormLayout(self)
        self.columns_input = QLineEdit("1")
        self.space_input = QLineEdit("0")
        self.screen_selection = QComboBox()

        screens = QGuiApplication.screens()
        for i, _ in enumerate(screens):
            self.screen_selection.addItem(f"Screen {i + 1}")

        layout.addRow(tr("label_align_columns"), self.columns_input)
        layout.addRow(tr("label_align_space"), self.space_input)
        layout.addRow(tr("label_align_screen"), self.screen_selection)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_values(self) -> Tuple[int, int, int]:
        """入力された列数、間隔、スクリーンインデックスを返す。"""
        try:
            columns = max(1, int(self.columns_input.text()))
            space = int(self.space_input.text())
            screen_index = self.screen_selection.currentIndex()
            return columns, space, screen_index
        except ValueError:
            return 1, 0, 0


class CornerRatioDialog(QDialog):
    """角丸の比率を設定するダイアログ。"""

    def __init__(self, initial_ratio: float, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("title_set_bg_corner_ratio"))

        layout = QVBoxLayout(self)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_ratio * 100))
        layout.addWidget(self.slider)

        self.label = QLabel(f"Corner Ratio: {initial_ratio * 100:.0f}%", self)
        layout.addWidget(self.label)
        self.slider.valueChanged.connect(self.update_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def update_label(self, value: int) -> None:
        self.label.setText(f"Corner Ratio: {value}%")

    def get_ratio(self) -> float:
        return self.slider.value() / 100.0


class TextSpacingDialog(QDialog):
    """文字間隔、行間隔、ウィンドウ内余白を一括設定するダイアログ。

    横書き/縦書きモードに応じて適切なラベルを表示し、
    SpacingSettingsオブジェクトとの変換もサポートする。
    """

    def __init__(
        self,
        h_ratio: float,
        v_ratio: float,
        top: float,
        bottom: float,
        left: float,
        right: float,
        parent: Optional[QWidget] = None,
        is_vertical: bool = False,
    ) -> None:
        super().__init__(parent)
        self._is_vertical = is_vertical

        # タイトルにモード表示を追加
        # mode_suffix = " (縦書き)" if is_vertical else " (横書き)"
        # self.setWindowTitle(tr("title_text_spacing_settings") + mode_suffix)
        self.setWindowTitle(tr("title_text_spacing_settings"))
        self.setFixedWidth(450)
        layout = QVBoxLayout(self)

        # モード表示ラベル
        mode_text = tr("mode_vertical") if is_vertical else tr("mode_horizontal")
        mode_label = QLabel(tr("label_current_mode_fmt").format(mode_text))
        mode_label.setProperty("class", "bold-label")
        layout.addWidget(mode_label)

        # 文字・行間隔グループ
        group_spacing = QGroupBox(tr("grp_char_line_spacing"))
        form_spacing = QFormLayout()

        def create_slider_row(
            value: float, min_val: float, max_val: float
        ) -> Tuple[QDoubleSpinBox, QSlider, QHBoxLayout]:
            spin = QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setSingleStep(0.05)
            spin.setValue(value)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(value * 100))
            spin.valueChanged.connect(lambda v: slider.setValue(int(v * 100)))
            slider.valueChanged.connect(lambda v: spin.setValue(v / 100))
            container = QHBoxLayout()
            container.addWidget(slider)
            container.addWidget(spin)
            return spin, slider, container

        self.h_spin, _, h_layout = create_slider_row(h_ratio, -0.5, 5.0)
        # ラベルの切り替え
        # label_char = tr("label_char_spacing_horz") + (" (縦)" if is_vertical else " (横)")
        form_spacing.addRow(tr("label_spacing_char"), h_layout)

        self.v_spin, _, v_layout = create_slider_row(v_ratio, 0.0, 5.0)
        # label_line = tr("label_line_spacing_vert") + (" (縦)" if is_vertical else " (横)")
        form_spacing.addRow(tr("label_spacing_line"), v_layout)

        group_spacing.setLayout(form_spacing)
        layout.addWidget(group_spacing)

        # ウィンドウ内余白グループ
        group_padding = QGroupBox(tr("grp_window_padding"))
        form_padding = QFormLayout()
        self.top_spin, _, top_layout = create_slider_row(top, 0.0, 5.0)
        form_padding.addRow(tr("label_margin_top"), top_layout)
        self.bottom_spin, _, bottom_layout = create_slider_row(bottom, 0.0, 5.0)
        form_padding.addRow(tr("label_margin_bottom"), bottom_layout)
        self.left_spin, _, left_layout = create_slider_row(left, 0.0, 5.0)
        form_padding.addRow(tr("label_margin_left"), left_layout)
        self.right_spin, _, right_layout = create_slider_row(right, 0.0, 5.0)
        form_padding.addRow(tr("label_margin_right"), right_layout)
        group_padding.setLayout(form_padding)
        layout.addWidget(group_padding)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(buttons)

    def restore_defaults(self) -> None:
        """Reset values to canonical defaults defined in TextWindowConfig."""
        from models.window_config import TextWindowConfig

        defaults = TextWindowConfig()

        # Horizontal
        self.h_spin.setValue(defaults.char_spacing_h)
        self.v_spin.setValue(defaults.line_spacing_h)

        # Padding
        self.top_spin.setValue(defaults.margin_top)
        self.bottom_spin.setValue(defaults.margin_bottom)
        self.left_spin.setValue(defaults.margin_left)
        self.right_spin.setValue(defaults.margin_right)

    def get_values(self) -> Tuple[float, float, float, float, float, float]:
        """設定されたすべての数値を返す（後方互換性のため維持）。"""
        return (
            self.h_spin.value(),
            self.v_spin.value(),
            self.top_spin.value(),
            self.bottom_spin.value(),
            self.left_spin.value(),
            self.right_spin.value(),
        )

    def get_values_dict(self) -> Dict[str, float]:
        """設定値を辞書形式で返す（推奨）。

        Returns:
            横書きモードの場合:
                char_spacing_h, line_spacing_h, margin_*_ratio
            縦書きモードの場合:
                char_spacing_v, line_spacing_v, v_margin_*_ratio
        """
        if self._is_vertical:
            return {
                "char_spacing_v": self.h_spin.value(),
                "line_spacing_v": self.v_spin.value(),
                # Fallback for old vertical_margin usage if needed, but we prefer explicit
                # "vertical_margin_ratio": self.v_spin.value(),
                "v_margin_top_ratio": self.top_spin.value(),
                "v_margin_bottom_ratio": self.bottom_spin.value(),
                "v_margin_left_ratio": self.left_spin.value(),
                "v_margin_right_ratio": self.right_spin.value(),
            }
        else:
            return {
                "char_spacing_h": self.h_spin.value(),
                "line_spacing_h": self.v_spin.value(),
                # Fallback updates for legacy properties (optional but safer for mixins?)
                "horizontal_margin_ratio": self.h_spin.value(),
                # "vertical_margin_ratio" is ambiguous, so we might skip it or map it to line_spacing?
                # For safety, let's update it too since getters reference it if char_spacing_h is missing?
                # Actually getter prefers char_spacing_h.
                "margin_top_ratio": self.top_spin.value(),
                "margin_bottom_ratio": self.bottom_spin.value(),
                "margin_left_ratio": self.left_spin.value(),
                "margin_right_ratio": self.right_spin.value(),
            }

    @property
    def is_vertical(self) -> bool:
        """現在編集中のモードを返す。"""
        return self._is_vertical


class StyleGalleryDialog(BaseTranslatableDialog):
    """保存されたスタイルプリセットをサムネイル付きで一覧表示・選択するダイアログ。"""

    def __init__(self, style_manager: Any, parent: Optional[QWidget] = None) -> None:
        """StyleGalleryDialog を初期化する。

        Args:
            style_manager (Any): StyleManager 相当。
            parent (Optional[QWidget]): 親。
        """
        super().__init__(parent)
        self.setWindowTitle(tr("menu_style_presets"))

        self.style_manager: Any = style_manager
        self.selected_json_path: Optional[str] = None

        try:
            self.resize(600, 500)
        except Exception:
            pass

        layout: QVBoxLayout = QVBoxLayout(self)

        # 検索バー
        search_layout: QHBoxLayout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍"))

        self.search_input: QLineEdit = QLineEdit()
        self.search_input.setPlaceholderText(tr("placeholder_search_styles"))
        self.search_input.textChanged.connect(self.filter_items)

        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # ギャラリーリスト
        self.list_widget: QListWidget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(120, 120))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.itemChanged.connect(self.on_item_changed)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        # OK/Cancel
        self.button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # 言語切替追従
        self._connect_language_changed()

        # 初回ロード（※二重ロードはしない）
        self.load_presets()

    def refresh_ui_text(self) -> None:
        """言語切替時に、ダイアログ内テキストを更新します。"""
        self.setWindowTitle(tr("menu_style_presets"))
        if hasattr(self, "search_input"):
            self.search_input.setPlaceholderText(tr("placeholder_search_styles"))

    def filter_items(self, text: str) -> None:
        """入力テキストに基づいて表示するスタイルをフィルタリングする。

        Args:
            text (str): 検索文字列。
        """
        try:
            q: str = str(text or "").lower()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item.setHidden(q not in item.text().lower())
        except Exception:
            pass

    def load_presets(self) -> None:
        """プリセット一覧を読み込んでリストを更新する。"""
        try:
            with QSignalBlocker(self.list_widget):
                self.list_widget.clear()
                presets = self.style_manager.get_available_presets()

                for p in presets:
                    name: str = str(p.get("name", ""))
                    json_path: str = str(p.get("json_path", ""))
                    thumb_path: Optional[str] = p.get("thumb_path")

                    item = QListWidgetItem(name)
                    item.setData(Qt.UserRole, json_path)
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

                    if thumb_path and os.path.exists(thumb_path):
                        item.setIcon(QIcon(thumb_path))
                    else:
                        pix = QPixmap(120, 120)
                        pix.fill(Qt.gray)
                        item.setIcon(QIcon(pix))

                    self.list_widget.addItem(item)
        except Exception:
            pass

    def show_context_menu(self, pos: QPoint) -> None:
        """アイテムに対する右クリックメニュー（名前変更・削除）を表示。

        Args:
            pos (QPoint): クリック位置（Qtの型は実際には QPoint のはずだが既存互換で受ける）。
        """
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        rename_action = QAction(tr("menu_rename_style"), self)
        rename_action.triggered.connect(lambda: self.list_widget.editItem(item))
        menu.addAction(rename_action)

        menu.addSeparator()

        delete_action = QAction(tr("menu_delete_style"), self)
        delete_action.triggered.connect(lambda: self.delete_preset(item))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def delete_preset(self, item: QListWidgetItem) -> None:
        """プリセットを削除する。

        Args:
            item (QListWidgetItem): 対象アイテム。
        """
        name: str = item.text()
        json_path: Any = item.data(Qt.UserRole)

        ret = QMessageBox.question(
            self,
            tr("menu_delete_style"),
            tr("msg_confirm_delete_style").format(name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return

        if self.style_manager.delete_style(str(json_path)):
            self.load_presets()
        else:
            QMessageBox.warning(self, tr("title_error"), tr("msg_failed_to_delete_style"))

    def on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """ダブルクリックでスタイルを選択して確定する。

        Args:
            item (QListWidgetItem): 対象アイテム。
        """
        try:
            self.selected_json_path = item.data(Qt.UserRole)
        except Exception:
            self.selected_json_path = None
        self.accept()

    def accept(self) -> None:
        """確定時に選択中スタイルパスを確定して閉じる。"""
        try:
            if not self.selected_json_path:
                items = self.list_widget.selectedItems()
                if items:
                    self.selected_json_path = items[0].data(Qt.UserRole)
        except Exception:
            pass

        super().accept()

    def get_selected_style_path(self) -> Optional[str]:
        """選択されたスタイルのパスを返す。

        Returns:
            Optional[str]: jsonパス。
        """
        try:
            return str(self.selected_json_path) if self.selected_json_path else None
        except Exception:
            return None

    def on_item_changed(self, item: QListWidgetItem) -> None:
        """プリセット名の変更をファイル名に反映する。

        Args:
            item (QListWidgetItem): 変更されたアイテム。
        """
        new_name: str = item.text().strip()
        old_json_path: Any = item.data(Qt.UserRole)

        if not old_json_path or not os.path.exists(str(old_json_path)):
            return

        directory: str = os.path.dirname(str(old_json_path))
        old_name: str = os.path.splitext(os.path.basename(str(old_json_path)))[0]

        if new_name == old_name or not new_name:
            return

        new_json_path: str = os.path.join(directory, f"{new_name}.json")

        if os.path.exists(new_json_path):
            QMessageBox.warning(self, tr("title_error"), tr("msg_file_exists"))
            with QSignalBlocker(self.list_widget):
                item.setText(old_name)
            return

        try:
            os.rename(str(old_json_path), new_json_path)

            old_thumb_path: str = os.path.splitext(str(old_json_path))[0] + ".png"
            new_thumb_path: str = os.path.splitext(new_json_path)[0] + ".png"
            if os.path.exists(old_thumb_path):
                os.rename(old_thumb_path, new_thumb_path)

            item.setData(Qt.UserRole, new_json_path)

        except Exception as e:
            QMessageBox.critical(self, tr("title_error"), tr("msg_rename_error").format(e))
            with QSignalBlocker(self.list_widget):
                item.setText(old_name)
            traceback.print_exc()


class AlignImagesRealtimeDialog(BaseTranslatableDialog):
    """画像整列をリアルタイムにプレビューするダイアログ。

    - 列数/間隔をスライダー＋スピンで調整
    - 調整中は Undo を積まない（プレビュー）
    - OKで確定した時だけ、呼び出し元が Undo をまとめて積む前提

    Attributes:
        _on_preview (Callable[[int, int, int], None]): プレビュー更新コールバック
    """

    def __init__(
        self,
        initial_columns: int,
        initial_space: int,
        screen_index: int,
        on_preview: Callable[[int, int, int], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        """AlignImagesRealtimeDialog を初期化する。

        Args:
            initial_columns (int): 初期の列数
            initial_space (int): 初期の間隔(px)
            screen_index (int): 初期のスクリーンindex
            on_preview (Callable[[int, int, int], None]): (columns, space, screen_index) を受けてプレビュー整列する
            parent (Optional[QWidget]): 親
        """
        super().__init__(parent)
        self.setWindowTitle(tr("title_align_images_realtime"))
        self.setModal(True)

        self._on_preview: Callable[[int, int, int], None] = on_preview

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        # Screen
        self.screen_selection = QComboBox()
        screens = QGuiApplication.screens()
        for i, _ in enumerate(screens):
            self.screen_selection.addItem(f"Screen {i + 1}", i)
        self.screen_selection.setCurrentIndex(max(0, int(screen_index)))
        form.addRow(tr("label_align_screen"), self.screen_selection)

        # Columns (slider + spin)
        col_row = QWidget()
        col_layout = QHBoxLayout(col_row)
        col_layout.setContentsMargins(0, 0, 0, 0)

        self.columns_slider = QSlider(Qt.Horizontal)
        self.columns_slider.setRange(1, 50)
        self.columns_slider.setSingleStep(1)
        self.columns_slider.setPageStep(1)

        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 50)

        initial_columns = max(1, int(initial_columns))
        self.columns_slider.setValue(initial_columns)
        self.columns_spin.setValue(initial_columns)

        col_layout.addWidget(self.columns_slider, 2)
        col_layout.addWidget(self.columns_spin, 1)
        form.addRow(tr("label_align_columns_slider"), col_row)

        # Space (slider + spin)
        space_row = QWidget()
        space_layout = QHBoxLayout(space_row)
        space_layout.setContentsMargins(0, 0, 0, 0)

        self.space_slider = QSlider(Qt.Horizontal)
        self.space_slider.setRange(-500, 1000)  # 詰めたい/広げたい両対応
        self.space_slider.setSingleStep(1)
        self.space_slider.setPageStep(10)

        self.space_spin = QSpinBox()
        self.space_spin.setRange(-500, 1000)

        initial_space = int(initial_space)
        self.space_slider.setValue(initial_space)
        self.space_spin.setValue(initial_space)

        space_layout.addWidget(self.space_slider, 2)
        space_layout.addWidget(self.space_spin, 1)
        form.addRow(tr("label_align_space_slider"), space_row)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        # signals
        self.columns_slider.valueChanged.connect(self.columns_spin.setValue)
        self.columns_spin.valueChanged.connect(self.columns_slider.setValue)

        self.space_slider.valueChanged.connect(self.space_spin.setValue)
        self.space_spin.valueChanged.connect(self.space_slider.setValue)

        self.columns_slider.valueChanged.connect(self._emit_preview)
        self.space_slider.valueChanged.connect(self._emit_preview)
        self.screen_selection.currentIndexChanged.connect(self._emit_preview)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # 初回プレビュー
        self._emit_preview()
        self._connect_language_changed()

    def refresh_ui_text(self) -> None:
        """言語切替時にUI文言を更新する（現状は将来用のフック）。"""
        # 将来、ラベルやボタン文言を tr() に置き換えたらここで更新する
        return

    def _emit_preview(self) -> None:
        """現在値でプレビューコールバックを呼ぶ。"""
        try:
            columns: int = int(self.columns_spin.value())
            space: int = int(self.space_spin.value())
            screen_index: int = int(self.screen_selection.currentData())
            self._on_preview(columns, space, screen_index)
        except Exception:
            # プレビューで落ちない
            pass

    def get_values(self) -> tuple[int, int, int]:
        """確定時の値を返す。

        Returns:
            tuple[int, int, int]: (columns, space, screen_index)
        """
        try:
            return (
                int(self.columns_spin.value()),
                int(self.space_spin.value()),
                int(self.screen_selection.currentData()),
            )
        except Exception:
            return (1, 0, 0)

    def _pick_textedit_font_with_fallback(self, preferred: QFont) -> QFont:
        """QTextEdit に適用するフォントを、文字対応状況を見て決める（Windows向けフォールバック）。

        入力欄で ♡ や絵文字が「□」になる問題は、適用フォントがグリフを持っていないのが原因。
        ここでは preferred を優先しつつ、代表的な記号/絵文字が描けない場合にフォールバックする。

        Args:
            preferred (QFont): 設定ファイル等から得た希望フォント。

        Returns:
            QFont: QTextEdit に適用するフォント。
        """
        try:
            # 代表的な「化けやすい」文字（ハートはBMP内、絵文字はサロゲートになる）
            samples: list[str] = ["♡", "♥", "★", "♪", "😀"]

            db: QFontDatabase = QFontDatabase()

            ok = True
            for s in samples:
                try:
                    if not db.supportsCharacter(preferred, s):
                        ok = False
                        break
                except Exception:
                    # supportsCharacter が失敗したら安全側でフォールバック
                    ok = False
                    break

            if ok:
                return preferred

            # Windows の定番フォールバック
            fallback_candidates: list[str] = [
                "Segoe UI Emoji",
                "Segoe UI Symbol",
                "Segoe UI",
            ]

            for fam in fallback_candidates:
                try:
                    if fam in db.families():
                        f = QFont(fam, preferred.pointSize())
                        return f
                except Exception:
                    continue

            # 最後の手段：preferred のまま
            return preferred

        except Exception:
            return preferred


class TextBrowserDialog(BaseTranslatableDialog):
    """HTMLテキストを読み取り専用で表示する汎用ダイアログ（説明書・ライセンス用）。"""

    def __init__(
        self,
        title: str,
        html_content: str,
        parent: Optional[QWidget] = None,
        allow_independence: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        if allow_independence:
            self.setWindowFlags(Qt.Window)

        self.resize(600, 500)

        layout = QVBoxLayout(self)

        from PySide6.QtWidgets import QTextBrowser

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  # リンクをクリック可能にする
        self.text_browser.setHtml(html_content)

        # 少し余白を持たせて読みやすくする
        self.text_browser.setStyleSheet("font-size: 14px; padding: 10px; line-height: 1.4;")

        layout.addWidget(self.text_browser)

        # OKボタン
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

        self._connect_language_changed()

    def refresh_ui_text(self) -> None:
        # タイトルやボタンなどはここで更新可能だが、
        # コンテンツ自体（html_content）は多言語化対応するなら引数で渡す前に分岐する必要がある。
        # ここでは簡易的にウィンドウタイトル等は維持する。
        pass
