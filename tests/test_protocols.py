import os
import sys

# Ensure path is set for imports
sys.path.append(os.getcwd())

from models.protocols import ImageConfigurable, TextConfigurable, UndoableConfigurable
from windows.base_window import BaseOverlayWindow
from windows.image_window import ImageWindow
from windows.text_window import TextWindow


class TestProtocols:
    """
    Verify that our Window classes strictly adhere to the defined Protocols.
    This ensures that Managers can safely rely on these interfaces.
    """

    def test_text_window_implements_protocol(self):
        """TextWindow must satisfy TextConfigurable."""
        # Static check via isinstance (runtime_checkable)
        # Note: This requires the class to handle the methods.
        # Ideally we instantiate, but for now checking class/mro is verifying inheritance.

        # Check explicit inheritance
        assert issubclass(TextWindow, TextConfigurable)
        assert issubclass(TextWindow, UndoableConfigurable)

        # Check method presence (runtime verification)
        assert hasattr(TextWindow, "set_undoable_property")
        assert hasattr(TextWindow, "update_text")

    def test_image_window_implements_protocol(self):
        """ImageWindow must satisfy ImageConfigurable."""
        assert issubclass(ImageWindow, ImageConfigurable)
        assert issubclass(ImageWindow, UndoableConfigurable)

        assert hasattr(ImageWindow, "set_undoable_property")
        assert hasattr(ImageWindow, "update_image")

    def test_base_window_implements_base_protocol(self):
        """BaseOverlayWindow must satisfy UndoableConfigurable."""
        assert issubclass(BaseOverlayWindow, UndoableConfigurable)
        assert hasattr(BaseOverlayWindow, "set_undoable_property")

    def test_protocol_is_runtime_checkable(self):
        """Ensure protocols are decorated with @runtime_checkable."""

        # Using a dummy class to verify isinstance behavior
        class Dummy:
            def set_undoable_property(self, a, b, c=None):
                pass

        assert isinstance(Dummy(), UndoableConfigurable)
