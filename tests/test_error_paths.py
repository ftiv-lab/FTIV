# -*- coding: utf-8 -*-
"""Error path tests to verify resilience and error handling.

This module focuses on testing error conditions, invalid inputs, and
recovery scenarios. Moving beyond happy-path testing.
"""

from pathlib import Path
from typing import Any

from managers.config_guardian import ConfigGuardian


class TestConfigGuardianErrorPaths:
    """Test error handling in ConfigGuardian."""

    def test_nonexistent_base_directory(self) -> None:
        """Test behavior with nonexistent base directory."""
        guardian = ConfigGuardian("/nonexistent/path/that/does/not/exist")
        # Should not raise - creates directory
        _ = guardian.validate_all()
        # Clean up is not needed as validate_all creates in nonexistent path

    def test_corrupted_json_recovery(self, tmp_path: Path) -> None:
        """Test recovery from corrupted JSON file."""
        # Setup
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        settings_file = json_dir / "settings.json"
        settings_file.write_text("{ invalid json syntax", encoding="utf-8")

        guardian = ConfigGuardian(str(tmp_path))
        result = guardian.validate_all()

        # Should report corruption and restore
        assert result is True
        assert any("corrupted" in r.lower() for r in guardian.reports)

    def test_missing_required_keys_recovery(self, tmp_path: Path) -> None:
        """Test recovery when required keys are missing."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        settings_file = json_dir / "settings.json"
        settings_file.write_text('{"unrelated_key": "value"}', encoding="utf-8")

        guardian = ConfigGuardian(str(tmp_path))
        result = guardian.validate_all()

        # Should detect missing keys and restore
        assert result is True
        assert any("missing" in r.lower() for r in guardian.reports)

    def test_valid_settings_passes(self, tmp_path: Path) -> None:
        """Test that valid settings pass without modification."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        settings_file = json_dir / "settings.json"
        valid_settings = '{"app_settings": {}, "overlay_settings": {}}'
        settings_file.write_text(valid_settings, encoding="utf-8")

        guardian = ConfigGuardian(str(tmp_path))
        result = guardian.validate_all()

        # Should pass without needing restoration
        assert result is False

    def test_backup_created_on_corruption(self, tmp_path: Path) -> None:
        """Test that backup file is created when restoring."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        settings_file = json_dir / "settings.json"
        settings_file.write_text("corrupted content", encoding="utf-8")

        guardian = ConfigGuardian(str(tmp_path))
        guardian.validate_all()

        # Verify backup was created
        backup_file = json_dir / "settings.json.bak"
        assert backup_file.exists()

    def test_json_dir_creation(self, tmp_path: Path) -> None:
        """Test that json directory is created if missing (lines 30-31)."""
        # tmp_path exists but has no json subdirectory
        guardian = ConfigGuardian(str(tmp_path))
        guardian.validate_all()

        # Verify json directory was created
        json_dir = tmp_path / "json"
        assert json_dir.exists()
        assert any("created missing json directory" in r.lower() for r in guardian.reports)

    def test_settings_not_found_creates_default(self, tmp_path: Path) -> None:
        """Test that missing settings.json creates default (lines 44-46)."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        # No settings.json file

        guardian = ConfigGuardian(str(tmp_path))
        result = guardian.validate_all()

        # Should create default and NOT report restoration needed
        assert result is False
        settings_file = json_dir / "settings.json"
        assert settings_file.exists()
        assert any("not found" in r.lower() for r in guardian.reports)

    def test_unexpected_read_exception(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test handling of unexpected exceptions (lines 65-67)."""
        import json as json_module

        json_dir = tmp_path / "json"
        json_dir.mkdir()
        settings_file = json_dir / "settings.json"
        settings_file.write_text('{"app_settings": {}, "overlay_settings": {}}', encoding="utf-8")

        # Make json.load raise an unexpected exception
        def mock_load(*args: Any, **kwargs: Any) -> None:
            raise OSError("Simulated I/O error")

        monkeypatch.setattr(json_module, "load", mock_load)

        guardian = ConfigGuardian(str(tmp_path))
        result = guardian.validate_all()

        # Should catch unexpected error and return False
        assert result is False
        assert any("unexpected error" in r.lower() for r in guardian.reports)

    def test_get_report_text(self, tmp_path: Path) -> None:
        """Test get_report_text formatting (line 93)."""
        guardian = ConfigGuardian(str(tmp_path))
        guardian.validate_all()

        report_text = guardian.get_report_text()
        assert isinstance(report_text, str)
        # Should have at least one report entry
        assert len(report_text) > 0


class TestSpacingSettingsErrorPaths:
    """Test error handling in SpacingSettings model."""

    def test_negative_spacing_values(self) -> None:
        """Test behavior with negative spacing values."""
        from models.spacing_settings import HorizontalSpacing

        # Should accept negatives (current behavior)
        settings = HorizontalSpacing(
            char_spacing=-10.0,
            line_spacing=-5.0,
        )
        assert settings.char_spacing == -10.0

    def test_extreme_spacing_values(self) -> None:
        """Test behavior with extreme spacing values."""
        from models.spacing_settings import HorizontalSpacing

        settings = HorizontalSpacing(
            char_spacing=9999.0,
            line_spacing=9999.0,
        )
        assert settings.char_spacing == 9999.0


class TestWindowConfigErrorPaths:
    """Test error handling in WindowConfig models."""

    def test_empty_position_dict(self) -> None:
        """Test behavior with empty position dictionary."""
        from models.window_config import WindowConfigBase

        config = WindowConfigBase(position={})
        assert config.position == {}

    def test_invalid_position_keys(self) -> None:
        """Test behavior with invalid position keys."""
        from models.window_config import WindowConfigBase

        config = WindowConfigBase(position={"invalid": 100})
        assert "invalid" in config.position

    def test_none_values_in_optional_fields(self) -> None:
        """Test that None is properly handled in optional fields."""
        from models.window_config import TextWindowConfig

        config = TextWindowConfig()
        # Verify defaults are applied for optional fields
        assert config.font is not None
        assert config.font_size > 0


class TestFileManagerErrorPaths:
    """Test error handling in FileManager edge cases."""

    def test_save_to_readonly_directory(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test handling of permission errors during save."""
        # This test documents expected behavior for permission issues
        # Actual implementation may vary
        pass  # Placeholder for permission-based tests

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a file that doesn't exist."""
        # This would require mocking MainWindow
        pass  # Placeholder - requires integration setup
