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


def test_archetype_persistence(qapp):
    """スタイルをデフォルトとして保存し、新規ウィンドウに継承されるか検証する。"""
    mw = MainWindow()
    mw.show()

    try:
        # 1. 最初のウィンドウを作成
        mw.main_controller.txt_actions.add_new_text_window()
        assert len(mw.text_windows) == 1
        w1 = mw.text_windows[0]

        w1 = mw.text_windows[0]

        # 2. スタイルを変更（目立つ設定に）
        w1.set_undoable_property("font_family", "Courier New", None)
        w1.set_undoable_property("font_size", 99, None)
        # Use simple Red #FF0000 to avoid ARGB/RGBA confusion
        w1.set_undoable_property("font_color", "#FF0000", "update_text")  # Red

        # 3. デフォルトとして保存
        mw.window_manager.set_selected_window(w1)
        mw.main_controller.txt_actions.save_as_default()

        # 4. 新しいウィンドウを作成
        mw.main_controller.txt_actions.add_new_text_window()
        assert len(mw.text_windows) == 2
        w2 = mw.text_windows[1]

        # 5. 検証: Archetypeが適用されているか
        assert w2.font_family == "Courier New"
        assert w2.font_size == 99

        # Color verification
        actual_color = w2.font_color
        if hasattr(actual_color, "name"):
            assert actual_color.name().upper() in ["#FF0000", "#FFFF0000"]
        else:
            assert actual_color.upper() in ["#FF0000", "#FFFF0000"]
    finally:
        mw.close()


def test_vertical_defaults_persistence(qapp):
    """縦書きのデフォルト余白が正しく継承されるか検証する。"""
    mw = MainWindow()
    mw.show()

    try:
        # 1. ウィンドウを作成し縦書きに
        mw.main_controller.txt_actions.add_new_text_window()
        w1 = mw.text_windows[0]
        w1.set_undoable_property("is_vertical", True, "update_text")

        # 2. 縦書き特有の余白を設定
        w1.config.v_margin_top = 0.77

        # 3. デフォルト保存
        mw.window_manager.set_selected_window(w1)
        mw.main_controller.txt_actions.save_as_default()

        # 4. 新規ウィンドウ作成
        mw.main_controller.txt_actions.add_new_text_window()
        w2 = mw.text_windows[1]
        w2.config.is_vertical = True

        # 検証
        assert w2.config.v_margin_top == 0.77
    finally:
        mw.close()
