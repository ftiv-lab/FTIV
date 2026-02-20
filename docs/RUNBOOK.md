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

## 6.1 Mode Contract (Current)
1. FTIV has no dedicated "MindMap mode" runtime path.
2. Visual mapping is provided by Connector relationships on the desktop overlay.
3. In docs and UI wording, avoid "MindMap mode" and prefer "visual map / relationship mapping".

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

## 10. Phase 10D Lane (UI Regression Enforce Governance)
1. Policy contract:
- `config/ui/phase10d_visual_gate_policy.json`
2. Policy + lane tests:
- `uv run pytest tests/test_ui_visual_gate_policy_contract.py tests/test_ci_ui_visual_lane.py tests/test_ui_visual_diff_report.py -q -p no:cacheprovider`
3. Visual contract suite:
- `uv run pytest tests/test_visual_profile_contract.py tests/test_visual_regression_minimal.py tests/test_visual_regression_contract.py -q -p no:cacheprovider`
4. Normal operation (PR/monitor):
- `uv run python scripts/ci_ui_visual_lane.py --mode monitor`
5. Normal operation (main/enforce):
- `uv run python scripts/ci_ui_visual_lane.py --mode enforce`
6. Failure triage diff:
- `uv run python scripts/ui_visual_diff_report.py`
7. Emergency temporary exception rule:
- `temporary_exceptions` entry requires `case_id / reason / expires_at`
- `expires_at` past date is treated as hard failure in enforce mode
- exception window must not exceed `governance.max_exception_days`
8. Governance:
- See `docs/internal/architecture/phase10d_visual_gate_governance.md`

## 11. Layer / Connector Shortcut Contract (feat/layer-tab)

### 11.1 Frozen shortcut assignments (do not reassign)

| Key | Action | File |
|-----|--------|------|
| Ctrl+Click | Resume animation | `windows/base_window.py` |
| Tab | Create child TextWindow | `windows/text_window.py` |
| Enter | Create sibling TextWindow | `windows/text_window.py` |
| F | Toggle frontmost | `windows/base_window.py` |
| H | Toggle hidden | `windows/base_window.py` |
| Delete | Delete window | `windows/base_window.py` |
| Wheel | Scale (ImageWindow) / font size (TextWindow) | respective files |

### 11.2 Layer operation key assignments

| Layer operation | Primary route | Secondary (shortcut) |
|----------------|---------------|----------------------|
| Attach child | LayerTab / right-click menu | none |
| Detach from parent | LayerTab / right-click menu | none |
| Move toward front | LayerTab `Bring Front` / `前面へ` | none |
| Move toward back | LayerTab `Send Back` / `背面へ` | none |

### 11.3 Rules

- **Shift shortcuts are intentionally unassigned for both Connector and Layer operations.**
- Connector creation must be done via MainWindow UI / context menu routes.
- All Layer operations must be completable without shortcuts (UI-only path is the default contract).
- Any new shortcut addition must not conflict with the frozen table above.
- Regression test: `tests/test_shortcut_contract.py`

### 11.4 Layer tab lane

1. Prerequisite tests:
- `uv run pytest tests/test_shortcut_contract.py tests/test_layer_prerequisites.py -q -p no:cacheprovider`
2. Selection / context checks:
- `uv run pytest tests/test_window_manager.py tests/test_window_manager_extended.py -q -p no:cacheprovider`
3. Performance smoke (cross-lane check):
- `uv run pytest tests/test_performance_smoke.py -q -p no:cacheprovider`
4. Final integrated verification:
- `cmd /c verify_all.bat`

### 11.5 Layer Attach UX (Parent Slot Contract)

1. Layer operations are completed in LayerTab without adding shortcuts.
2. Recommended flow:
- Select or focus the parent candidate in LayerTab, then click `Set Parent`.
- Select the child window in tree, then click `Make Child`.
- Use `Detach` to make child independent again.
3. Drag & Drop in LayerTab is a secondary route:
- Drop on item => attach (make child).
- Drop between items => reorder within siblings.
- Drop on viewport empty area => detach (if currently attached).
4. Sonar Hover (MVP):
- Hovering a Layer item briefly highlights the corresponding window subtree on canvas.
4. Undo contract:
  - Attach / Detach / Reorder are all undoable (`Ctrl+Z`).
  - Reorder from both button route and D&D route is recorded in undo stack.
5. Context menu routing:
- If right-click lands on MainWindow but the cursor is over the currently selected overlay window, FTIV forwards the menu to that selected window (useful in click-through scenarios).
