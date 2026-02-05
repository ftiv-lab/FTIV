import logging
from typing import Optional

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QFrame, QPlainTextEdit

logger = logging.getLogger(__name__)


class InlineEditorMixin:
    """
    TextWindow および ConnectorLabel にインライン編集機能を提供する Mixin。
    対象クラスは BaseOverlayWindow 相当の QWidget であり、
    self.config, self.text, self.update_text() 等を持つことを想定している。
    """

    def __init__(self, *args, **kwargs):
        # Mixinなので super().__init__ は協調的に呼ぶか、または呼ばない設計にする。
        # ここでは特に初期化不要だが、状態フラグだけ定義しておく。
        self._is_editing: bool = False
        self._inline_editor: Optional[QPlainTextEdit] = None
        self._original_text_for_cancel: str = ""

        # 縦書き時の横書きエディタ用マージン
        self._vertical_edit_margin: int = 4

        # 案A: 編集開始時のサイズを記録（最小サイズ保持用）
        self._edit_start_size: Optional[tuple] = None
        # 案B: 編集開始時の縦書きフラグを記録
        self._edit_start_is_vertical: bool = False

    def _start_inline_edit(self) -> None:
        """インライン編集を開始する。"""
        if self._is_editing:
            return

        # 既存の状態を保存（キャンセル用）
        self._original_text_for_cancel = getattr(self, "text", "")

        # 編集開始時の縦書きフラグを記録
        self._edit_start_is_vertical = getattr(self, "is_vertical", False)

        # --- Geometry Expansion Strategy (Parent Resizing) ---
        # Clipping対策: QPlainTextEditは内部パディングが必要なので、ウィンドウ自体を少し広げる
        # 縦書き対策: 縦長ウィンドウの場合も、編集用にある程度の横幅を確保する
        current_w = self.width()
        current_h = self.height()

        SAFETY_PADDING_W = 40  # 左右の余白+スクロールバーの遊び
        SAFETY_PADDING_H = 20  # 上下の余白

        min_edit_w = current_w + SAFETY_PADDING_W
        min_edit_h = current_h + SAFETY_PADDING_H

        if self._edit_start_is_vertical:
            # 縦書きの場合は強制的に横幅を確保 (例: 250px)
            min_edit_w = max(min_edit_w, 250)

            # --- Phase 5: Adaptive Reset Strategy ---
            # 縦書きの「今の高さ」を引き継ぐと、横書き編集時に「巨大な余白」ができてしまう。
            # そのため、縦書き時は高さを継承せず、最小限の高さ（1行分+余白）にリセットする。
            # Active Metric Sizing (Phase 3) があるため、入力すれば自動で広がる。
            min_edit_h = 60  # SAFETY_PADDING_H (20) + 1 line (approx 30-40)

        else:
            # 横書きの場合も極端に小さいと編集しづらいので最低幅保証
            min_edit_w = max(min_edit_w, 100)
            min_edit_h = max(min_edit_h, 40)

        # 最小編集サイズとして記録
        self._min_edit_size = (min_edit_w, min_edit_h)

        # ウィンドウ自体をリサイズ (TextRendererの描画エリアも広がる)
        self.resize(min_edit_w, min_edit_h)

        # 1. エディタ作成
        try:
            self._inline_editor = QPlainTextEdit(self)
        except TypeError:
            logger.error("InlineEditorMixin must be used with a QWidget subclass.")
            return

        editor = self._inline_editor
        self._is_editing = True

        # 2. スタイル適用
        cfg = getattr(self, "config", None)
        if cfg:
            font = QFont(cfg.font, int(cfg.font_size))
            editor.setFont(font)

            txt_color = str(cfg.font_color)
            bg_color = str(cfg.background_color)

            # 3. Padding & Spacing Calculation (Match TextRenderer)
            font_size = float(getattr(self, "font_size", 12))

            # Outline width
            outline_width = 1.0  # Min width
            if getattr(self, "background_outline_enabled", False):
                ratio = float(getattr(self, "background_outline_width_ratio", 0.05))
                calc_width = font_size * ratio
                outline_width = max(calc_width, 1.0)

            # Margins (Ratios -> Pixels)
            m_top = int(font_size * float(getattr(self, "margin_top_ratio", 0.0)))
            m_bottom = int(font_size * float(getattr(self, "margin_bottom_ratio", 0.0)))
            m_left = int(font_size * float(getattr(self, "margin_left_ratio", 0.3)))
            m_right = int(font_size * float(getattr(self, "margin_right_ratio", 0.0)))

            # Padding = Margin + Outline
            pad_top = int(m_top + outline_width)
            pad_bottom = int(m_bottom + outline_width)
            pad_left = int(m_left + outline_width)
            pad_right = int(m_right + outline_width)

            # Character Spacing
            char_spacing_ratio = float(getattr(self, "horizontal_margin_ratio", 0.0))
            if char_spacing_ratio > 0:
                char_spacing_px = font_size * char_spacing_ratio
                font.setLetterSpacing(QFont.AbsoluteSpacing, char_spacing_px)
                editor.setFont(font)

            # Style Application
            editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {bg_color};
                    color: {txt_color};
                    border: none;
                    margin: 0px;
                    padding-top: {pad_top}px;
                    padding-bottom: {pad_bottom}px;
                    padding-left: {pad_left}px;
                    padding-right: {pad_right}px;
                }}
            """)

        # 3. テキストセット
        editor.setPlainText(self._original_text_for_cancel)
        editor.selectAll()

        # 4. 配置と挙動
        editor.setFrameShape(QFrame.NoFrame)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- Phase 2: No-Wrap Mode ---
        # 縦書き編集時の構造を明確にし、かつ勝手な折り返しを防ぐ
        editor.setLineWrapMode(QPlainTextEdit.NoWrap)

        # エディタの初期サイズ・位置合わせ
        self._on_inline_text_changed()  # 初期サイズ計算のため一度呼ぶ

        editor.show()
        editor.setFocus()

        # 5. イベントフィルタ
        editor.installEventFilter(self)

        # 6. テキスト変更シグナル
        editor.textChanged.connect(self._on_inline_text_changed)

    def _update_editor_geometry(self):
        """エディタのサイズと位置をウィンドウに合わせる"""
        if not self._inline_editor:
            return
        self._inline_editor.setGeometry(self.rect())

    def _on_inline_text_changed(self) -> None:
        """テキスト変更時の自動リサイズ処理（Editor-Driven Sizing）"""
        if not self._inline_editor:
            return

        new_text = self._inline_editor.toPlainText()

        # 縦書きモード中は一時的に横書きとして背景更新
        original_is_vertical = getattr(self, "is_vertical", False)
        temporarily_switched = False

        if original_is_vertical:
            try:
                if hasattr(self, "config"):
                    self.config.is_vertical = False
                    temporarily_switched = True
            except Exception:
                pass

        # 仮更新
        setattr(self, "text", new_text)

        try:
            # 1. レンダリング実行 (背景更新)
            # 注: ここで一時的にウィンドウサイズがRenderer計算値にリサイズされる可能性があるが、
            # 直後に上書きするので問題ない。
            if hasattr(self, "_update_text_immediate"):
                self._update_text_immediate()
            elif hasattr(self, "update_text"):
                self.update_text()

            # 2. Editor-Driven Resizing (エディタサイズ優先)
            # エディタのドキュメントサイズを取得（NoWrapなので全幅が取れる）
            doc = self._inline_editor.document()

            # ドキュメントサイズを正確に反映させるため調整
            doc.adjustSize()
            doc_size = doc.size()

            # --- Phase 3: Active Metric Sizing ---
            # Enterキー直後の「空行」はドキュメントサイズに反映されにくい（Qt仕様）ため
            # 明示的に行数から必要な高さを計算する (Active Metric)
            # これにより、Enterを押した瞬間にウィンドウが物理的に広がり、スクロールを防ぐ

            fm = self._inline_editor.fontMetrics()
            line_height_px = fm.lineSpacing()
            block_count = self._inline_editor.blockCount()

            # 論理的な必要高さ (行数 * 行の高さ + 少々の遊び)
            metric_h = (block_count * line_height_px) + fm.descent() + 10

            # padding情報を取得 (Safetyマージン)
            SAFETY_PADDING_W = 50
            SAFETY_PADDING_H = 30

            req_w = int(doc_size.width()) + SAFETY_PADDING_W

            # ドキュメントサイズと論理計算、大きい方を採用 (Safety Paddingもしっかり加算)
            raw_h = max(int(doc_size.height()), int(metric_h))
            req_h = raw_h + SAFETY_PADDING_H

            # 最小サイズの適用
            min_w, min_h = getattr(self, "_min_edit_size", (0, 0))

            final_w = max(req_w, min_w)
            final_h = max(req_h, min_h)

            current_w = self.width()
            current_h = self.height()

            # 3. 強制リサイズ (TextRendererの結果を上書き)
            if final_w != current_w or final_h != current_h:
                self.resize(final_w, final_h)

            # 4. エディタ追従
            self._update_editor_geometry()

            # カーソルが見える位置へスクロール（ウィンドウサイズが十分なら不要だが念のため）
            self._inline_editor.ensureCursorVisible()

        except Exception as e:
            logger.error(f"Inline edit resize failed: {e}")

        finally:
            # 縦書きフラグを元に戻す
            if temporarily_switched:
                try:
                    if hasattr(self, "config"):
                        self.config.is_vertical = True
                except Exception:
                    pass

    def _finish_inline_edit(self, commit: bool) -> None:
        """編集を終了する。"""
        if not self._is_editing:
            return

        self._is_editing = False
        editor = self._inline_editor
        if not editor:
            return

        final_text = editor.toPlainText()

        try:
            editor.setFocusPolicy(Qt.NoFocus)  # type: ignore
            editor.hide()
            editor.deleteLater()
        except Exception:
            pass
        self._inline_editor = None

        # 縦書きフラグ復元（念のため）
        if self._edit_start_is_vertical:
            try:
                if hasattr(self, "config"):
                    self.config.is_vertical = True
            except Exception:
                pass

        self._min_edit_size = None

        if commit:
            if final_text != self._original_text_for_cancel:
                # 一旦戻してからUndoableでセット
                setattr(self, "text", self._original_text_for_cancel)
                if hasattr(self, "set_undoable_property"):
                    try:
                        self.set_undoable_property("text", final_text, "update_text")
                    except Exception:
                        setattr(self, "text", final_text)
                        if hasattr(self, "update_text"):
                            self.update_text()
                else:
                    setattr(self, "text", final_text)
                    if hasattr(self, "update_text"):
                        self.update_text()
            else:
                # 変更なしでも再描画（縦書きレイアウトに戻るため必須）
                if hasattr(self, "update_text"):
                    self.update_text()
        else:
            # キャンセル：元のテキストに戻す
            setattr(self, "text", self._original_text_for_cancel)
            if hasattr(self, "update_text"):
                self.update_text()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """エディタのキーイベントをフックする。"""
        if obj == self._inline_editor and event.type() == QEvent.KeyPress:
            key_evt = typing_cast_key_event(event)
            key = key_evt.key()
            mods = key_evt.modifiers()

            # Shift+Enter -> Commit
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if mods & Qt.ShiftModifier:
                    self._finish_inline_edit(commit=True)
                    return True  # イベント消費
                # Enterのみは改行許容

            # Escape -> Cancel
            if key == Qt.Key_Escape:
                self._finish_inline_edit(commit=False)
                return True

        # FocusOut 処理
        if obj == self._inline_editor and event.type() == QEvent.FocusOut:
            if self._is_editing:
                self._finish_inline_edit(commit=True)
            return False

        return super().eventFilter(obj, event)


# Helper for type checking inside eventFilter if needed
def typing_cast_key_event(event: QEvent) -> QKeyEvent:
    return event
