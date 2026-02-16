from pathlib import Path

from scripts import measure_phase9e


def test_resolve_thresholds_path_prefers_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    config_path = tmp_path / "config" / "perf" / "phase9e_performance_thresholds.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("{}", encoding="utf-8")

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == config_path


def test_resolve_thresholds_path_points_to_config_even_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    expected = tmp_path / "config" / "perf" / "phase9e_performance_thresholds.json"

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == expected


def test_resolve_thresholds_path_honors_env_override(tmp_path: Path, monkeypatch) -> None:
    custom = tmp_path / "custom_thresholds.json"
    custom.write_text("{}", encoding="utf-8")
    monkeypatch.setenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, str(custom))

    resolved = measure_phase9e._resolve_thresholds_path(tmp_path)
    assert resolved == custom
