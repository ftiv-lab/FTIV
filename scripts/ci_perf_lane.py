#!/usr/bin/env python
"""CI entrypoint for Phase 9E/9F performance lanes.

Modes:
- monitor: run measurement in monitoring mode (no threshold enforcement)
- enforce: run measurement with threshold enforcement
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts import measure_phase9e

DEFAULT_SCENARIOS = ("P9E-S06", "P9E-S05", "P9E-S02")


def _parse_scenarios(raw: str) -> list[str]:
    values = [token.strip() for token in str(raw).split(",") if token.strip()]
    if not values:
        raise ValueError("at least one scenario ID is required")
    return values


def _build_measure_args(
    *,
    base_dir: Path,
    output_dir: Path | None,
    scenarios: list[str],
    warmup: int,
    samples: int,
) -> list[str]:
    args = [
        "--base-dir",
        str(base_dir),
        "--warmup",
        str(max(0, int(warmup))),
        "--samples",
        str(max(1, int(samples))),
    ]
    if output_dir is not None:
        args.extend(["--output-dir", str(output_dir)])
    for scenario_id in scenarios:
        args.extend(["--scenario", scenario_id])
    return args


def run_lane(
    *,
    mode: str,
    base_dir: Path,
    output_dir: Path | None,
    scenarios: list[str],
    warmup: int,
    samples: int,
) -> int:
    if mode not in {"monitor", "enforce"}:
        raise ValueError(f"unsupported mode: {mode}")

    measure_args = _build_measure_args(
        base_dir=base_dir,
        output_dir=output_dir,
        scenarios=scenarios,
        warmup=warmup,
        samples=samples,
    )

    prev_enforce = os.getenv(measure_phase9e.ENV_PERF_ENFORCE)
    try:
        if mode == "enforce":
            os.environ[measure_phase9e.ENV_PERF_ENFORCE] = "1"
        else:
            os.environ.pop(measure_phase9e.ENV_PERF_ENFORCE, None)

        rc = int(measure_phase9e.main(measure_args))
        # Normalize exit status for CI consumers: success=0, failure=1.
        return 0 if rc == 0 else 1
    finally:
        if prev_enforce is None:
            os.environ.pop(measure_phase9e.ENV_PERF_ENFORCE, None)
        else:
            os.environ[measure_phase9e.ENV_PERF_ENFORCE] = prev_enforce


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run CI performance lane for FTIV.")
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
        help="Optional output directory for measurement reports.",
    )
    parser.add_argument(
        "--scenarios",
        default=",".join(DEFAULT_SCENARIOS),
        help="Comma separated scenario IDs (default: P9E-S06,P9E-S05,P9E-S02).",
    )
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per scenario.")
    parser.add_argument("--samples", type=int, default=3, help="Measured runs per scenario for CI lane.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        scenarios = _parse_scenarios(args.scenarios)
    except ValueError as exc:
        print(f"[CI-PERF] invalid scenarios: {exc}")
        return 2

    print(f"[CI-PERF] mode={args.mode} scenarios={','.join(scenarios)}")
    result = run_lane(
        mode=args.mode,
        base_dir=args.base_dir.resolve(),
        output_dir=args.output_dir.resolve() if args.output_dir is not None else None,
        scenarios=scenarios,
        warmup=args.warmup,
        samples=args.samples,
    )
    if result == 0:
        print("[CI-PERF] lane passed.")
    else:
        print("[CI-PERF] lane failed.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
