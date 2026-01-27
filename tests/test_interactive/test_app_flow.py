import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_app_startup_and_add_text(qapp):
    """
    アプリ起動 -> テキスト追加 -> ウィンドウ数増加を確認するE2Eテスト。
    pytest-qtを使わず、QTestと直接インスタンス化で行う。
    """
    from ui.main_window import MainWindow

    # 1. Start App
    mw = MainWindow()
    mw.show()  # QTest needs it to be shown or at least created

    try:
        # Initial check
        assert len(mw.text_windows) == 0, "Should start with 0 text windows"

        # 2. Add Text Window (Simulate click)
        # Assuming the button is accessible via Tab structure (verified in Phase 12)
        btn_add = mw.text_tab.btn_add_text_main

        # Click the button using QTest
        QTest.mouseClick(btn_add, Qt.LeftButton)

        # 3. Verify
        assert len(mw.text_windows) == 1, "Text window count should be 1 after adding"

        # Check if the new window is visible
        new_win = mw.text_windows[0]
        assert new_win.isVisible(), "New text window should be visible"

    finally:
        # Cleanup
        mw.close()
        # Close any spawned windows
        for win in mw.text_windows:
            win.close()
