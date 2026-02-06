import os
import sys

# PySide6 paths setup if needed
sys.path.append(os.getcwd())

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QMainWindow

from models.constants import AppDefaults  # noqa: F401
from models.window_config import TextWindowConfig  # noqa: F401
from windows.connector import ConnectorLabel, ConnectorLine  # noqa: F401


def main():
    _ = QApplication(sys.argv)
    mw = QMainWindow()

    # Mock settings
    class Settings:
        glyph_cache_size = 512
        render_debounce_ms = 50
        wheel_debounce_ms = 80

    mw.app_settings = Settings()

    # Create simple start/end windows (mocks)
    class MockWindow:
        def geometry(self):
            from PySide6.QtCore import QRect

            return QRect(0, 0, 100, 100)

        def isVisible(self):
            return True

        def pos(self):
            from PySide6.QtCore import QPoint

            return QPoint(0, 0)

    start_w = MockWindow()
    end_w = MockWindow()

    # Move end window to avoid 0 delta
    def pos_end():
        from PySide6.QtCore import QPoint

        return QPoint(200, 200)

    end_w.pos = pos_end

    def geometry_end():
        from PySide6.QtCore import QRect

        return QRect(200, 200, 100, 100)

    end_w.geometry = geometry_end

    line = ConnectorLine(start_w, end_w, parent=mw, color=QColor("red"))
    label = line.label_window

    print(f"Initial Label Text: '{label.text}'")
    print(f"Initial Visibility: {label.isVisible()}")
    print(f"Config Text Visible: {label.config.text_visible}")

    # Set text
    label.text = "Hello World"
    print(f"Set Text: '{label.text}'")

    import traceback

    try:
        print("Attempting explicit render...")
        pix = label.renderer.render(label)
        label.setPixmap(pix)
        print("Render successful.")
    except Exception:
        print("Render FAILED:")
        traceback.print_exc()
        pix = None
    if pix:
        print(f"Pixmap Size: {pix.width()}x{pix.height()}")
        print(f"Pixmap isNull: {pix.isNull()}")
    else:
        print("Pixmap is None!")

    line.update_position()
    print(f"Visibility after update: {label.isVisible()}")

    # Check if text_visible property works
    label.text_visible = False
    print(f"Set text_visible=False. Config: {label.config.text_visible}")
    label._update_text_immediate()
    # verify if it still renders (since we suspect check is missing)

    label.text_visible = True
    label._update_text_immediate()
    pix2 = label.pixmap()
    if pix2:
        print(f"Pixmap Size (visible=True): {pix2.width()}x{pix2.height()}")

    # Check spacing properties
    print(f"Initial char_spacing_h: {label.char_spacing_h}")
    label.char_spacing_h = 0.5
    print(f"Set char_spacing_h=0.5. Config: {label.config.char_spacing_h}")

    try:
        pix3 = label.renderer.render(label)
        label.setPixmap(pix3)
        if pix3:
            print(f"Pixmap Size (wide spacing): {pix3.width()}x{pix3.height()}")
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
