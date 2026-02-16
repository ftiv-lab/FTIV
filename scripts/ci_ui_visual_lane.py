#!/usr/bin/env python
"""CI entrypoint for Phase 10C UI visual regression lanes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DEFAULT_THRESHOLDS_RELATIVE_PATH = Path("config/ui/phase10c_visual_thresholds.json")
DEFAULT_PROFILES_RELATIVE_PATH = Path("config/ui/phase10b_visual_profiles.json")
DEFAULT_RUNS_DIR = Path("docs/internal/architecture/ui_visual_runs")
ENV_UI_VISUAL_THRESHOLDS_PATH = "FTIV_UI_VISUAL_THRESHOLDS_PATH"

CASE_TO_TEST_NAME: dict[str, str] = {
    "task_title_divider_horizontal": "test_visual_contract_task_title_divider_horizontal",
    "task_title_divider_vertical": "test_visual_contract_task_title_divider_vertical_hidden",
    "due_state_today": "test_visual_contract_due_state_today_line",
    "due_state_overdue": "test_visual_contract_due_state_overdue_line",
    "due_state_none": "test_visual_contract_due_state_none_has_no_due_badge",
    "property_panel_summary_short": "test_visual_contract_property_panel_summary_short",
    "property_panel_summary_long": "test_visual_contract_property_panel_summary_long_elides",
    "dialog_only_routes_textwindow": "test_visual_contract_dialog_only_textwindow_context_menu",
    "density_about_compact": "test_visual_contract_about_compact_hides_hints",
    "density_about_comfortable": "test_visual_contract_about_comfortable_restores_hints",
}

CASE_TO_NODEID: dict[str, str] = {
    case_id: f"tests/test_visual_regression_contract.py::{test_name}"
    for case_id, test_name in CASE_TO_TEST_NAME.items()
}


def _parse_cases(raw: str) -> list[str]:
    values = [token.strip() for token in str(raw).split(",") if token.strip()]
    if not values:
        raise ValueError("at least one case ID is required")
    return values


def _resolve_thresholds_path(base_dir: Path, cli_path: Path | None) -> Path:
    if cli_path is not None:
        return cli_path.resolve()
    env_override = os.getenv(ENV_UI_VISUAL_THRESHOLDS_PATH, "").strip()
    if env_override:
        return Path(env_override).resolve()
    return (base_dir / DEFAULT_THRESHOLDS_RELATIVE_PATH).resolve()


def _load_thresholds(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "mode", "max_failures_allowed", "required_cases"}
    missing = sorted(required.difference(payload.keys()))
    if missing:
        raise ValueError(f"threshold contract missing keys: {missing}")
    if not isinstance(payload["required_cases"], list) or not payload["required_cases"]:
        raise ValueError("required_cases must be a non-empty list")
    if not isinstance(payload["max_failures_allowed"], int) or payload["max_failures_allowed"] < 0:
        raise ValueError("max_failures_allowed must be a non-negative integer")
    if str(payload["mode"]) not in {"monitor", "enforce"}:
        raise ValueError("mode must be monitor or enforce")
    return payload


def _load_profile_cases(base_dir: Path) -> dict[str, Any]:
    path = (base_dir / DEFAULT_PROFILES_RELATIVE_PATH).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise ValueError("profile contract has no cases")
    return cases


def _resolve_selected_cases(
    *,
    raw_cases: str | None,
    thresholds: dict[str, Any],
    profile_cases: dict[str, Any],
) -> list[str]:
    selected = _parse_cases(raw_cases) if raw_cases else [str(v) for v in thresholds["required_cases"]]
    unknown = sorted(case_id for case_id in selected if case_id not in profile_cases)
    if unknown:
        raise ValueError(f"unknown case IDs: {unknown}")
    return selected


def _nodeids_for_cases(selected_cases: list[str]) -> list[str]:
    nodeids: list[str] = ["tests/test_visual_profile_contract.py"]
    for case_id in selected_cases:
        nodeid = CASE_TO_NODEID.get(case_id)
        if not nodeid:
            raise ValueError(f"case has no nodeid mapping: {case_id}")
        nodeids.append(nodeid)
    # Keep deterministic order while avoiding duplicates.
    return list(dict.fromkeys(nodeids))


def _run_pytest(*, base_dir: Path, nodeids: list[str], junit_path: Path) -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *nodeids,
        "-q",
        "-p",
        "no:cacheprovider",
        "--junitxml",
        str(junit_path),
    ]
    completed = subprocess.run(cmd, cwd=str(base_dir), check=False)
    return int(completed.returncode)


def _collect_test_results(junit_path: Path) -> dict[str, dict[str, str]]:
    if not junit_path.exists():
        return {}
    root = ElementTree.fromstring(junit_path.read_text(encoding="utf-8"))
    results: dict[str, dict[str, str]] = {}
    for testcase in root.iter("testcase"):
        name = str(testcase.attrib.get("name", "")).strip()
        if not name:
            continue
        status = "passed"
        message = ""
        failure = testcase.find("failure")
        error = testcase.find("error")
        skipped = testcase.find("skipped")
        if failure is not None:
            status = "failed"
            message = str(failure.attrib.get("message") or failure.text or "").strip()
        elif error is not None:
            status = "failed"
            message = str(error.attrib.get("message") or error.text or "").strip()
        elif skipped is not None:
            status = "skipped"
            message = str(skipped.attrib.get("message") or skipped.text or "").strip()
        results[name] = {"status": status, "message": message}
    return results


def _build_case_results(
    *,
    selected_cases: list[str],
    profile_cases: dict[str, Any],
    test_results: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in selected_cases:
        test_name = CASE_TO_TEST_NAME[case_id]
        result = test_results.get(test_name)
        status = "missing" if result is None else str(result.get("status", "missing"))
        message = "" if result is None else str(result.get("message", ""))
        rows.append(
            {
                "id": case_id,
                "test_name": test_name,
                "status": status,
                "message": message,
                "profile": profile_cases.get(case_id, {}),
            }
        )
    return rows


def _evaluate_thresholds(
    *,
    selected_cases: list[str],
    case_results: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> list[str]:
    violations: list[str] = []
    required = {str(value) for value in thresholds["required_cases"]}
    selected = set(selected_cases)
    missing_required = sorted(required.difference(selected))
    if missing_required:
        violations.append(f"required_cases not selected: {missing_required}")

    failing = [row for row in case_results if row["status"] != "passed"]
    max_failures_allowed = int(thresholds["max_failures_allowed"])
    if len(failing) > max_failures_allowed:
        violations.append(f"failing cases {len(failing)} exceed max_failures_allowed {max_failures_allowed}")
    return violations


def _write_run_report(
    *,
    output_dir: Path,
    measurement_id: str,
    mode: str,
    pytest_exit_code: int,
    selected_cases: list[str],
    case_results: list[dict[str, Any]],
    thresholds_path: Path,
    threshold_violations: list[str],
    junit_path: Path,
) -> Path:
    report_path = output_dir / f"{measurement_id}.json"
    payload = {
        "meta": {
            "measurement_id": measurement_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": mode,
            "pytest_exit_code": pytest_exit_code,
            "thresholds_path": str(thresholds_path),
            "selected_cases": selected_cases,
            "junit_xml": str(junit_path),
        },
        "summary": {
            "total_cases": len(case_results),
            "failing_cases": sum(1 for row in case_results if row["status"] != "passed"),
            "threshold_violations": threshold_violations,
            "lane_status": "passed" if pytest_exit_code == 0 and not threshold_violations else "failed",
        },
        "cases": case_results,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def run_lane(
    *,
    mode: str,
    base_dir: Path,
    output_dir: Path | None,
    raw_cases: str | None,
    thresholds_path: Path | None = None,
) -> int:
    if mode not in {"monitor", "enforce"}:
        raise ValueError(f"unsupported mode: {mode}")

    resolved_thresholds_path = _resolve_thresholds_path(base_dir, thresholds_path)
    thresholds = _load_thresholds(resolved_thresholds_path)
    profile_cases = _load_profile_cases(base_dir)
    selected_cases = _resolve_selected_cases(
        raw_cases=raw_cases,
        thresholds=thresholds,
        profile_cases=profile_cases,
    )
    nodeids = _nodeids_for_cases(selected_cases)

    runs_dir = output_dir if output_dir is not None else (base_dir / DEFAULT_RUNS_DIR)
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    measurement_id = f"phase10c_ui_visual_run_{timestamp}"
    junit_path = runs_dir / f"{measurement_id}.junit.xml"

    pytest_rc = _run_pytest(base_dir=base_dir, nodeids=nodeids, junit_path=junit_path)
    test_results = _collect_test_results(junit_path)
    case_results = _build_case_results(
        selected_cases=selected_cases,
        profile_cases=profile_cases,
        test_results=test_results,
    )

    threshold_violations: list[str] = []
    if mode == "enforce":
        threshold_violations = _evaluate_thresholds(
            selected_cases=selected_cases,
            case_results=case_results,
            thresholds=thresholds,
        )

    report_path = _write_run_report(
        output_dir=runs_dir,
        measurement_id=measurement_id,
        mode=mode,
        pytest_exit_code=pytest_rc,
        selected_cases=selected_cases,
        case_results=case_results,
        thresholds_path=resolved_thresholds_path,
        threshold_violations=threshold_violations,
        junit_path=junit_path,
    )
    print(f"[CI-UI-VISUAL] report: {report_path}")

    if pytest_rc != 0:
        print("[CI-UI-VISUAL] pytest failed.")
        return 1
    if mode == "enforce" and threshold_violations:
        print(f"[CI-UI-VISUAL] threshold violations: {threshold_violations}")
        return 1
    print("[CI-UI-VISUAL] lane passed.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run CI UI visual regression lane for FTIV.")
    parser.add_argument("--mode", choices=("monitor", "enforce"), required=True, help="Lane mode.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Project base directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for visual run reports.",
    )
    parser.add_argument(
        "--cases",
        default=None,
        help="Optional comma-separated case IDs to run. Defaults to required_cases in thresholds.",
    )
    parser.add_argument(
        "--thresholds-path",
        type=Path,
        default=None,
        help="Optional override for phase10c thresholds JSON path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    base_dir = args.base_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir is not None else None
    try:
        return run_lane(
            mode=args.mode,
            base_dir=base_dir,
            output_dir=output_dir,
            raw_cases=args.cases,
            thresholds_path=args.thresholds_path,
        )
    except ValueError as exc:
        print(f"[CI-UI-VISUAL] invalid config: {exc}")
        return 2
    except FileNotFoundError as exc:
        print(f"[CI-UI-VISUAL] missing file: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
