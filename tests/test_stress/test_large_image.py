import os
import tempfile
import time

from PIL import Image
from PySide6.QtCore import QPoint

from ui.main_window import MainWindow


def test_large_image_load(qapp):
    """
    Stress check: Load a massive image (8K+ resolution).
    Verify that the application handles the memory allocation gracefully.
    """
    mw = MainWindow()
    mw.show()

    # Create a large image (e.g., 8192x8192 = 64MP -> ~200MB in memory raw)
    # Using a solid color for speed of creation
    WIDTH, HEIGHT = 8192, 8192

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        print(f"\nGeneratng large image ({WIDTH}x{HEIGHT})...")
        t0 = time.time()
        # Create image
        img = Image.new("RGB", (WIDTH, HEIGHT), color="red")
        img.save(tmp_path)
        print(f"Image generated in {time.time() - t0:.2f}s")

        # Test Loading
        t1 = time.time()

        # We assume add_image_window handles the logic
        # Ideally, we should mock any user interaction if it pops up, but add_image_window direct call shouldn't.
        # However, ImageWindow might resize it or process it.
        mw.window_manager.add_image_window(image_path=tmp_path, pos=QPoint(100, 100))

        load_time = time.time() - t1
        print(f"Image loaded into Window in {load_time:.2f}s")

        # Verification
        assert len(mw.window_manager.image_windows) == 1
        img_win = mw.window_manager.image_windows[0]
        assert img_win.isVisible()

        # Check if internal pixmap has correct size (or resized if we have logic for that, but currently should be full)
        # Note: Qt might load it lazily or optimized.
        # But we ensure creation succeeded.

    finally:
        # Cleanup
        mw.window_manager.clear_all()
        mw.close()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
