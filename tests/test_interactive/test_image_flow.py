import sys
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from ui.main_window import MainWindow


# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_image_add_flow(qapp, tmp_path):
    """
    アプリ起動 -> 画像追加ボタン -> ファイル選択ダイアログ(Mock) -> 画像追加
    のフローを検証する。
    """
    # 1. Create a dummy image file
    dummy_image_path = tmp_path / "test_image.png"
    # Create a simple red 10x10 png using PIL or by writing bytes if PIL unavailable in test env?
    # Environment has Pillow installed.
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="red")
    img.save(dummy_image_path)

    str_path = str(dummy_image_path)

    # 2. Start App
    mw = MainWindow()
    mw.show()

    try:
        # Initial check
        assert len(mw.image_windows) == 0, "Should start with 0 image windows"

        # 3. Add Image Window (Simulate click + Mock Dialog)

        # Target button
        btn_add = mw.image_tab.btn_add_image_main

        # Patch QFileDialog to return our dummy path
        # Note: The code does `from PySide6.QtWidgets import QFileDialog` inside the method `add_new_image`.
        # So we must patch `PySide6.QtWidgets.QFileDialog.getOpenFileName`.

        future_file = (str_path, "Images (*.png ...)")

        with pytest.MonkeyPatch.context() as m:
            # We mock the return value of getOpenFileName
            m.setattr(QFileDialog, "getOpenFileName", MagicMock(return_value=future_file))

            # Click!
            QTest.mouseClick(btn_add, Qt.LeftButton)

        # 4. Verify
        # Image should be added asynchronously or synchronously?
        # add_image_from_path is usually synchronous in this app structure unless using ThreadPool (which it doesn't seem to for local).

        assert len(mw.image_windows) == 1, "Image window count should be 1 after adding"

        new_win = mw.image_windows[0]
        assert new_win.isVisible(), "New image window should be visible"
        # Check source path or object name if available
        # ImageWindow might not store the full path as a public property easily accessible,
        # but we can check if it has a pixmap.
        assert not new_win.pixmap().isNull(), "Image window should have a valid pixmap"

    finally:
        mw.close()
        for win in mw.image_windows:
            win.close()
