import gc
import os
import sys

import pytest
from PySide6.QtWidgets import QApplication, QWidget


def pytest_configure(config):
    """Configure test environment."""
    # Enforce Headless Mode to avoid display driver issues
    os.environ["QPA_PLATFORM"] = "offscreen"
    # Enable FTIV Test Mode (disables animations, etc)
    os.environ["FTIV_TEST_MODE"] = "1"


@pytest.fixture(scope="session")
def qapp():
    """PySide6 QApplication fixture for test session.

    Robust singleton pattern with cleanup.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No explicit quit() here as it might crash if other tests rely on it,
    # but scope="session" keeps it alive until the end.


@pytest.fixture(autouse=True)
def auto_close_widgets(qapp):
    """Automatically close and delete all top-level widgets after each test."""
    yield

    # Garbage collect first to find unreachables
    gc.collect()

    # Close all top-level widgets
    top_widgets = QApplication.topLevelWidgets()
    for w in top_widgets:
        if isinstance(w, QWidget):
            try:
                w.close()
                w.deleteLater()
            except RuntimeError:
                # Already deleted
                pass

    # Process cleanup events
    qapp.processEvents()

    # Force GC again
    gc.collect()


@pytest.fixture(autouse=True)
def force_gc():
    """Force garbage collection after each test."""
    yield
    gc.collect()
