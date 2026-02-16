import json
from pathlib import Path

from scripts import ui_visual_diff_report


def _write_visual_run(path: Path, measurement_id: str, case_status: str, message: str = "") -> None:
    payload = {
        "meta": {
            "measurement_id": measurement_id,
            "mode": "monitor",
            "timestamp": "2026-02-17T00:00:00",
        },
        "summary": {
            "total_cases": 1,
            "failing_cases": 0 if case_status == "passed" else 1,
            "threshold_violations": [],
            "lane_status": "passed" if case_status == "passed" else "failed",
        },
        "cases": [
            {
                "id": "task_title_divider_horizontal",
                "test_name": "test_visual_contract_task_title_divider_horizontal",
                "status": case_status,
                "message": message,
                "profile": {"window_size": [320, 180]},
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_ui_visual_diff_report_with_explicit_inputs(tmp_path: Path) -> None:
    base = tmp_path / "phase10c_ui_visual_run_20260217_010000.json"
    target = tmp_path / "phase10c_ui_visual_run_20260217_020000.json"
    output = tmp_path / "diff.md"
    _write_visual_run(base, "phase10c_ui_visual_run_20260217_010000", "passed")
    _write_visual_run(target, "phase10c_ui_visual_run_20260217_020000", "failed", "regressed")

    rc = ui_visual_diff_report.main(
        [
            "--base-report",
            str(base),
            "--target-report",
            str(target),
            "--output-file",
            str(output),
        ]
    )
    assert rc == 0
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "task_title_divider_horizontal" in text
    assert "Regressions" in text


def test_ui_visual_diff_report_uses_latest_two_when_unspecified(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _write_visual_run(runs_dir / "phase10c_ui_visual_run_20260217_010000.json", "r1", "passed")
    _write_visual_run(runs_dir / "phase10c_ui_visual_run_20260217_020000.json", "r2", "passed")

    rc = ui_visual_diff_report.main(["--runs-dir", str(runs_dir)])
    assert rc == 0
    outputs = list(runs_dir.glob("phase10c_ui_visual_diff_*.md"))
    assert outputs


def test_ui_visual_diff_report_fails_when_not_enough_reports(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _write_visual_run(runs_dir / "phase10c_ui_visual_run_20260217_010000.json", "r1", "passed")
    rc = ui_visual_diff_report.main(["--runs-dir", str(runs_dir)])
    assert rc == 2
