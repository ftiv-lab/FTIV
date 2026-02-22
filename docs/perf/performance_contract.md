# FTIV Performance Contract

Updated: 2026-02-17

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

## Legacy Sunset Policy
1. Performance contract legacy fallback under `docs/internal/architecture/*` is removed.
2. Runtime contract paths are fixed to `config/perf/*` unless `FTIV_PERF_THRESHOLDS_PATH` is explicitly set.
3. Historical plan documents remain available for reference and training material; only runtime fallback paths were removed.
