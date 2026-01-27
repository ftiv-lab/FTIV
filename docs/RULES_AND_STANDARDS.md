# Antigravity Development Standards & Rules v4.0 (Reliability)

## 1. UI Access Strategy (Fail Fast)

### ⛔ PROHIBITED (Exploratory Access)
*   `hasattr` usage to "guess" if a widget exists.
*   `try-except AttributeError` just to silence errors when a widget is missing.
*   Assumption that `MainWindow` holds all widgets directly (e.g. `self.mw.btn_start`).

### ✅ REQUIRED (Explicit Path)
*   Access widgets via their definitive containers (Tabs/Panels).
    *   Example: `self.mw.animation_tab.anim_move_speed`
*   If a widget is moved or renamed, the code MUST fail immediately (AttributeError), so that tests/linters catch it.
*   **Encapsulation**: If possible, define accessor methods in the Tab class, rather than exposing raw widgets.

## 2. Pre-flight Check Workflow

Before starting any task involving UI or logic changes, follow this checklist:

1.  **Verify Structure**: Use `view_file` on the target Tab/Window's `__init__` or `setup_ui` to confirm exact widget names.
2.  **Audit References**: Run `tools/check_ui_refs.py` to ensure no "unsafe" MainWindow assumptions are being introduced.
3.  **Run Integrity Tests**: Run `pytest tests/test_ui_structure.py` to ensure the known world matches reality.

## 3. Testing Requirements

*   **Logic Isolation**: Business logic (Managers/Controllers) must be testable without a real GUI (using `pytest` + `unittest.mock` or headless Qt).
*   **Structural Integrity**: If you rename a UI variable, you MUST update `tests/test_ui_structure.py`.
*   **Regression Check**: Before finishing a task, run existing tests to ensure no regressions.

## 4. Documentation

*   Update `task.md` continuously.
*   Keep `docs/refactoring_plans/` up to date with major architectural decisions.
