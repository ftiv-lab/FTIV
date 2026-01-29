import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from managers.file_manager import FileManager


@pytest.fixture
def file_manager():
    # Instantiate with Mock MW
    return FileManager(MagicMock())


def test_write_failure_preserves_original(file_manager):
    """
    Chaos Test: Failure DURING writing (json.dump) should leave the original file untouched.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "target.json")

        # 1. Create original file
        original_data = {"key": "original"}
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(original_data, f)

        # 2. Attempt save with "crash" during write
        new_data = {"key": "NEW_DATA"}

        # Mock json.dump to raise exception
        with patch("json.dump", side_effect=RuntimeError("Simulated Write Crash")):
            with pytest.raises(RuntimeError):
                file_manager._save_json_atomic(target_path, new_data)

        # 3. Verify Original Preserved
        with open(target_path, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        assert current_data == original_data

        # 4. Verify Cleanup
        assert not os.path.exists(target_path + ".tmp")


def test_replace_failure_preserves_original(file_manager):
    """
    Chaos Test: Failure DURING replacement (os.replace) should leave the original file untouched.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "target.json")

        # 1. Create original
        original_data = {"key": "original"}
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(original_data, f)

        # 2. Attempt save with "crash" during replace
        new_data = {"key": "NEW_DATA"}

        with patch("os.replace", side_effect=OSError("Simulated Disk Error")):
            with pytest.raises(OSError):
                file_manager._save_json_atomic(target_path, new_data)

        # 3. Verify Original Preserved
        with open(target_path, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        assert current_data == original_data

        # 4. Verify Tmp file still exists (because replace failed, but write succeeded)
        # Wait, the code says:
        # except Exception as e:
        #     if os.path.exists(temp_path): remove...
        # So even if replace fails, it cleans up the temp file!
        # Let's verify that cleanup happens.
        assert not os.path.exists(target_path + ".tmp")
