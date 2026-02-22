import json
from pathlib import Path

from scripts import measure_phase9e


def _latest_report(output_dir: Path) -> tuple[Path, Path]:
    json_reports = sorted(output_dir.glob("phase9e_measurement_*.json"))
    md_reports = sorted(output_dir.glob("phase9e_measurement_*.md"))
    assert json_reports
    assert md_reports
    return json_reports[-1], md_reports[-1]


def _write_thresholds(path: Path, *, median_ms: float, p95_ms: float) -> None:
    payload = {
        "schema_version": 1,
        "baseline_measurement_id": "test-thresholds",
        "scenarios": {
            "P9E-S02": {"median_ms": median_ms, "p95_ms": p95_ms, "samples": 1},
            "P9E-S05": {"median_ms": 9999.0, "p95_ms": 9999.0, "samples": 1},
            "P9E-S06": {"median_ms": 9999.0, "p95_ms": 9999.0, "samples": 1},
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_phase9e_smoke_selected_scenarios_generate_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_ENFORCE, raising=False)
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    output_dir = tmp_path / "perf"

    exit_code = measure_phase9e.main(
        [
            "--base-dir",
            str(Path.cwd()),
            "--output-dir",
            str(output_dir),
            "--warmup",
            "0",
            "--samples",
            "1",
            "--scenario",
            "P9E-S06",
            "--scenario",
            "P9E-S05",
            "--scenario",
            "P9E-S02",
        ]
    )

    assert exit_code == 0
    json_path, md_path = _latest_report(output_dir)
    assert json_path.exists()
    assert md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    meta = payload.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("measurement_id")
    assert meta.get("warmup") == 0
    assert meta.get("samples") == 1
    assert meta.get("scenarios") == ["P9E-S06", "P9E-S05", "P9E-S02"]

    scenarios = payload.get("scenarios")
    assert isinstance(scenarios, list)
    assert [str(entry.get("id")) for entry in scenarios] == ["P9E-S06", "P9E-S05", "P9E-S02"]
    for entry in scenarios:
        assert entry.get("status") == "ok"
        elapsed = entry.get("elapsed_ms")
        assert isinstance(elapsed, dict)
        assert "median" in elapsed
        assert "p95" in elapsed
        assert "max" in elapsed


def test_phase9e_smoke_monitoring_mode_allows_schema_only_validation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(measure_phase9e.ENV_PERF_ENFORCE, raising=False)
    monkeypatch.delenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, raising=False)
    output_dir = tmp_path / "perf"

    exit_code = measure_phase9e.main(
        [
            "--base-dir",
            str(Path.cwd()),
            "--output-dir",
            str(output_dir),
            "--warmup",
            "0",
            "--samples",
            "1",
            "--scenario",
            "P9E-S01",
        ]
    )

    # Monitoring mode:
    # validates execution + output contract only, without hard performance thresholds.
    assert exit_code == 0
    json_path, _ = _latest_report(output_dir)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    assert isinstance(scenarios, list)
    assert len(scenarios) == 1
    assert scenarios[0].get("id") == "P9E-S01"
    assert scenarios[0].get("status") == "ok"


def test_phase9e_smoke_threshold_mode_passes_with_valid_limits(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "perf"
    threshold_path = tmp_path / "thresholds.json"
    _write_thresholds(threshold_path, median_ms=9999.0, p95_ms=9999.0)

    monkeypatch.setenv(measure_phase9e.ENV_PERF_ENFORCE, "1")
    monkeypatch.setenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, str(threshold_path))

    exit_code = measure_phase9e.main(
        [
            "--base-dir",
            str(Path.cwd()),
            "--output-dir",
            str(output_dir),
            "--warmup",
            "0",
            "--samples",
            "1",
            "--scenario",
            "P9E-S06",
            "--scenario",
            "P9E-S05",
            "--scenario",
            "P9E-S02",
        ]
    )

    assert exit_code == 0


def test_phase9e_smoke_threshold_mode_fails_when_exceeds(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "perf"
    threshold_path = tmp_path / "thresholds.json"
    _write_thresholds(threshold_path, median_ms=0.0001, p95_ms=0.0001)

    monkeypatch.setenv(measure_phase9e.ENV_PERF_ENFORCE, "1")
    monkeypatch.setenv(measure_phase9e.ENV_PERF_THRESHOLDS_PATH, str(threshold_path))

    exit_code = measure_phase9e.main(
        [
            "--base-dir",
            str(Path.cwd()),
            "--output-dir",
            str(output_dir),
            "--warmup",
            "0",
            "--samples",
            "1",
            "--scenario",
            "P9E-S02",
        ]
    )

    assert exit_code == 3
