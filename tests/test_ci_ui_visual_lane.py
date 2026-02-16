import json
from pathlib import Path

from scripts import ci_ui_visual_lane


def _write_profile_and_thresholds(base_dir: Path, *, required_cases: list[str]) -> Path:
    profile_path = base_dir / "config" / "ui" / "phase10b_visual_profiles.json"
    threshold_path = base_dir / "config" / "ui" / "phase10c_visual_thresholds.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    profiles = {
        "schema_version": 1,
        "cases": {case_id: {"window_size": [320, 180]} for case_id in required_cases},
    }
    thresholds = {
        "schema_version": 1,
        "mode": "monitor",
        "max_failures_allowed": 0,
        "required_cases": required_cases,
    }
    profile_path.write_text(json.dumps(profiles), encoding="utf-8")
    threshold_path.write_text(json.dumps(thresholds), encoding="utf-8")
    return threshold_path


def test_parse_cases_rejects_empty() -> None:
    try:
        _ = ci_ui_visual_lane._parse_cases(" , ")
    except ValueError as exc:
        assert "at least one case ID" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_parse_cases_accepts_csv() -> None:
    values = ci_ui_visual_lane._parse_cases("a, b, c")
    assert values == ["a", "b", "c"]


def test_run_lane_monitor_writes_report(monkeypatch, tmp_path: Path) -> None:
    case_id = "task_title_divider_horizontal"
    threshold_path = _write_profile_and_thresholds(tmp_path, required_cases=[case_id])

    monkeypatch.setattr(ci_ui_visual_lane, "_run_pytest", lambda **_kwargs: 0)
    monkeypatch.setattr(
        ci_ui_visual_lane,
        "_collect_test_results",
        lambda _path: {
            ci_ui_visual_lane.CASE_TO_TEST_NAME[case_id]: {"status": "passed", "message": ""},
        },
    )

    rc = ci_ui_visual_lane.run_lane(
        mode="monitor",
        base_dir=tmp_path,
        output_dir=tmp_path / "runs",
        raw_cases=None,
        thresholds_path=threshold_path,
    )
    assert rc == 0
    reports = list((tmp_path / "runs").glob("phase10c_ui_visual_run_*.json"))
    assert reports
    payload = json.loads(reports[-1].read_text(encoding="utf-8"))
    assert payload["summary"]["lane_status"] == "passed"


def test_run_lane_enforce_fails_when_threshold_violated(monkeypatch, tmp_path: Path) -> None:
    case_id = "task_title_divider_horizontal"
    threshold_path = _write_profile_and_thresholds(tmp_path, required_cases=[case_id])

    monkeypatch.setattr(ci_ui_visual_lane, "_run_pytest", lambda **_kwargs: 0)
    monkeypatch.setattr(
        ci_ui_visual_lane,
        "_collect_test_results",
        lambda _path: {
            ci_ui_visual_lane.CASE_TO_TEST_NAME[case_id]: {"status": "failed", "message": "boom"},
        },
    )

    rc = ci_ui_visual_lane.run_lane(
        mode="enforce",
        base_dir=tmp_path,
        output_dir=tmp_path / "runs",
        raw_cases=None,
        thresholds_path=threshold_path,
    )
    assert rc == 1


def test_run_lane_enforce_fails_when_required_case_not_selected(monkeypatch, tmp_path: Path) -> None:
    required_cases = ["task_title_divider_horizontal", "task_title_divider_vertical"]
    threshold_path = _write_profile_and_thresholds(tmp_path, required_cases=required_cases)

    monkeypatch.setattr(ci_ui_visual_lane, "_run_pytest", lambda **_kwargs: 0)
    monkeypatch.setattr(
        ci_ui_visual_lane,
        "_collect_test_results",
        lambda _path: {
            ci_ui_visual_lane.CASE_TO_TEST_NAME["task_title_divider_horizontal"]: {
                "status": "passed",
                "message": "",
            }
        },
    )

    rc = ci_ui_visual_lane.run_lane(
        mode="enforce",
        base_dir=tmp_path,
        output_dir=tmp_path / "runs",
        raw_cases="task_title_divider_horizontal",
        thresholds_path=threshold_path,
    )
    assert rc == 1
