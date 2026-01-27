import json
import os
import sys
import tempfile

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from managers.config_guardian import ConfigGuardian


@pytest.fixture
def temp_config_env():
    """Create a temporary environment for ConfigGuardian testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_dir = os.path.join(tmpdir, "json")
        os.makedirs(json_dir)
        settings_path = os.path.join(json_dir, "settings.json")

        # Helper to simulate app environment
        yield tmpdir, settings_path


def test_config_corruption_recovery(temp_config_env):
    """
    Chaos Test: Corrupt settings.json and verify ConfigGuardian restores it.
    """
    base_dir, settings_path = temp_config_env

    # 1. Create a corrupted settings.json
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write("{ invalid_json: ... this is garbage data ... ")

    # 2. Initialize Guardian
    guardian = ConfigGuardian(base_dir)

    # 3. Run Validation
    restored = guardian.validate_all()

    # 4. Assertions
    assert restored is True, "Guardian should report restoration."

    # Check if file is valid JSON now
    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "app_settings" in data, "Default settings should be restored."

    # Check if backup exists
    assert os.path.exists(settings_path + ".bak"), "Backup file should be created."


def test_missing_keys_recovery(temp_config_env):
    """
    Chaos Test: Valid JSON but missing required keys.
    """
    base_dir, settings_path = temp_config_env

    # 1. Create incomplete settings.json
    incomplete_data = {"some_other_key": "value"}
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(incomplete_data, f)

    # 2. Guardian Check
    guardian = ConfigGuardian(base_dir)
    restored = guardian.validate_all()

    # 3. Assertions
    assert restored is True
    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "app_settings" in data
    assert os.path.exists(settings_path + ".bak")
