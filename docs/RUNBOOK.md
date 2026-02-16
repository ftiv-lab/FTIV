# FTIV Development Runbook

Updated: 2026-02-17

## 1. Purpose
This is the single tracked entry point for development flow in FTIV.
If you are new to the repository or switching environments, start here.

## 2. Quick Start
1. Sync env:
- `uv sync`
2. Run app:
- `uv run main.py`
3. Run targeted tests first:
- `uv run pytest <target> -q -p no:cacheprovider`
4. Final integrated check:
- `cmd /c verify_all.bat`

## 3. Current Perf Contract (Tracked)
1. Thresholds:
- `config/perf/phase9e_performance_thresholds.json`
2. CI default scenarios:
- `config/perf/phase9e_scenarios.json`
3. Rules:
- `docs/perf/performance_contract.md`

## 4. Perf Commands
1. Monitor mode:
- `uv run python scripts/ci_perf_lane.py --mode monitor`
2. Enforce mode:
- `uv run python scripts/ci_perf_lane.py --mode enforce`
3. Diff report:
- `uv run python scripts/phase9e_perf_diff_report.py`

## 5. Legacy Fallback Sunset (Finalized)
1. Legacy path fallback for perf contracts under `docs/internal/architecture/*` has been removed.
2. Runtime now resolves only tracked contract files under `config/perf/*` (unless env override is set).
3. If a custom path is needed, use:
- `FTIV_PERF_THRESHOLDS_PATH=<absolute_or_relative_path>`

## 6. Environment Notes
1. Use `uv run` for Python commands.
2. Keep push human-only unless explicitly requested.
3. If terminal output becomes garbled, restore UTF-8 before editing:
- `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

## 7. Phase 10A Lane (UI Structure + Visual Regression)
1. Boundary guard:
- `uv run pytest tests/test_architecture_boundaries.py -q -p no:cacheprovider`
2. UI orchestration scope:
- `uv run pytest tests -q -p no:cacheprovider -k "property_panel or text_window"`
3. Visual minimal regression:
- `uv run pytest tests/test_visual_regression_minimal.py -q -p no:cacheprovider`
4. Dialog-only flow guard:
- `uv run pytest tests/test_dialog_edit_flow.py -q -p no:cacheprovider`
5. Final integrated verification:
- `cmd /c verify_all.bat`

## 8. Phase 10B Lane (UI Regression Contract Hardening)
1. Boundary guard:
- `uv run pytest tests/test_architecture_boundaries.py -q -p no:cacheprovider`
2. Visual profile contract:
- `uv run pytest tests/test_visual_profile_contract.py -q -p no:cacheprovider`
3. Visual regression contract:
- `uv run pytest tests/test_visual_regression_minimal.py tests/test_visual_regression_contract.py -q -p no:cacheprovider`
4. Dialog-only guard:
- `uv run pytest tests/test_dialog_edit_flow.py -q -p no:cacheprovider`
5. Final integrated verification:
- `cmd /c verify_all.bat`

## 9. Phase 10C Lane (UI Regression CI Operationalization)
1. Visual contract suite:
- `uv run pytest tests/test_visual_profile_contract.py tests/test_visual_regression_minimal.py tests/test_visual_regression_contract.py -q -p no:cacheprovider`
2. CI helper tests:
- `uv run pytest tests/test_ci_ui_visual_lane.py tests/test_ui_visual_diff_report.py -q -p no:cacheprovider`
3. UI visual lane (monitor):
- `uv run python scripts/ci_ui_visual_lane.py --mode monitor`
4. UI visual lane (enforce):
- `uv run python scripts/ci_ui_visual_lane.py --mode enforce`
5. UI visual diff report:
- `uv run python scripts/ui_visual_diff_report.py`
6. Final integrated verification:
- `cmd /c verify_all.bat`
