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
    verify_all.bat
    ```
    This script runs:
    *   **Ruff**: Linter and formatter.
    *   **UI Audit**: Checks for unsafe references.
    *   **Pytest**: Runs all unit and interactive tests (30+ tests).

2.  **Strict Typing**
    *   All new code must have type hints.
    *   Avoid `Any` where possible.
    *   Use `TYPE_CHECKING` imports to prevent circular references.

3.  **Interactive Tests**
    *   When adding UI features, add a test in `tests/test_interactive/`.
    *   Mock dialogs (`QFileDialog`, `QMessageBox`) to ensure automation capability.

## 📝 Coding Standards

*   **Language**: Python 3.14+ features allowed (except in build scripts restricted to 3.13).
*   **Style**: Follow PEP 8 (enforced by Ruff).
*   **Docstrings**: Google Style docstrings are required for all public methods.
*   **Internationalization**: All user-facing text must use `tr("key")` and be defined in `utils/locales/`.

## 🌍 Environment Setup

We use a **Dual Environment Strategy** to balance latest features and build compatibility:

| Environment | Directory | Python Ver | Purpose | Executable |
|---|---|---|---|---|
| **Development** | `.venv314` | **3.14** | Coding, Testing, Debugging | `.venv314\Scripts\python.exe` |
| **Build** | `.venv313` | **3.13** | Nuitka Compilation, Release | `.venv313\Scripts\python.exe` |

### Setup Instructions

1.  **Configure VSCode**: Set your workspace interpreter to `.venv314`.
2.  **Coding**: Use Python 3.14 features freely (except where noted).
3.  **Building**: Run `build_release.py` (automatically enforces 3.13).

## 🚧 Known Issues

*   **Nuitka Build**: Requires Python 3.13. Do not attempt to build with 3.14 yet.
*   **Agent Workflows**: Always verify which environment the agent is using. Use `run_tests` workflow to enforce `.venv314`.
