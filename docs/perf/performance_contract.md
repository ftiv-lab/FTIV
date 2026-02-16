# FTIV Performance Contract

Updated: 2026-02-16

## Goal
1. Keep performance verification reproducible across environments and AI agents.
2. Define one source of truth for thresholds and CI scenario selection.
3. Make threshold changes auditable with measurement evidence.

## Contract Files
1. Threshold rules: `config/perf/phase9e_performance_thresholds.json`
2. CI default scenarios: `config/perf/phase9e_scenarios.json`

## Execution Modes
1. `monitor`
- Use during daily development.
- Command: `uv run python scripts/ci_perf_lane.py --mode monitor`
2. `enforce`
- Use for regression checks and release readiness.
- Command: `uv run python scripts/ci_perf_lane.py --mode enforce`

## Threshold Update Rules
1. Update thresholds only with a baseline + target measurement pair.
2. Generate diff evidence:
- `uv run python scripts/phase9e_perf_diff_report.py`
3. Keep change scope small (prefer 3 scenarios or fewer per update).
4. Validate with:
- `uv run pytest tests/test_performance_smoke.py -q -p no:cacheprovider`
- `uv run python scripts/ci_perf_lane.py --mode enforce`
- `cmd /c verify_all.bat`

## Migration Compatibility
1. Current scripts prefer `config/perf/*`.
2. Legacy files under `docs/internal/architecture/*` are supported temporarily when present.
3. When legacy paths are used, scripts emit a warning and should be migrated.
