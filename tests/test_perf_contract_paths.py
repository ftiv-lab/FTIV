from pathlib import Path

from scripts import measure_phase9e


def test_resolve_thresholds_path_prefers_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    config_path = tmp_path / "config" / "perf" / "phase9e_performance_thresholds.json"
    legacy_path = tmp_path / "docs" / "internal" / "architecture" / "phase9e_performance_thresholds.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("{}", encoding="utf-8")
    legacy_path.write_text("{}", encoding="utf-8")

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == config_path


def test_resolve_thresholds_path_uses_legacy_when_config_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    legacy_path = tmp_path / "docs" / "internal" / "architecture" / "phase9e_performance_thresholds.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text("{}", encoding="utf-8")

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == legacy_path


def test_resolve_thresholds_path_honors_env_override(tmp_path: Path, monkeypatch) -> None:
    custom = tmp_path / "custom_thresholds.json"
    custom.write_text("{}", encoding="utf-8")
    monkeypatch.setenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, str(custom))

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == custom
