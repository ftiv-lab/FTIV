import os
import shutil
import tempfile

import pytest

from utils.reset_manager import ResetManager


class TestResetManager:
    @pytest.fixture
    def mock_env(self):
        """Create a mock environment with dummy config files."""
        base_dir = tempfile.mkdtemp(prefix="ftiv_reset_test_")

        # Create structure
        json_dir = os.path.join(base_dir, "json")
        settings_dir = os.path.join(base_dir, "user_data", "settings")
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(settings_dir, exist_ok=True)

        # Create dummy files
        files = {
            os.path.join(json_dir, "app_settings.json"): '{"dummy": 1}',
            os.path.join(json_dir, "scenes_db.json"): '{"scenes": []}',
            os.path.join(json_dir, "text_archetype.json"): '{"font": "Arial"}',
            os.path.join(settings_dir, "text_archetype.json"): '{"font": "Arial"}',
        }

        for path, content in files.items():
            with open(path, "w") as f:
                f.write(content)

        yield base_dir, files.keys()

        # Cleanup
        shutil.rmtree(base_dir, ignore_errors=True)

    @pytest.mark.parametrize(
        "reset_settings, reset_user_data, expected_deleted, expected_kept",
        [
            # Case 1: Reset Settings Only
            (
                True,
                False,
                ["app_settings.json", "overlay_settings.json", "text_archetype.json"],
                ["scenes_db.json", "presets/custom_preset.json"],
            ),
            # Case 2: Reset User Data Only
            (
                False,
                True,
                ["scenes_db.json", "presets/custom_preset.json"],
                ["app_settings.json"],
            ),
            # Case 3: Reset Both
            (
                True,
                True,
                [
                    "app_settings.json",
                    "scenes_db.json",
                    "presets/custom_preset.json",
                    "text_archetype.json",
                ],
                [],
            ),
            # Case 4: Reset None
            (False, False, [], ["app_settings.json", "scenes_db.json"]),
        ],
    )
    def test_factory_reset_granular(self, mock_env, reset_settings, reset_user_data, expected_deleted, expected_kept):
        base_dir, _ = mock_env
        manager = ResetManager(base_dir=base_dir)

        # Create specific dummy files for this test structure
        json_dir = os.path.join(base_dir, "json")
        presets_dir = os.path.join(json_dir, "presets")
        os.makedirs(presets_dir, exist_ok=True)

        # Ensure preset file exists (mock_env might not create it by default)
        with open(os.path.join(presets_dir, "custom_preset.json"), "w") as f:
            f.write("{}")

        # Perform Reset
        manager.perform_factory_reset(reset_settings=reset_settings, reset_user_data=reset_user_data)

        # Verify Deleted
        for filename in expected_deleted:
            # Re-eval strategy: Helper to resolve path
            full_path = self._resolve_path(base_dir, filename)
            assert not os.path.exists(full_path), f"File should be deleted: {filename}"

        # Verify Kept
        for filename in expected_kept:
            full_path = self._resolve_path(base_dir, filename)
            assert os.path.exists(full_path), f"File should stay: {filename}"

    def _resolve_path(self, base_dir, filename):
        if filename.startswith("presets/"):
            return os.path.join(base_dir, "json", filename.replace("/", os.sep))
        elif filename == "app_settings.json":
            return os.path.join(base_dir, "json", filename)
        elif filename == "scenes_db.json":
            return os.path.join(base_dir, "json", filename)
        elif filename == "text_archetype.json":
            # For this test we assume the one in json dir
            return os.path.join(base_dir, "json", filename)
        elif filename == "overlay_settings.json":
            return os.path.join(base_dir, "json", filename)
        return os.path.join(base_dir, "json", filename)
