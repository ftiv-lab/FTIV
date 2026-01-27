import sys

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from ui.controllers.text_actions import TextActions
from ui.main_window import MainWindow
from utils.commands import MoveWindowCommand


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_undo_redo_move(qapp):
    """
    ウィンドウ移動(Command) -> Undo -> 位置が戻る -> Redo -> 位置が進む
    を確認する。
    """
    mw = MainWindow()
    mw.show()

    try:
        # Setup: Add Text Window
        actions = TextActions(mw)
        actions.add_new_text_window()
        assert len(mw.text_windows) == 1
        win = mw.text_windows[0]

        # Initial Position
        p0 = QPoint(100, 100)
        p1 = QPoint(200, 200)
        win.move(p0)
        assert win.pos() == p0

        # Execute Move via Command
        cmd = MoveWindowCommand(win, p0, p1)
        # Usually pushed to stack, which calls redo()
        mw.undo_stack.push(cmd)

        # Verify Redo (Immediate effect)
        assert win.pos() == p1

        # UNDO
        mw.undo_stack.undo()
        assert win.pos() == p0

        # REDO
        mw.undo_stack.redo()
        assert win.pos() == p1

    finally:
        mw.close()
