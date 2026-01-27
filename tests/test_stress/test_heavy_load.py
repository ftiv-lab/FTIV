import time
from unittest.mock import patch

from PySide6.QtCore import QPoint

from ui.main_window import MainWindow


def test_heavy_load_text_windows(qapp):
    """
    Stress check: Create 200 text windows rapidly.
    Verify that the application does not crash and handles the load.
    Mocks 'is_over_limit' to bypass edition restrictions.
    """
    mw = MainWindow()
    mw.show()

    # Target count
    TARGET_COUNT = 200

    try:
        # Mock the limit check to always return False (Under limit)
        with patch("managers.window_manager.is_over_limit", return_value=False):
            start_time = time.time()

            for i in range(TARGET_COUNT):
                # Offset position to avoid exact overlap (though not strictly necessary for crash test)
                pos = QPoint(100 + (i % 20) * 10, 100 + (i // 20) * 10)

                # Directly call WindowManager to skip UI signaling overhead if possible,
                # but calling through MW action or simple add is better integration test.
                # using add_text_window directly.
                mw.window_manager.add_text_window(text=f"Stress Window {i}", pos=pos, suppress_limit_message=True)

                # Optional: Process events every 50 windows to simulate "some" responsiveness
                # or just hammer it to see if it breaks.
                if i % 50 == 0:
                    qapp.processEvents()

            end_time = time.time()
            duration = end_time - start_time
            print(f"\nCreated {TARGET_COUNT} windows in {duration:.4f} seconds.")

            # Assertions
            assert len(mw.window_manager.text_windows) == TARGET_COUNT

            # Verify one random window is valid
            assert mw.window_manager.text_windows[TARGET_COUNT - 1].isVisible()

    finally:
        # Cleanup is critical for stress tests to avoid leaking 1000 widgets
        mw.window_manager.clear_all()
        mw.close()
