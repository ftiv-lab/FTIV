from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPixmap

from models.window_config import TextWindowConfig
from windows.connector import ConnectorLabel
from windows.text_renderer import TextRenderer
from windows.text_window import TextWindow


def _make_text_window() -> TextWindow:
    with patch.object(TextWindow, "__init__", lambda self, *a, **kw: None):
        obj = TextWindow.__new__(TextWindow)
    obj.config = TextWindowConfig()
    obj.main_window = MagicMock()
    obj.main_window.json_directory = "."
    obj.main_window.settings_manager = MagicMock()
    obj.main_window.settings_manager.load_text_archetype.return_value = None
    obj.main_window.undo_stack = MagicMock()
    obj.child_windows = []
    obj.connected_lines = []
    obj.is_selected = False
    obj._previous_text_opacity = 100
    obj._previous_background_opacity = 100
    obj._render_debounce_ms = 25
    obj._wheel_render_relax_timer = MagicMock()
    obj.canvas_size = MagicMock()
    return obj


def _make_connector_label() -> ConnectorLabel:
    with patch.object(ConnectorLabel, "__init__", lambda self, *a, **kw: None):
        obj = ConnectorLabel.__new__(ConnectorLabel)
    obj.config = TextWindowConfig()
    obj.main_window = MagicMock()
    obj.connector = MagicMock()
    return obj


def test_text_window_double_click_always_starts_dialog():
    w = _make_text_window()
    w.change_text = MagicMock()
    event = MagicMock()
    event.modifiers.return_value = Qt.NoModifier
    event.button.return_value = Qt.MouseButton.LeftButton

    w.mouseDoubleClickEvent(event)

    w.change_text.assert_called_once()
    event.accept.assert_called_once()


def test_text_window_context_menu_has_no_editing_mode_submenu():
    w = _make_text_window()

    class DummyBuilder:
        last_instance = None

        def __init__(self, *_args, **_kwargs):
            self.submenus = []
            DummyBuilder.last_instance = self

        def add_connect_group_menu(self):
            return None

        def add_action(self, *_args, **_kwargs):
            return MagicMock()

        def add_submenu(self, text_key, **_kwargs):
            self.submenus.append(text_key)
            return MagicMock()

        def add_separator(self, **_kwargs):
            return None

        def exec(self, *_args, **_kwargs):
            return None

    with patch("windows.text_window.ContextMenuBuilder", DummyBuilder):
        with patch.object(type(w), "mapToGlobal", return_value=QPoint(0, 0)):
            w.show_context_menu(QPoint(0, 0))

    assert DummyBuilder.last_instance is not None
    assert "menu_text_editing_mode" not in DummyBuilder.last_instance.submenus


@patch("windows.text_window.TextInputDialog")
def test_text_window_dialog_font_is_independent(mock_dialog_cls):
    w = _make_text_window()
    w.config.text = "abc"
    w.config.font = "Arial"
    w.config.font_size = 48
    w.update_text = MagicMock()
    w.screen = MagicMock(return_value=None)

    dialog = MagicMock()
    dialog.exec.return_value = 0  # Rejected
    mock_dialog_cls.return_value = dialog

    w.change_text()

    _args, kwargs = mock_dialog_cls.call_args
    assert "initial_font" not in kwargs


def test_connector_label_double_click_starts_dialog():
    label = _make_connector_label()
    label.edit_text_realtime = MagicMock()
    event = MagicMock()
    event.button.return_value = Qt.MouseButton.LeftButton

    label.mouseDoubleClickEvent(event)

    label.edit_text_realtime.assert_called_once()
    event.accept.assert_called_once()


def test_text_renderer_horizontal_draws_text_without_inline_skip():
    renderer = TextRenderer()
    renderer._draw_horizontal_text_content = MagicMock()

    window = MagicMock()
    window.shadow_enabled = False
    window.outline_enabled = False
    window.second_outline_enabled = False
    window.third_outline_enabled = False
    window.font_color = "#ffffff"
    window.text_opacity = 100
    window.content_mode = "note"
    window.is_vertical = False
    window.font_size = 24
    window.font_family = "Arial"

    from PySide6.QtCore import QSize
    from PySide6.QtGui import QFontMetrics, QPainter

    fm = MagicMock(spec=QFontMetrics)
    fm.height.return_value = 20
    fm.ascent.return_value = 16
    fm.horizontalAdvance.return_value = 10

    pixmap = QPixmap(200, 100)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    try:
        renderer._draw_horizontal_text_elements(
            painter,
            window,
            QSize(200, 100),
            ["test"],
            fm,
            0,
            0,
            0,
            0,
            0,
            1.0,
        )
    finally:
        painter.end()

    assert renderer._draw_horizontal_text_content.called
