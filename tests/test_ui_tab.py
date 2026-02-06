import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from ui.tabs.general_tab import GeneralTab


# Mock MainWindow and its attributes
class MockMainWindow(MagicMock):
    def __init__(self):
        super().__init__()
        self.base_directory = "."
        self.windowFlags = lambda: 0
        self.is_property_panel_active = False

        # Managers
        self.settings_manager = MagicMock()
        self.settings_manager.set_main_frontmost = MagicMock()

        self.main_controller = MagicMock()
        self.main_controller.bulk_manager = MagicMock()

        self.overlay_settings = MagicMock()
        self.overlay_settings.selection_frame_enabled = True
        self.overlay_settings.selection_frame_color = "#FFFF00FF"
        self.overlay_settings.selection_frame_width = 4

        self.file_manager = MagicMock()

        # Methods
        self.change_language = MagicMock()
        self.toggle_property_panel = MagicMock()
        self.apply_overlay_settings_to_all_windows = MagicMock()


def test_general_tab_instantiation():
    _app = QApplication.instance() or QApplication(sys.argv)

    mw = MockMainWindow()
    try:
        tab = GeneralTab(mw)
        tab.show()
        print("GeneralTab instantiated successfully.")

        # Verify specific widgets exist
        assert hasattr(tab, "danger_group")
        assert hasattr(tab, "btn_factory_reset")

        # Verify text setup
        assert tab.btn_factory_reset.text() != ""

    except Exception as e:
        print(f"Failed to instantiate GeneralTab: {e}")
        raise


if __name__ == "__main__":
    test_general_tab_instantiation()
