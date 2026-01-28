from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QAction, QFocusEvent, QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPlainTextEdit

from windows.connector import ConnectorLabel
from windows.text_window import TextWindow


class MockMainWindow:
    def __init__(self):
        self.app_settings = MagicMock()
        self.app_settings.glyph_cache_size = 512
        self.app_settings.render_debounce_ms = 10
        self.app_settings.wheel_debounce_ms = 10
        self.undo_stack = MagicMock()
        self.undo_action = QAction("Undo")
        self.redo_action = QAction("Redo")
        self.json_directory = "."  # Dummy path

    def add_undo_command(self, command):
        self.undo_stack.push(command)


@pytest.fixture
def mock_main_window(qapp):
    return MockMainWindow()


@pytest.fixture
def text_window(mock_main_window):
    # TextRenderer をモックしてCI環境でのフォント問題を回避
    from PySide6.QtGui import QColor, QPixmap

    with patch("windows.text_window.TextRenderer") as MockRenderer:
        # render メソッドが (pixmap, mask) を返すように設定
        instance = MockRenderer.return_value

        # Fix: render method should return only pixmap for QLabel.setPixmap
        def render(self, *args, **kwargs):
            pixmap = QPixmap(100, 100)
            pixmap.fill(QColor("transparent"))
            return pixmap

        instance.render.side_effect = render

        win = TextWindow(mock_main_window, "Initial Text", QPoint(0, 0))
        # Mixinが正しく初期化されているか確認
        assert hasattr(win, "_start_inline_edit")
        return win


@pytest.fixture
def connector_label(mock_main_window):
    from PySide6.QtGui import QBitmap, QPixmap

    connector = MagicMock()
    with patch("windows.connector.TextRenderer") as MockRenderer:
        # render メソッドが (pixmap, mask) を返すように設定
        instance = MockRenderer.return_value
        instance.render.return_value = (QPixmap(100, 100), QBitmap(100, 100))

        label = ConnectorLabel(mock_main_window, connector, "Label Text")
        return label


def test_text_window_inline_edit_start(text_window, qapp):
    """TextWindowでインライン編集が開始されるかテスト"""
    window = text_window
    window.show()

    # まだ編集モードではない
    assert not window._is_editing
    assert window._inline_editor is None

    # 編集開始
    window._start_inline_edit()

    assert window._is_editing
    assert isinstance(window._inline_editor, QPlainTextEdit)
    assert window._inline_editor.isVisible()
    assert window._inline_editor.toPlainText() == "Initial Text"


def test_text_window_commit_changes(text_window, qapp):
    """変更をコミットできるかテスト"""
    window = text_window
    window.show()

    window._start_inline_edit()
    editor = window._inline_editor

    # テキスト変更
    editor.setPlainText("New Text")

    # 変更フラグなどはMixin内部で処理される
    # _finish_inline_edit(commit=True) を呼ぶ
    window._finish_inline_edit(commit=True)

    assert not window._is_editing
    assert window._inline_editor is None
    window.main_window.undo_stack.push.assert_called()


def test_text_window_cancel_changes(text_window, qapp):
    """変更をキャンセルできるかテスト"""
    window = text_window
    window.show()

    original_text = window.text
    window._start_inline_edit()
    editor = window._inline_editor

    # テキスト変更
    editor.setPlainText("Changed Text")

    # キャンセル
    window._finish_inline_edit(commit=False)

    assert not window._is_editing
    assert window.text == original_text


def test_connector_label_inline_edit(connector_label, qapp):
    """ConnectorLabelでもインライン編集が機能するかテスト"""
    label = connector_label
    label.show()

    assert not label._is_editing

    label._start_inline_edit()

    assert label._is_editing
    assert isinstance(label._inline_editor, QPlainTextEdit)
    assert label._inline_editor.toPlainText() == "Label Text"

    # 変更とコミット
    label._inline_editor.setPlainText("Updated Label")
    label._finish_inline_edit(commit=True)

    assert not label._is_editing
    label.main_window.undo_stack.push.assert_called()


def test_double_click_triggers_edit(text_window, qapp):
    """ダブルクリックで編集が開始されるか（イベント統合テスト）"""
    window = text_window
    window.show()

    # QTest.mouseDClick などを使う
    QTest.mouseDClick(window, Qt.MouseButton.LeftButton)

    # ダブルクリックイベント処理が正しければ編集モードに入っているはず
    assert window._is_editing
    assert window._inline_editor is not None


def test_shift_enter_commits(text_window, qapp):
    """Shift+Enterでコミットされるかテスト"""
    window = text_window
    window.show()
    window._start_inline_edit()

    editor = window._inline_editor
    editor.setPlainText("Committed Text")
    editor.setFocus()

    # Use direct eventFilter call to be robust against QTest focus issues in headless
    # This verifies the LOGIC flow completely
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.ShiftModifier)
    res = window.eventFilter(editor, event)

    assert res is True
    assert not window._is_editing
    # assert window.text == "Committed Text" # Mock undo_stack doesn't execute redo
    window.main_window.undo_stack.push.assert_called()


def test_focus_out_commits(text_window, qapp):
    """フォーカスアウトでコミットされるかテスト"""
    window = text_window
    window.show()
    window._start_inline_edit()

    editor = window._inline_editor
    editor.setPlainText("FocusOut Text")

    # Direct eventFilter call for FocusOut
    event = QFocusEvent(QEvent.FocusOut, Qt.OtherFocusReason)
    window.eventFilter(editor, event)

    assert not window._is_editing
    # assert window.text == "FocusOut Text" # Mock undo_stack doesn't execute redo
    window.main_window.undo_stack.push.assert_called()


def test_event_filter_logic_direct(text_window, qapp):
    """eventFilterのロジックを直接テスト"""
    window = text_window
    window.show()
    window._start_inline_edit()
    editor = window._inline_editor

    editor.setPlainText("Filter Logic Text")  # Change text to trigger commit

    # Shift+Enter logic
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.ShiftModifier)

    # Direct call
    result = window.eventFilter(editor, event)

    assert result is True  # Should consume event
    assert not window._is_editing
    # assert window.text == "Filter Logic Text" # Mock undo_stack doesn't execute redo
    window.main_window.undo_stack.push.assert_called()


def test_scroll_during_edit_does_not_resize(text_window, qapp):
    """インライン編集中はスクロールによるリサイズが無効化されるべき"""
    window = text_window
    window.show()
    window._start_inline_edit()

    # Simulate Wheel Event: Delta > 0 -> Up -> Shrink (in current logic: new_size = current - step)
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QWheelEvent

    # Simple construction for PySide6
    angle_delta = QPoint(0, 120)
    event = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        angle_delta,
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )

    window.wheelEvent(event)

    # Should NOT change size (Ref: Issue Phase 26)
    # Since UndoStack is mocked, the value won't change, but a command should NOT be pushed.
    window.main_window.undo_stack.push.assert_not_called()
