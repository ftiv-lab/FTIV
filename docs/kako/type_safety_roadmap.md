# Type Safety Roadmap: From "Green Baseline" to "Strict Compliance" (Super Senior Edition)

**Current Status**: We have established a "Baseline Green" by silencing ~700 errors.
**Goal**: Systematically remove these silencers and fix the underlying logic, transforming FTIV into a strictly typed, crash-resistant application.

---

## 🛡️ Philosophy: "The Pyramid of Types"

We will not fix errors randomly. We will fix them in layers, starting from the foundation.

1.  **Foundation (Syntax & Structure)**: valid-type, name-defined, no-redef.
2.  **Framework (Qt/PySide)**: attr-defined, call-overload (The hardest part).
3.  **Logic (Data Flow)**: arg-type, return-value.
4.  **Strictness (Null Safety)**: strict_optional.

---

## 🗺️ Execution Plan

### Phase 1: Low Hanging Fruit (Syntax Cleanup)
**Target**: `valid-type`, `name-defined`, `no-redef`, `unused-ignore`.
**Difficulty**: 🟢 Easy
**Risk**: 🟢 Low

*   **Objective**: Fix obvious Python syntax misunderstandings.
*   **Action Items**:
    1.  Replace `callable` with `typing.Callable` (Python 3.9+ deprecation).
    2.  Rename variables in loops to avoid `no-redef` (Reuse of variable names).
    3.  Remove `type: ignore` comments that are no longer needed (`unused-ignore`).

### Phase 2: The "Qt Trap" (Framework Correctness)
**Target**: `call-overload`, `attr-defined`.
**Difficulty**: 🔴 Hard
**Risk**: 🟡 Medium

*   **Objective**: Align our code with PySide6's strict C++ type definitions.
*   **Problem**: Python allows flexible arguments, but C++ via PySide6 does not. Mypy sees the C++ signatures.
*   **Action Items**:
    1.  **Overload resolution**: When calling `QAction` or `QPoint`, we must match *exact* signatures.
        *   *Example*: `QPoint(float, float)` is invalid. It must be `QPoint(int, int)`. We must cast `int()`.
    2.  **Missing Attributes**: `MainWindow.mindmaps` etc. need proper Type Hints in `__init__`.
    3.  **Refactor**: Use `typing.cast` judiciously where PySide stubs are wrong (rare).

### Phase 3: Core Logic Integrity
**Target**: `arg-type`, `return-value`, `assignment`.
**Difficulty**: 🟡 Medium
**Risk**: 🔴 High (Potential Logic Changes)

*   **Objective**: Ensure functions receive what they expect. This catches real bugs.
*   **Action Items**:
    1.  **Focus on Models**: `window_config.py` must be perfect.
    2.  **Focus on Managers**: `WindowManager` passing incorrect types to windows.
    3.  **Correction**:
        *   If a function takes `int`, do not pass `float`.
        *   If a function returns `None`, ensure the type hint says `-> None`, not `-> str`.

### Phase 4: The "Strict" Standard (Null Safety)
**Target**: `strict_optional`, `check_untyped_defs = true`.
**Difficulty**: 🟡 Medium
**Risk**: 🟢 Low

*   **Objective**: Eliminate `AttributeError: 'NoneType' object has no attribute 'foo'`.
*   **Action Items**:
    1.  Re-enable `strict_optional`.
    2.  Handle every `Optional[T]` with `if x is not None:` checks.
    3.  This is arguably the most valuable phase for stability.

---

## 🛠️ How to Work (Your Daily Workflow)

1.  **Pick a Category**: "Today I will fix `valid-type`."
2.  **Enable Check**: In `pyproject.toml`, remove `"valid-type"` from `disable_error_code`.
3.  **Run Check**: `uv run mypy .` -> See errors explode 💥.
4.  **Fix & Verify**: Fix the errors until `verify_all.bat` passes again.
5.  **Commit**: Lock in the improvement.

## ⚠️ Known High-Volume Issues

| File/Module | Primary Issue | Strategy |
| :--- | :--- | :--- |
| `ui/main_window.py` | `attr-defined` | Needs major cleanup. Variables are added dynamically via `setattr` or mixins. Define them in `__init__` or use Protocol. |
| `windows/base_window.py` | `call-overload` | Heavy use of Qt coordinate systems. Expect lots of `int()` casting fixes. |
| `ui/mixins/*.py` | `attr-defined` | Mixins assume `self` is a `QMainWindow`. Use `typing.Protocol` to tell Mypy what `self` expects. |

---

### Start Recommendation

I recommend starting with **Phase 1 (Syntax Cleanup)**. It's safe, fast, and satisfying.
Do you want me to proceed with Phase 1 now?
