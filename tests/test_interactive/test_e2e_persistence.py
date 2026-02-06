import os
import shutil
import subprocess
import sys
import tempfile

import pytest


class TestE2EPersistence:
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temp dir for config and cleanup after."""
        d = tempfile.mkdtemp(prefix="ftiv_e2e_")
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_gradient_persistence(self, temp_config_dir):
        """
        Verify that Gradient settings obey the persistence cycle:
        Write (Process A) -> Save -> Read (Process B) -> Verify
        """
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/simulate_session.py"))

        # 1. WRITE Session
        cmd_write = [sys.executable, script_path, "--config-dir", temp_config_dir, "--mode", "write"]

        # Run process. Capture output for debugging.
        result_write = subprocess.run(cmd_write, capture_output=True, text=True, encoding="utf-8")
        print("--- WRITE STDOUT ---\n", result_write.stdout)
        print("--- WRITE STDERR ---\n", result_write.stderr)

        if result_write.returncode != 0:
            pytest.fail(f"Write process failed with code {result_write.returncode}")

        # Check if files were created
        # We saved scenes_db, so we check for that
        assert os.path.exists(os.path.join(temp_config_dir, "scenes_db.json"))
        # scenes_db might be created depending on logic

        # 2. READ Session
        cmd_read = [sys.executable, script_path, "--config-dir", temp_config_dir, "--mode", "read"]

        result_read = subprocess.run(cmd_read, capture_output=True, text=True, encoding="utf-8")
        print("--- READ STDOUT ---\n", result_read.stdout)
        print("--- READ STDERR ---\n", result_read.stderr)

        if result_read.returncode != 0:
            pytest.fail(f"Read process failed with code {result_read.returncode}")

        # Verify Output
        assert "VERIFY_SUCCESS" in result_read.stdout
