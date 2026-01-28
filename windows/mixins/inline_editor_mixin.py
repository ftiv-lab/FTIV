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

    def _start_inline_edit(self) -> None:
        """インライン編集を開始する。"""
        if self._is_editing:
            return

        # 既存の状態を保存（キャンセル用）
        self._original_text_for_cancel = getattr(self, "text", "")

        # 1. エディタ作成
        try:
            self._inline_editor = QPlainTextEdit(self)
        except TypeError:
            # self が QWidget 継承でない場合（稀だが）
            logger.error("InlineEditorMixin must be used with a QWidget subclass.")
            return

        editor = self._inline_editor
        self._is_editing = True

        # 2. スタイル適用
        # 設定オブジェクト (self.config) からフォント情報を取得
        cfg = getattr(self, "config", None)
        if cfg:
            font = QFont(cfg.font, int(cfg.font_size))
            editor.setFont(font)

            # テキスト色（背景は透過か、ウィンドウ背景に合わせる）
            # ここではシンプルに「ウィンドウと同じ背景色（不透明）」にする
            # 理由: 透明にすると元のテキスト（縦書きなど）が透けて見えて邪魔になるため
            txt_color = str(cfg.font_color)
            bg_color = str(cfg.background_color)

            # スタイルシートで設定（枠線なし、背景色、文字色）
            # selection-background-color も設定すると良いが、一旦デフォルト
            editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {bg_color};
                    color: {txt_color};
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }}
            """)

        # 3. テキストセット
        # 縦書きの場合でも、エディタは横書きでテキストを表示する（仕様通り）
        editor.setPlainText(self._original_text_for_cancel)
        editor.selectAll()  # 全選択状態で開始（上書きしやすく）

        # 4. 配置と挙動
        editor.setFrameShape(QFrame.NoFrame)
        # スクロールバーは原則出さない（オートリサイズするため）が、画面外に出る場合は出るかもしれない
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # エディタの初期サイズ・位置合わせ
        self._update_editor_geometry()

        editor.show()
        editor.setFocus()

        # 5. イベントフィルタ (Shift+Enter, Esc)
        editor.installEventFilter(self)

        # 6. テキスト変更シグナル
        editor.textChanged.connect(self._on_inline_text_changed)

        # 7. 元の描画を隠すためのフラグが必要なら設定
        # ただし、エディタが不透明背景(background_color)を持っていれば
        # 上に被さるので元のテキストは見えなくなるはず。
        # 透過背景(opacity < 100)の場合は混ざるが、編集中だけ opacity 100 にする手もある。
        # いったんそのまま（エディタが上に被さる）で進める。
        # 半透明ウィンドウの場合はエディタも半透明になる（親のOpacity継承）点に注意。

    def _update_editor_geometry(self):
        """エディタのサイズと位置をウィンドウに合わせる"""
        if not self._inline_editor:
            return

        # 親ウィンドウのクライアント領域全体を使う
        # 余白 (padding) は TextRenderer が計算しているが、
        # QPlainTextEdit 自体の margin/padding と整合させるのは難しい。
        # ここでは「全体を覆う」アプローチをとる。

        rect = self.rect()

        # 若干のマージンを持たせる（枠線などがある場合）
        # TextRenderer の outline_width 分くらいは内側が良いかもしれないが、
        # 厳密すぎると文字が切れるので、広めに取る。
        self._inline_editor.setGeometry(rect)

    def _on_inline_text_changed(self) -> None:
        """テキスト変更時の自動リサイズ処理"""
        if not self._inline_editor:
            return

        new_text = self._inline_editor.toPlainText()

        # 現在のテキストを仮適用して、TextRenderer にサイズ計算させる
        # ただし、描画は更新したくない（チラつくので）
        # でも resize() を呼ぶには TextRenderer の計算が必要...
        # 解決策: self.config.text を書き換えて、TextRenderer.render() を呼び、
        # QPixmapは捨てるが、side effectとして self.canvas_size が更新され、self.resize() されるのを期待する。

        # 縦書きモードの場合は「横書きエディタ」の入力内容を「縦書きレイアウト」で計算すると
        # 縦長になりすぎる（編集中は横書きで見せたいのにウィンドウが縦に伸びる）問題があるか？
        # -> はい、あります。

        is_vert = getattr(self, "is_vertical", False)

        if is_vert:
            # 縦書きモード中の編集:
            # 文面は "横書き" でエディタに出ている。
            # しかしウィンドウサイズは "縦書き" の最終形態に合わせてリサイズすると、
            # エディタの表示領域（横長）と合わなくなる可能性がある。
            #
            # 解法: 編集中は「ウィンドウサイズをエディタの内容（横書き）に合わせて広げる」か？
            # -> それはウィンドウの位置(x,y)や回転などを破壊する恐れがある。
            #
            # MVPアプローチ:
            # 編集中はウィンドウのリサイズを行わない（スクロールさせる）、
            # もしくは「縦書きレンダリング結果」のサイズに合わせてウィンドウ枠を広げる（既存ロジック）。
            # ユーザーは「確定後」に正しいレイアウトを見る。
            #
            # ただし、行が増えたときに枠が広がらないと入力文字が見えない。
            # なので、やはり「テキスト更新 -> ジオメトリ更新」は必要。
            pass

        # 仮更新（Undoスタックには積まない）
        # 直接代入 (setter経由だと再描画が走る可能性があるが、update_text()を呼ばなければ軽い？)
        # TextWindow.text setter は config.text = val するだけ。
        setattr(self, "text", new_text)

        # サイズ計算だけ行いたい。
        # TextRenderer.render() を呼ぶと resize() までやってくれる。
        # 編集中なのでパフォーマンスは気にせず都度呼ぶ。
        # ただし Undoable Property として登録してしまうと履歴が汚れるので、
        # ここでは「プロパティとしての変更」ではなく「内部状態の一時変更」とする。

        try:
            # レンダリング実行（リサイズ含む）
            # ConnectorLabel / TextWindow 共に _update_text_immediate 等を持っている
            if hasattr(self, "_update_text_immediate"):
                self._update_text_immediate()
            elif hasattr(self, "update_text"):
                self.update_text()

            # エディタのサイズも追従させる
            self._update_editor_geometry()

            # エディタにフォーカスを戻す（念のため）
            self._inline_editor.setFocus()

        except Exception as e:
            logger.error(f"Inline edit resize failed: {e}")

    def _finish_inline_edit(self, commit: bool) -> None:
        """編集を終了する。"""
        # 二重呼び出しガード: _is_editing が False なら即リターン
        if not self._is_editing:
            return

        # フラグを下ろす（再入防止）
        self._is_editing = False

        editor = self._inline_editor
        if not editor:
            return

        final_text = editor.toPlainText()

        # エディタの非表示・フォーカス解除を確実に行う
        try:
            editor.setFocusPolicy(Qt.NoFocus)  # type: ignore
            editor.hide()
        except Exception:
            pass

        # エディタ破棄スケジュール
        try:
            editor.deleteLater()
        except Exception:
            pass
        self._inline_editor = None

        if commit:
            # 変更があれば Undoable Property として確定
            if final_text != self._original_text_for_cancel:
                # 一旦元のテキストに戻してから、正規の手順（Undoable）でセットする
                setattr(self, "text", self._original_text_for_cancel)

                if hasattr(self, "set_undoable_property"):
                    try:
                        self.set_undoable_property("text", final_text, "update_text")
                    except Exception as e:
                        logger.error(f"Failed to commit inline edit: {e}")
                        # Fallback to direct set if undo failed
                        setattr(self, "text", final_text)
                        if hasattr(self, "update_text"):
                            self.update_text()
                else:
                    # fallback
                    setattr(self, "text", final_text)
                    if hasattr(self, "update_text"):
                        self.update_text()
            else:
                # 変更なし：状態としてはリセット不要だが、念のため再描画
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
