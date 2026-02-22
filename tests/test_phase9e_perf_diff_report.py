import json
from pathlib import Path

from scripts import phase9e_perf_diff_report


def _write_measurement(path: Path, measurement_id: str, median: float, p95: float) -> None:
    payload = {
        "meta": {
            "measurement_id": measurement_id,
            "timestamp": "2026-02-16T00:00:00",
            "git_commit": "deadbee",
            "python": "3.13.11",
            "os": "Windows-10",
            "window_size": [433, 640],
            "warmup": 1,
            "samples": 5,
            "scenarios": ["P9E-S06"],
        },
        "scenarios": [
            {
                "id": "P9E-S06",
                "name": "InfoTab filter switch sequence",
                "status": "ok",
                "warmup": 1,
                "samples": 5,
                "elapsed_ms": {"median": median, "p95": p95, "max": median, "min": median},
                "counters": {"filter_apply_count": 3},
                "error": "",
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_diff_report_with_explicit_reports(tmp_path: Path) -> None:
    base_json = tmp_path / "phase9e_measurement_20260216_210000.json"
    target_json = tmp_path / "phase9e_measurement_20260216_220000.json"
    out_md = tmp_path / "diff.md"
    _write_measurement(base_json, "phase9e_measurement_20260216_210000", median=10.0, p95=11.0)
    _write_measurement(target_json, "phase9e_measurement_20260216_220000", median=8.0, p95=9.0)

    rc = phase9e_perf_diff_report.main(
        [
            "--base-report",
            str(base_json),
            "--target-report",
            str(target_json),
            "--output-file",
            str(out_md),
        ]
    )
    assert rc == 0
    assert out_md.exists()
    text = out_md.read_text(encoding="utf-8")
    assert "P9E-S06" in text
    assert "Top Improvements" in text


def test_diff_report_uses_latest_two_when_reports_not_specified(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _write_measurement(runs_dir / "phase9e_measurement_20260216_210000.json", "m1", median=10.0, p95=11.0)
    _write_measurement(runs_dir / "phase9e_measurement_20260216_220000.json", "m2", median=12.0, p95=13.0)

    rc = phase9e_perf_diff_report.main(["--runs-dir", str(runs_dir)])
    assert rc == 0
    outputs = list(runs_dir.glob("phase9e_diff_*.md"))
    assert outputs


def test_diff_report_fails_when_not_enough_reports(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _write_measurement(runs_dir / "phase9e_measurement_20260216_210000.json", "m1", median=10.0, p95=11.0)

    rc = phase9e_perf_diff_report.main(["--runs-dir", str(runs_dir)])
    assert rc == 2
