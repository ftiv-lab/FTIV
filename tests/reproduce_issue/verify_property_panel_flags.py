import os
import sys

# FTIVルートディレクトリをパスに追加
sys.path.append(os.getcwd())

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.property_panel import PropertyPanel


def verify_property_panel_flags():
    _app = QApplication(sys.argv)

    # Instantiate as done in main_window.py
    panel = PropertyPanel(parent=None)

    flags = panel.windowFlags()

    print(f"Flags: {flags}")

    # Check parent
    if panel.parent() is not None:
        print("FAIL: Parent should be None")
        sys.exit(1)

    # Check Qt.Window bit (0x00000001)
    if not (flags & Qt.Window):
        print("FAIL: Qt.Window flag missing")
        sys.exit(1)

    # Check Qt.WindowStaysOnTopHint (0x00040000)
    if not (flags & Qt.WindowStaysOnTopHint):
        print("FAIL: Qt.WindowStaysOnTopHint flag missing")
        sys.exit(1)

    print("SUCCESS: PropertyPanel flags verified.")
    sys.exit(0)


if __name__ == "__main__":
    verify_property_panel_flags()
