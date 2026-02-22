#!/usr/bin/env python
"""Generate diff report between two Phase 10C UI visual run JSON files."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RUNS_DIR = Path("docs/internal/architecture/ui_visual_runs")


@dataclass(frozen=True)
class VisualCaseStatus:
    status: str
    message: str
    test_name: str
    rerun_command: str


@dataclass(frozen=True)
class VisualRunReport:
    path: Path
    measurement_id: str
    mode: str
    cases: dict[str, VisualCaseStatus]


def _load_report(path: Path) -> VisualRunReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid report root object: {path}")

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        raise ValueError(f"missing meta object: {path}")
    measurement_id = str(meta.get("measurement_id") or path.stem)
    mode = str(meta.get("mode") or "unknown")

    cases_raw = payload.get("cases")
    if not isinstance(cases_raw, list):
        raise ValueError(f"missing cases list: {path}")

    cases: dict[str, VisualCaseStatus] = {}
    for entry in cases_raw:
        if not isinstance(entry, dict):
            continue
        case_id = str(entry.get("id") or "").strip()
        if not case_id:
            continue
        status = str(entry.get("status") or "unknown")
        message = str(entry.get("message") or "")
        test_name = str(entry.get("test_name") or "")
        rerun_command = str(entry.get("rerun_command") or "")
        cases[case_id] = VisualCaseStatus(
            status=status,
            message=message,
            test_name=test_name,
            rerun_command=rerun_command,
        )

    if not cases:
        raise ValueError(f"no case results found: {path}")

    return VisualRunReport(path=path, measurement_id=measurement_id, mode=mode, cases=cases)


def _resolve_latest_pair(runs_dir: Path) -> tuple[Path, Path]:
    reports = sorted(runs_dir.glob("phase10c_ui_visual_run_*.json"))
    if len(reports) < 2:
        raise FileNotFoundError("need at least two phase10c_ui_visual_run_*.json files")
    return reports[-2], reports[-1]


def _build_markdown(base: VisualRunReport, target: VisualRunReport) -> str:
    case_ids = sorted(set(base.cases).union(target.cases))
    if not case_ids:
        raise ValueError("no cases found for diff report")

    lines: list[str] = []
    lines.append("# Phase 10C UI Visual Diff Report")
    lines.append(f"- Base: `{base.measurement_id}` ({base.path.name}, mode={base.mode})")
    lines.append(f"- Target: `{target.measurement_id}` ({target.path.name}, mode={target.mode})")
    lines.append("")
    lines.append("## Case Status Diff")
    lines.append("")
    lines.append("| Case ID | Base | Target | Changed |")
    lines.append("|---|---|---|---|")

    regressions: list[str] = []
    improvements: list[str] = []
    message_changes: list[str] = []
    for case_id in case_ids:
        b = base.cases.get(case_id, VisualCaseStatus(status="missing", message="", test_name="", rerun_command=""))
        t = target.cases.get(case_id, VisualCaseStatus(status="missing", message="", test_name="", rerun_command=""))
        changed = b.status != t.status
        lines.append(f"| {case_id} | {b.status} | {t.status} | {'yes' if changed else 'no'} |")

        if b.status != "failed" and t.status == "failed":
            regressions.append(case_id)
        if b.status != "passed" and t.status == "passed":
            improvements.append(case_id)
        if (b.message or t.message) and b.message != t.message:
            message_changes.append(case_id)

    new_failures = [
        case_id
        for case_id in case_ids
        if base.cases.get(case_id, VisualCaseStatus("missing", "", "", "")).status == "passed"
        and target.cases.get(case_id, VisualCaseStatus("missing", "", "", "")).status == "failed"
    ]

    lines.append("")
    lines.append("## Top Regressions")
    lines.append("")
    if regressions:
        for case_id in regressions:
            target_case = target.cases.get(case_id, VisualCaseStatus("missing", "", "", ""))
            lines.append(f"- `{case_id}` ({target_case.status})")
            if target_case.rerun_command:
                lines.append(f"  - rerun: `{target_case.rerun_command}`")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## New Failures")
    lines.append("")
    if new_failures:
        for case_id in new_failures:
            target_case = target.cases.get(case_id, VisualCaseStatus("missing", "", "", ""))
            lines.append(f"- `{case_id}`")
            if target_case.rerun_command:
                lines.append(f"  - rerun: `{target_case.rerun_command}`")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Improvements")
    lines.append("")
    if improvements:
        for case_id in improvements:
            lines.append(f"- `{case_id}`")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Failure Message Changes")
    lines.append("")
    if message_changes:
        for case_id in message_changes:
            b = base.cases.get(case_id, VisualCaseStatus(status="missing", message="", test_name="", rerun_command=""))
            t = target.cases.get(
                case_id, VisualCaseStatus(status="missing", message="", test_name="", rerun_command="")
            )
            lines.append(f"- `{case_id}`")
            lines.append(f"  - base: `{b.message[:120]}`")
            lines.append(f"  - target: `{t.message[:120]}`")
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate diff report between two UI visual run JSON files.")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Directory containing phase10c_ui_visual_run_*.json files.",
    )
    parser.add_argument("--base-report", type=Path, default=None, help="Base JSON report path.")
    parser.add_argument("--target-report", type=Path, default=None, help="Target JSON report path.")
    parser.add_argument("--output-file", type=Path, default=None, help="Output markdown path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    runs_dir = args.runs_dir.resolve()
    try:
        if args.base_report is not None and args.target_report is not None:
            base_path = args.base_report.resolve()
            target_path = args.target_report.resolve()
        else:
            base_path, target_path = _resolve_latest_pair(runs_dir)

        base_report = _load_report(base_path)
        target_report = _load_report(target_path)
        markdown = _build_markdown(base_report, target_report)

        if args.output_file is not None:
            output_path = args.output_file.resolve()
        else:
            output_name = f"phase10c_ui_visual_diff_{target_report.measurement_id}_vs_{base_report.measurement_id}.md"
            output_path = runs_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"[Phase10C-UI-DIFF] report: {output_path}")
        return 0
    except Exception as exc:
        print(f"[Phase10C-UI-DIFF] error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
