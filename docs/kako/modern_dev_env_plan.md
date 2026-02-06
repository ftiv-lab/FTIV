# Modern Development Environment Improvement Plan (Super Senior Edition)

This document outlines a high-resolution plan to elevate the FTIV development environment to current industry "Super Senior" standards. The goal is **Speed, Reliability, and Automation**.

## 1. Executive Summary: The "Modern Stack"

We are moving from a **Traditional** stack to a **High-Performance** stack.

| Component | Current (Traditional) | **Target (Super Senior)** | Why? |
| :--- | :--- | :--- | :--- |
| **Package Manager** | `pip` + `venv` (manual) | **`uv` (Astral)** | 10-100x faster, unified workflow, deterministic builds. |
| **Linter/Formatter** | `ruff` (Already used) | `ruff` (Keep) | Industry standard. We will just tighten the rules. |
| **Type Checking** | None (Manual hints only) | **`mypy` (Strict Mode)** | Catches bugs that tests miss. "If it compiles, it runs." |
| **Automation** | `verify_all.bat` (Manual) | **`pre-commit` hooks** | Runs checks *automatically* when you try to git commit. |

---

## 2. Detailed Technical Proposal

### 2.1. Adopt `uv` (The "Game Changer")

`uv` is a Rust-based replacement for `pip`, `pip-tools`, and `virtualenv`. It is incredibly fast and simplifies dependency management.

**Benefits:**
*   **Speed**: Installing dependencies takes milliseconds.
*   **Virtual Env Management**: `uv venv` creates environments automatically.
*   **Script Running**: `uv run pytest` ensures commands run in the correct environment (no more `.venv314\Scripts\python` paths).
*   **Dependency Groups**: cleanly separate "App" libs (PySide6) from "Dev" libs (Ruff, Pytest).

**Proposed Change:**
Migrate `pyproject.toml` to use `[dependency-groups]`.

```toml
[project]
dependencies = [
    "PySide6>=6.8.0",
    # ...
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.9.0",
    "mypy>=1.0.0",
    "types-PySide6",  # Type stubs for QT
]
```

### 2.2. Enforce `mypy` (The "Safety Net")

Ruff checks syntax and style. `mypy` checks **logic and data types**.
Currently, `verify_all.bat` does not checking types. If you pass a `str` to a function expecting `int`, it crashes at runtime. `mypy` catches this at edit-time.

**Proposed Configuration (`pyproject.toml`):**
```toml
[tool.mypy]
files = ["ui", "managers", "windows", "models"]
ignore_missing_imports = true  # Practical first step
check_untyped_defs = true      # Check inside functions even if not typed
strict_optional = true         # Catch None errors
```

### 2.3. Automation via `pre-commit`

Human memory is unreliable. We forget to run `verify_all.bat`.
`pre-commit` installs a git hook that runs checks automatically when you type `git commit`.

**Workflow:**
1.  Dev makes changes.
2.  `git commit -m "feat: new thing"`
3.  **Automatically**:
    *   Ruff fixes imports.
    *   Ruff formats code.
    *   Mypy checks types.
4.  If fail -> Commit rejected.
5.  If pass -> Commit succeeds.

---

## 3. Implementation Roadmap

### Phase 1: The "UV" Migration (Foundation)
1.  **Install `uv`**: `pip install uv` (or winget).
2.  **Initialize**: Run `uv init` (re-generates modern `pyproject.toml`).
3.  **Add Deps**:
    *   `uv add PySide6 pillow python-osc`
    *   `uv add --dev ruff pytest mypy pre-commit types-PySide6`
4.  **Update Scripts**: Rewrite `verify_all.bat` to use `uv run verify_all.py` (simpler, cross-platform).

### Phase 2: The "Type Safety" Retrofit
1.  **Configure Mypy**: Add `[tool.mypy]` to `pyproject.toml`.
2.  **Baseline**: Run `uv run mypy .` and see the error count (likely high).
3.  **Triage**: Fix easy errors, suppress hard ones with `# type: ignore` to get to "Clean State".
4.  **Enforce**: Add `uv run mypy .` to `verify_all.bat`.

### Phase 3: The "Zero Friction" Workflow
1.  **Config**: Create `.pre-commit-config.yaml`.
2.  **Install**: Run `pre-commit install`.
3.  **Enjoy**: Commits are now safe by default.

---

## 4. Recommendation for FTIV

**Start with Phase 1 (UV Adoption) immediately.**
It requires minimal code changes but immediately improves the "Developer Experience" (install speed, command simplification).

**Phase 2 (Mypy)** is high value but requires time to fix existing typing errors. I recommend doing this iteratively (file by file).

**Phase 3** can be done anytime after Phase 1.
