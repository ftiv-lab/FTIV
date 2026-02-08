# Contributing to FTIV

Thank you for your interest in contributing to FTIV!
Please follow these guidelines to ensure consistency and quality.

## 📐 Architecture Overview

*   **MainController Pattern**: All business logic and state management are handled by `MainController` (`ui/controllers/main_controller.py`). The `MainWindow` is strictly for View logic.
*   **Action Controllers**: Specific domains (Text, Image, Layout) have dedicated controllers in `ui/controllers/`.
*   **Managers**: `WindowManager`, `FileManager`, etc., handle backend logic and resource management.

## 🧪 Testing Strategy

We maintain a high standard of reliability. Before submitting changes:

1.  **Run One-Click Verification**
    ```powershell
    .\verify_all.bat
    ```
    This script runs:
    *   **Ruff**: Linter and formatter.
    *   **Mypy**: Static type checker (Strict Mode).
    *   **UI Audit**: Checks for unsafe references.
    *   **Pytest**: Runs all configured test suites (core / interactive / chaos / stress).
    *   **Latest Metrics**: Test count and coverage snapshots are tracked in `docs/internal/guides/MEMORY.md`.

2.  **Strict Typing (Mypy)**
    *   **Zero Errors Policy**: The CI (and `verify_all.bat`) will fail on a single Mypy error.
    *   `check_untyped_defs = True` is enabled.
    *   `strict_optional = True` is enabled.
    *   Use `TYPE_CHECKING` imports to prevent circular references.

3.  **Interactive Tests**
    *   When adding UI features, add a test in `tests/test_interactive/`.
    *   Mock dialogs (`QFileDialog`, `QMessageBox`) to ensure automation capability.

## 📝 Coding Standards

*   **Language**: Python 3.14+ features allowed (except in build scripts restricted to 3.13).
*   **Style**: Follow PEP 8 (enforced by Ruff).
*   **Docstrings**: Google Style docstrings are required for all public methods.
*   **Internationalization**: All user-facing text must use `tr("key")` and be defined in `utils/locales/`.

## 🐛 Debugging & Troubleshooting

If `verify_all.bat` fails, use these steps to rapidly identify the root cause:

1.  **Fail Fast & Verbose**:
    *   The script is configured with `--maxfail=1 --showlocals -v`.
    *   It stops at the **first error**. Scroll to the bottom of the log to see the "Traceback".
    *   `--showlocals` displays the values of variables at the time of the crash. Check these first!

2.  **Isolate the Test**:
    *   Don't keep running the full suite. Run only the failing test file:
        ```powershell
        # Example: If tests/test_main_controller.py failed
        uv run pytest tests/test_main_controller.py
        ```

3.  **UI Reference Errors**:
    *   If `check_ui_refs.py` fails, it means you are accessing a widget blindly (e.g., `self.mw.some_button`).
    *   **Fix**: Use the explicit path (e.g., `self.mw.text_tab.some_button`) or check if it exists in `__init__`.

## 🌍 Environment Setup (Modern Stack)

We use **uv** for blazing fast, reliable dependency management.

### Setup Instructions

1.  **Install uv**
    ```powershell
    pip install uv
    ```
2.  **Install Dependencies**
    ```powershell
    uv sync
    ```
3.  **Install Pre-commit Hooks**
    ```powershell
    uv run pre-commit install
    ```

### Development Workflow

*   **Running the App**:
    ```powershell
    uv run main.py
    ```
*   **Running Tests**:
    ```powershell
    uv run pytest
    ```
*   **Verification**:
    ```powershell
    .\verify_all.bat
    ```
*   **Reset Defaults (Factory Settings)**:
    ```powershell
    uv run scripts/reset_defaults.py
    ```

### Dual Environment Strategy (Legacy Build)

| Environment | Directory | Python Ver | Purpose |
|---|---|---|---|
| **Development** | `.venv` (Managed by uv) | **3.12+** | Coding, Testing, Debugging |
| **Build** | `.venv313` | **3.13** | Nuitka Compilation, Release |

> **Note**: For Nuitka builds, we still use a dedicated 3.13 environment (`.venv313`) for compatibility.

## 🚧 Known Issues

*   **Nuitka Build**: Requires Python 3.13. Do not attempt to build with 3.14 yet.
*   **Agent Workflows**: Always verify which environment the agent is using. Use `run_tests` workflow to enforce `.venv314`.
