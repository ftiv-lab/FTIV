from PySide6.QtTest import QTest

from ui.main_window import MainWindow
from utils.translator import tr


def test_show_feedback_message_with_undo(qapp) -> None:
    _ = qapp
    called = {"value": False}

    def _undo() -> None:
        called["value"] = True

    mw = MainWindow()
    try:
        mw.show_feedback_message("hello", timeout_ms=5000, undo_callback=_undo)
        assert mw.footer_label.text() == "hello"
        assert mw.footer_undo_button.isVisible() is True
        assert mw.footer_undo_button.isEnabled() is True

        mw.footer_undo_button.click()
        assert called["value"] is True
        assert mw.footer_undo_button.isVisible() is False
        assert mw.footer_label.text() == tr("footer_msg")
    finally:
        mw.close()


def test_feedback_timer_replaces_previous_message(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        mw.show_feedback_message("first", timeout_ms=20, undo_callback=None)
        mw.show_feedback_message("second", timeout_ms=200, undo_callback=None)

        QTest.qWait(60)
        assert mw.footer_label.text() == "second"

        QTest.qWait(200)
        assert mw.footer_label.text() == tr("footer_msg")
    finally:
        mw.close()


def test_show_status_message_uses_feedback_path(qapp) -> None:
    _ = qapp
    mw = MainWindow()
    try:
        mw.show_status_message("status", timeout_ms=50)
        assert mw.footer_label.text() == "status"
        QTest.qWait(80)
        assert mw.footer_label.text() == tr("footer_msg")
    finally:
        mw.close()
