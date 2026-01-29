import json
import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_persistence_save_load(qapp, tmp_path):
    """
    ウィンドウ作成 -> 保存 -> 全消去 -> ロード -> 復元確認
    の一連のフローをテストする。
    GUIダイアログを回避するため、FileManagerの内部メソッドを直接使用する。
    """
    mw = MainWindow()
    mw.show()

    # Create dummy file path for Scene JSON
    save_path = tmp_path / "test_scene.json"
    str_path = str(save_path)

    try:
        # 1. Add Text Window (Setup)
        assert len(mw.text_windows) == 0
        from ui.controllers.text_actions import TextActions

        # Direct call to controller logic is easier for Setup than clicking buttons
        actions = TextActions(mw)
        actions.add_new_text_window()

        assert len(mw.text_windows) == 1

        # Modify window content
        target_win = mw.text_windows[0]
        original_uuid = target_win.uuid
        # Use public property or config
        target_win.text = "Persistence Test"
        target_win.move(100, 200)

        # 2. Save Scene (Bypass Dialog)
        file_mgr = mw.file_manager

        # Manually invoke safe save logic
        data = file_mgr.get_scene_data()
        file_mgr._save_json_atomic(str_path, data)

        assert os.path.exists(str_path), "Scene file was not created."

        # 3. Clear All (Simulate New Scene)
        mw.window_manager.clear_all()
        assert len(mw.text_windows) == 0

        # 4. Load Scene (Bypass Dialog)
        with open(str_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        file_mgr.load_scene_from_data(loaded_data)

        # 5. Verify Restoration
        assert len(mw.text_windows) == 1
        restored_win = mw.text_windows[0]

        # UUID should be preserved
        assert restored_win.uuid == original_uuid
        assert restored_win.text == "Persistence Test"
        # Floating point coordinates check
        assert restored_win.x() == 100
        assert restored_win.y() == 200

    finally:
        mw.close()
        for win in mw.text_windows:
            win.close()
