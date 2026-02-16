#!/usr/bin/env python
"""Generate diff report between two Phase 9E measurement JSON files."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RUNS_DIR = Path("docs/internal/architecture/performance_runs")


@dataclass(frozen=True)
class ScenarioMetrics:
    median_ms: float
    p95_ms: float


@dataclass(frozen=True)
class ReportData:
    path: Path
    measurement_id: str
    scenarios: dict[str, ScenarioMetrics]


def _pct_change(before: float, after: float) -> float:
    if before == 0:
        return 0.0 if after == 0 else 100.0
    return ((after - before) / before) * 100.0


def _load_report(path: Path) -> ReportData:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid report root object: {path}")

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        raise ValueError(f"missing meta object: {path}")
    measurement_id = str(meta.get("measurement_id") or path.stem)

    scenarios_raw = payload.get("scenarios")
    if not isinstance(scenarios_raw, list):
        raise ValueError(f"missing scenarios list: {path}")

    scenarios: dict[str, ScenarioMetrics] = {}
    for entry in scenarios_raw:
        if not isinstance(entry, dict):
            continue
        scenario_id = str(entry.get("id") or "").strip()
        elapsed = entry.get("elapsed_ms")
        if not scenario_id or not isinstance(elapsed, dict):
            continue
        median = float(elapsed.get("median", 0.0))
        p95 = float(elapsed.get("p95", 0.0))
        scenarios[scenario_id] = ScenarioMetrics(median_ms=median, p95_ms=p95)

    if not scenarios:
        raise ValueError(f"no scenario metrics found: {path}")

    return ReportData(path=path, measurement_id=measurement_id, scenarios=scenarios)


def _resolve_latest_pair(runs_dir: Path) -> tuple[Path, Path]:
    reports = sorted(runs_dir.glob("phase9e_measurement_*.json"))
    if len(reports) < 2:
        raise FileNotFoundError("need at least two phase9e_measurement_*.json files")
    return reports[-2], reports[-1]


def _build_markdown(base: ReportData, target: ReportData) -> str:
    shared_ids = sorted(set(base.scenarios).intersection(target.scenarios))
    if not shared_ids:
        raise ValueError("no shared scenarios between base and target reports")

    lines: list[str] = []
    lines.append("# Phase 9E Diff Report")
    lines.append(f"- Base: `{base.measurement_id}` ({base.path.name})")
    lines.append(f"- Target: `{target.measurement_id}` ({target.path.name})")
    lines.append("")

    lines.append("## Scenario Diff")
    lines.append("")
    lines.append(
        "| Scenario | Base median | Target median | Δ median | Δ median % | Base p95 | Target p95 | Δ p95 | Δ p95 % |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    delta_rows: list[tuple[str, float, float, float, float]] = []
    for scenario_id in shared_ids:
        b = base.scenarios[scenario_id]
        t = target.scenarios[scenario_id]
        delta_median = t.median_ms - b.median_ms
        delta_p95 = t.p95_ms - b.p95_ms
        pct_median = _pct_change(b.median_ms, t.median_ms)
        pct_p95 = _pct_change(b.p95_ms, t.p95_ms)
        delta_rows.append((scenario_id, delta_median, pct_median, delta_p95, pct_p95))
        lines.append(
            f"| {scenario_id} | {b.median_ms:.4f} | {t.median_ms:.4f} | {delta_median:+.4f} | {pct_median:+.2f}% | "
            f"{b.p95_ms:.4f} | {t.p95_ms:.4f} | {delta_p95:+.4f} | {pct_p95:+.2f}% |"
        )

    lines.append("")
    lines.append("## Top Regressions (median)")
    lines.append("")
    regressions = sorted((row for row in delta_rows if row[1] > 0), key=lambda row: row[1], reverse=True)[:3]
    if regressions:
        for scenario_id, delta_median, pct_median, _, _ in regressions:
            lines.append(f"- `{scenario_id}`: {delta_median:+.4f} ms ({pct_median:+.2f}%)")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Top Improvements (median)")
    lines.append("")
    improvements = sorted((row for row in delta_rows if row[1] < 0), key=lambda row: row[1])[:3]
    if improvements:
        for scenario_id, delta_median, pct_median, _, _ in improvements:
            lines.append(f"- `{scenario_id}`: {delta_median:+.4f} ms ({pct_median:+.2f}%)")
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate diff report between two Phase 9E measurement JSON files.")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Directory containing phase9e_measurement_*.json files.",
    )
    parser.add_argument("--base-report", type=Path, default=None, help="Base JSON report path.")
    parser.add_argument("--target-report", type=Path, default=None, help="Target JSON report path.")
    parser.add_argument("--output-file", type=Path, default=None, help="Output markdown path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    runs_dir = args.runs_dir.resolve()

    try:
        if args.base_report and args.target_report:
            base_path = args.base_report.resolve()
            target_path = args.target_report.resolve()
        else:
            base_path, target_path = _resolve_latest_pair(runs_dir)

        base_data = _load_report(base_path)
        target_data = _load_report(target_path)
        markdown = _build_markdown(base_data, target_data)

        if args.output_file is not None:
            output_path = args.output_file.resolve()
        else:
            output_name = f"phase9e_diff_{target_data.measurement_id}_vs_{base_data.measurement_id}.md"
            output_path = runs_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"[Phase9E-DIFF] report: {output_path}")
        return 0
    except Exception as exc:
        print(f"[Phase9E-DIFF] error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
