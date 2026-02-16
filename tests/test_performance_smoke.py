import json
from pathlib import Path

from scripts import measure_phase9e


def _latest_report(output_dir: Path) -> tuple[Path, Path]:
    json_reports = sorted(output_dir.glob("phase9e_measurement_*.json"))
    md_reports = sorted(output_dir.glob("phase9e_measurement_*.md"))
    assert json_reports
    assert md_reports
    return json_reports[-1], md_reports[-1]


def test_phase9e_smoke_selected_scenarios_generate_reports(tmp_path: Path) -> None:
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


def test_phase9e_smoke_monitoring_mode_allows_schema_only_validation(tmp_path: Path) -> None:
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
