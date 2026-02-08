# Antigravity Development Standards & Rules v5.0 (Phase 2)

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

### 3.1 Core Testing Principles
*   **Logic Isolation**: Business logic (Managers/Controllers) must be testable without a real GUI (using `pytest` + `unittest.mock` or headless Qt).
*   **Structural Integrity**: If you rename a UI variable, you MUST update `tests/test_ui_structure.py`.
*   **Regression Check**: Before finishing a task, run existing tests to ensure no regressions.

### 3.2 Property-Based Testing (Phase 2)
*   Use **Hypothesis** for model validation tests.
*   Example: `tests/test_hypothesis.py` validates WindowConfig, ImageWindowConfig, TextWindowConfig.
*   Property tests discover edge cases humans miss.

### 3.3 Coverage Requirements
*   **Minimum Threshold**: 27% (enforced by `verify_all.bat`)
*   **Target Threshold**: 30%+
*   **Critical Modules**: Aim for 100% on ConfigGuardian, SpacingManager.

*   Keep `docs/refactoring_plans/` up to date with major architectural decisions.

## 4. Maintenance & Reset
*   **Do NOT pollute Main App**: Never add "Debug Reset Buttons" inside the production UI.
*   **Use External Scripts**: If you mess up the configuration during testing (e.g., Red text, Vertical mode default), use:
    *   `uv run scripts/reset_defaults.py`
    *   This restores `text_archetype.json` to factory settings (White, Horizontal, Zero margins).

## 5. Modern Quality Gates (Super Senior Stack)

### 🛡️ Type Safety Paradox
> **"Dynamic language requires static discipline."**

*   **Zero Mypy Errors**:
    *   `check_untyped_defs = True`: Even untyped functions are checked.
    *   `strict_optional = True`: No more `None` surprises.
*   **No `Any` abuse**: If you must use it, explain WHY in a comment.

### 🔧 Qt6 Enum Standard (Phase 2)
*   Use **fully qualified enum names**:
    *   ✅ `Qt.Orientation.Horizontal`
    *   ❌ `Qt.Horizontal`
*   Apply to all Qt enums: `QFont.SpacingType`, `QSizePolicy.Policy`, etc.

### ⚡️ Forward Declaration Pattern (Phase 2)
*   When using class attributes in lambdas/callbacks before definition:
    ```python
    self.my_widget: Optional[QWidget] = None  # Forward declaration
    ```
*   Prevents Mypy `has-type` errors.

### ⚡ fast-track & pre-commit
*   **Git Hooks**: `pre-commit` prevents bad code from entering the repo.
*   **Virtual Pre-Commit**: Run `python scripts/hook_pre_commit.py` before `git commit`.
*   **Dev Command**: ALWAYS use `uv run <command>`.
    *   ❌ `python main.py`
    *   ✅ `uv run main.py`

## 6. verify_all.bat Workflow

**One-Click Verification**:
```batch
cmd /c verify_all.bat
```

**Checks (in order)**:
1. Ruff Linter
2. UI Reference Audit
3. Mypy Type Checks (52 files)
4. Core Tests + Coverage (111 tests, 27%+)
5. Interactive Tests (75 tests)
6. Chaos/Stress Tests (6 tests)

**Total: 192 tests must pass before committing.**

