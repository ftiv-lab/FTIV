import logging
from typing import Any, Optional, cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QFont, QFontInfo, QKeyEvent, QTextBlockFormat, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QFrame, QPlainTextEdit, QWidget

logger = logging.getLogger(__name__)

# カーソル表示用の最小追加幅
_CURSOR_EXTRA: int = 4


class InlineEditorMixin:
    """
    TextWindow および ConnectorLabel にインライン編集機能を提供する Mixin。
    対象クラスは BaseOverlayWindow 相当の QWidget であり、
    self.config, self.text, self.update_text() 等を持つことを想定している。
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._is_editing: bool = False
        self._inline_editor: Optional[QPlainTextEdit] = None
        self._original_text_for_cancel: str = ""
        self._edit_start_is_vertical: bool = False
        self._min_edit_size: Optional[tuple[int, int]] = None
        self._edit_layout_info: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Layout info helper
    # ------------------------------------------------------------------

    def _get_renderer_layout_info(self) -> Optional[dict[str, Any]]:
        """TextRenderer.get_editing_layout_info() からレイアウト情報を取得する。"""
        renderer = getattr(self, "renderer", None)
        if renderer is None or not hasattr(renderer, "get_editing_layout_info"):
            return None
        try:
            info = renderer.get_editing_layout_info(self)
            if not isinstance(info, dict) or "canvas_size" not in info:
                return None
            return info
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def _start_inline_edit(self) -> None:
        """インライン編集を開始する。"""
        if self._is_editing:
            return

        self._original_text_for_cancel = getattr(self, "text", "")
        self._edit_start_is_vertical = getattr(self, "is_vertical", False)

        # --- レイアウト情報を TextRenderer から取得 ---
        layout_info = self._get_renderer_layout_info()
        self._edit_layout_info = layout_info

        # --- ウィンドウサイズ決定 (canvas_size ベース) ---
        if layout_info:
            canvas = layout_info["canvas_size"]
            min_edit_w = canvas.width() + _CURSOR_EXTRA
            min_edit_h = canvas.height() + _CURSOR_EXTRA
        else:
            min_edit_w = self.width() + _CURSOR_EXTRA
            min_edit_h = self.height() + _CURSOR_EXTRA

        if self._edit_start_is_vertical:
            min_edit_w = max(min_edit_w, 250)
            min_edit_h = 60
        else:
            min_edit_w = max(min_edit_w, 100)
            min_edit_h = max(min_edit_h, 40)

        self._min_edit_size = (min_edit_w, min_edit_h)
        self.resize(min_edit_w, min_edit_h)

        # --- エディタ作成 ---
        try:
            self._inline_editor = QPlainTextEdit(cast(QWidget, self))
        except TypeError:
            logger.error("InlineEditorMixin must be used with a QWidget subclass.")
            return

        editor = self._inline_editor
        self._is_editing = True

        # --- 配置と挙動 (スタイル適用前に設定) ---
        editor.setFrameShape(QFrame.Shape.NoFrame)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # --- documentMargin を 0 に設定 ---
        editor.document().setDocumentMargin(0)

        # --- フォント設定 (pixelSize 強制) ---
        cfg = getattr(self, "config", None)
        if cfg:
            # 1) TextRenderer と同じ pointSize フォントから pixelSize を取得
            ref_font = QFont(cfg.font, int(cfg.font_size))
            ref_fi = QFontInfo(ref_font)
            resolved_pixel_size = ref_fi.pixelSize()

            # 2) pixelSize を直接指定してエディタ用フォントを作成
            font = QFont(cfg.font)
            font.setPixelSize(resolved_pixel_size)
            font.setKerning(False)

            # 文字間隔
            char_spacing_ratio = float(getattr(self, "horizontal_margin_ratio", 0.0))
            if char_spacing_ratio > 0:
                char_spacing_px = float(cfg.font_size) * char_spacing_ratio
                font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, char_spacing_px)

            txt_color = str(cfg.font_color)

            # --- パディング: setViewportMargins で明示的に制御 ---
            # (CSS padding は QSS 解釈で曖昧になるため使わない)
            if layout_info:
                pad_top = layout_info["pad_top"]
                pad_bottom = layout_info["pad_bottom"]
                pad_left = layout_info["pad_left"]
                pad_right = layout_info["pad_right"]
            else:
                font_size = float(cfg.font_size)
                outline_width = 1.0
                if getattr(self, "background_outline_enabled", False):
                    ratio = float(getattr(self, "background_outline_width_ratio", 0.05))
                    outline_width = max(font_size * ratio, 1.0)
                pad_top = int(float(getattr(self, "margin_top_ratio", 0.0)) * font_size + outline_width)
                pad_bottom = int(float(getattr(self, "margin_bottom_ratio", 0.0)) * font_size + outline_width)
                pad_left = int(float(getattr(self, "margin_left_ratio", 0.0)) * font_size + outline_width)
                pad_right = int(float(getattr(self, "margin_right_ratio", 0.0)) * font_size + outline_width)

            # --- グローバル QSS (theme_manager) がフォントを上書きするため ---
            # ローカル QSS にフォント指定を含めて明示的に上書きする
            font_family_escaped = cfg.font.replace('"', '\\"')
            editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: transparent;
                    color: {txt_color};
                    border: none;
                    margin: 0px;
                    padding: 0px;
                    font-family: "{font_family_escaped}";
                    font-size: {resolved_pixel_size}px;
                }}
            """)

            # document のデフォルトフォントも明示設定 (カーニング無効等)
            editor.document().setDefaultFont(font)

            # ビューポートマージンで TextRenderer と同じ位置にテキストを配置
            editor.setViewportMargins(pad_left, pad_top, pad_right, pad_bottom)

        # --- line_spacing_h の反映 ---
        if layout_info and layout_info.get("line_spacing_px", 0) > 0:
            fmt = QTextBlockFormat()
            fmt.setLineHeight(
                float(layout_info["line_spacing_px"]),
                3,  # LineDistanceHeight
            )
            cursor = editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.mergeBlockFormat(fmt)
            editor.setTextCursor(cursor)

        # --- テキストセット ---
        editor.setPlainText(self._original_text_for_cancel)

        # --- QTextCharFormat でフォントをコンテンツに直接適用 ---
        # QSS はウィジェットフォントを制御するが、document layout の
        # idealWidth() やカーニング設定には反映されない。
        # QTextCharFormat で既存テキスト + 新規入力テキストに直接適用する。
        if cfg:
            char_fmt = QTextCharFormat()
            char_fmt.setFont(font)
            cursor = editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.mergeCharFormat(char_fmt)
            editor.setTextCursor(cursor)
            editor.setCurrentCharFormat(char_fmt)

        # --- 初期サイズ計算 ---
        self._on_inline_text_changed()

        # --- 全選択 + ビューポート先頭にスクロール ---
        # selectAll() → カーソルが末尾 → ensureCursorVisible() でスクロール
        # の問題を避けるため、Start→End 方向で選択
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End,
            QTextCursor.MoveMode.KeepAnchor,
        )
        editor.setTextCursor(cursor)
        editor.horizontalScrollBar().setValue(0)
        editor.verticalScrollBar().setValue(0)

        editor.show()
        editor.setFocus()
        editor.installEventFilter(self)
        editor.textChanged.connect(self._on_inline_text_changed)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def _update_editor_geometry(self) -> None:
        """エディタのサイズと位置をウィンドウに合わせる。"""
        if not self._inline_editor:
            return
        self._inline_editor.setGeometry(self.rect())

    # ------------------------------------------------------------------
    # Text Changed → Resize
    # ------------------------------------------------------------------

    def _on_inline_text_changed(self) -> None:
        """テキスト変更時の自動リサイズ処理 (canvas_size ベース)。"""
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

        setattr(self, "text", new_text)

        try:
            # 1. TextRenderer で背景描画 (_is_editing=True → テキストスキップ)
            if hasattr(self, "_update_text_immediate"):
                self._update_text_immediate()
            elif hasattr(self, "update_text"):
                self.update_text()

            # 2. canvas_size ベースのサイジング
            canvas_size = getattr(self, "canvas_size", None)

            if canvas_size:
                req_w = canvas_size.width() + _CURSOR_EXTRA
                req_h = canvas_size.height() + _CURSOR_EXTRA
            else:
                # フォールバック: ドキュメントサイズベース
                doc = self._inline_editor.document()
                doc.adjustSize()
                doc_size = doc.size()
                fm = self._inline_editor.fontMetrics()
                block_count = self._inline_editor.blockCount()
                metric_h = (block_count * fm.lineSpacing()) + fm.descent() + 10
                req_w = int(doc_size.width()) + 50
                req_h = max(int(doc_size.height()), int(metric_h)) + 30

            min_w, min_h = self._min_edit_size or (0, 0)
            final_w = max(req_w, min_w)
            final_h = max(req_h, min_h)

            if final_w != self.width() or final_h != self.height():
                self.resize(final_w, final_h)

            self._update_editor_geometry()
            self._inline_editor.ensureCursorVisible()

        except Exception as e:
            logger.error(f"Inline edit resize failed: {e}")

        finally:
            if temporarily_switched:
                try:
                    if hasattr(self, "config"):
                        self.config.is_vertical = True
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Finish
    # ------------------------------------------------------------------

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
            editor.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            editor.hide()
            editor.deleteLater()
        except Exception:
            pass
        self._inline_editor = None
        self._edit_layout_info = None

        # 縦書きフラグ復元
        if self._edit_start_is_vertical:
            try:
                if hasattr(self, "config"):
                    self.config.is_vertical = True
            except Exception:
                pass

        self._min_edit_size = None

        if commit:
            if final_text != self._original_text_for_cancel:
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
                if hasattr(self, "update_text"):
                    self.update_text()
        else:
            setattr(self, "text", self._original_text_for_cancel)
            if hasattr(self, "update_text"):
                self.update_text()

    # ------------------------------------------------------------------
    # Event Filter
    # ------------------------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """エディタのキーイベントをフックする。"""
        if obj == self._inline_editor and event.type() == QEvent.Type.KeyPress:
            key_evt = typing_cast_key_event(event)
            key = key_evt.key()
            mods = key_evt.modifiers()

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if mods & Qt.KeyboardModifier.ControlModifier:
                    if hasattr(self, "_toggle_task_line_under_cursor"):
                        self._toggle_task_line_under_cursor()
                    return True
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    self._finish_inline_edit(commit=True)
                    return True

            if key == Qt.Key.Key_Escape:
                self._finish_inline_edit(commit=False)
                return True

        if obj == self._inline_editor and event.type() == QEvent.Type.FocusOut:
            if self._is_editing:
                self._finish_inline_edit(commit=True)
            return False

        return super().eventFilter(obj, event)  # type: ignore[misc]


def typing_cast_key_event(event: QEvent) -> QKeyEvent:
    return event
