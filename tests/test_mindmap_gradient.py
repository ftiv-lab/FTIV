import os
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

# プロジェクトルートパス追加
sys.path.append(os.getcwd())

from ui.main_window import MainWindow
from ui.mindmap.mindmap_node import MindMapNode


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    yield app


def test_mindmap_gradient_interactions(qapp):
    """MindMapNodeのテキスト/背景グラデーション操作のE2Eテスト"""
    mw = MainWindow()
    mw.show()
    mw.app_mode_manager.switch_to_mindmap()

    # 1. ノード追加
    canvas = mw.mindmap_widget.canvas
    node = MindMapNode("Gradient Test Node")
    canvas.scene().addItem(node)
    node.setSelected(True)

    # 2. PropertyPanel 取得
    prop_panel = mw.property_panel
    assert prop_panel.current_target == node

    # --- テキストグラデーション ---
    # UI要素の存在確認
    assert hasattr(prop_panel, "btn_text_gradient_toggle")
    assert hasattr(prop_panel, "btn_edit_text_gradient")

    # トグル有効化
    prop_panel.btn_text_gradient_toggle.click()
    assert node.config.text_gradient_enabled is True

    # 編集ダイアログ Mock
    with patch("ui.dialogs.GradientEditorDialog") as MockDialog:
        mock_instance = MockDialog.return_value
        # dialog.exec() == True (Accepted)
        mock_instance.exec.return_value = True

        # 期待する戻り値
        new_gradient = [(0.0, "#ff0000"), (1.0, "#0000ff")]
        mock_instance.get_gradient.return_value = new_gradient
        mock_instance.get_angle.return_value = 90

        # "Edit" ボタンクリック
        prop_panel.btn_edit_text_gradient.click()

        # 検証
        assert node.config.text_gradient == new_gradient
        assert node.config.text_gradient_angle == 90
        # ダイアログが正しい引数で呼ばれたか (current values)
        # MockDialog.assert_called_with(..., ..., prop_panel) # 引数の厳密チェックは省略可

    # --- 背景グラデーション ---
    assert hasattr(prop_panel, "btn_bg_gradient_toggle")
    assert hasattr(prop_panel, "btn_edit_bg_gradient")

    prop_panel.btn_bg_gradient_toggle.click()
    assert node.config.background_gradient_enabled is True

    with patch("ui.dialogs.GradientEditorDialog") as MockDialogBg:
        mock_bg = MockDialogBg.return_value
        mock_bg.exec.return_value = True

        bg_gradient = [(0.0, "#000000"), (1.0, "#ffffff")]
        mock_bg.get_gradient.return_value = bg_gradient
        mock_bg.get_angle.return_value = 45

        prop_panel.btn_edit_bg_gradient.click()

        assert node.config.background_gradient == bg_gradient
        assert node.config.background_gradient_angle == 45

    # 背景グラデーション角度スライダーテスト
    if prop_panel.slider_bg_gradient_angle:
        prop_panel.slider_bg_gradient_angle.setValue(180)
        prop_panel.slider_bg_gradient_angle.sliderReleased.emit()
        assert node.config.background_gradient_angle == 180

    # 背景グラデーション透明度スライダーテスト
    if prop_panel.slider_bg_gradient_opacity:
        prop_panel.slider_bg_gradient_opacity.setValue(75)
        prop_panel.slider_bg_gradient_opacity.sliderReleased.emit()
        assert node.config.background_gradient_opacity == 75

    mw.close()
