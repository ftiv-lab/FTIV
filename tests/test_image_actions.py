from unittest.mock import MagicMock

import pytest

from ui.controllers.image_actions import ImageActions


class TestImageActions:
    @pytest.fixture
    def image_actions(self):
        self.mw = MagicMock()
        self.mw.window_manager = MagicMock()
        self.mw.image_windows = []  # fallback if needed
        return ImageActions(self.mw)

    def test_set_all_image_opacity_realtime(self, image_actions):
        # Setup mock images
        img1 = MagicMock()
        img2 = MagicMock()

        image_actions.mw.window_manager.image_windows = [img1, img2]

        # Action: Set opacity to 50%
        image_actions.set_all_image_opacity_realtime(50)

        # Verify
        # Expected: set_opacity(0.5) or opacity = 0.5

        if hasattr(img1, "set_opacity"):
            img1.set_opacity.assert_called_with(0.5)
        else:
            # Check attribute set logic if we mocked properties (complex in MagicMock)
            pass

        # MagicMock by default creates method for any call.
        # But if the code checks hasattr(w, "set_opacity"), MagicMock returns True.
        # So it should call set_opacity.

        img1.set_opacity.assert_called_with(0.5)
        img2.set_opacity.assert_called_with(0.5)

    def test_set_all_image_size_realtime(self, image_actions):
        # Setup mock images
        img1 = MagicMock()
        # Mocking property 'scale_factor' on MagicMock is tricky for assignment check unless using Configure
        # But code is: w.scale_factor = scale
        # We can check if assignment happened

        image_actions.mw.window_manager.image_windows = [img1]

        # Action: Set size to 150%
        image_actions.set_all_image_size_realtime(150)

        # Verify
        # MagicMock records property assignment as set attribute if not configured otherwise?
        # Actually it's simpler to check if update_image was called, which implies the block ran.

        img1.update_image.assert_called()

        # To strictly check property assignment on MagicMock:
        # assert img1.scale_factor == 1.5
        # (This works if simple assignment)

        assert img1.scale_factor == 1.5

    def test_set_all_image_rotation_realtime(self, image_actions):
        img1 = MagicMock()
        image_actions.mw.window_manager.image_windows = [img1]

        image_actions.set_all_image_rotation_realtime(90)

        img1.set_rotation_angle.assert_called_with(90.0)
