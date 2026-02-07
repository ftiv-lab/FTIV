@echo off
setlocal
chcp 65001 >nul

echo ========================================================
echo  Antigravity One-Click Verification (Powered by UV)
echo ========================================================

echo.
echo [1/6] Running Ruff Linter...
echo [1/6] Running Ruff Linter...
uv run ruff check .
if %errorlevel% neq 0 (
    echo [ERROR] Ruff found issues.
    goto :FAIL
)

echo.
echo [2/6] Running UI Reference Audit...
echo [2/6] Running UI Reference Audit...
uv run tools/check_ui_refs.py
if %errorlevel% neq 0 (
    echo [ERROR] UI Reference Audit failed.
    goto :FAIL
)


echo.
echo [3/6] Running Type Checks (Mypy)...
uv run mypy ui managers windows models
if %errorlevel% neq 0 (
    echo [ERROR] Mypy found type errors.
    goto :FAIL
)


echo.
echo [4/6] Running Tests: Group 1 (Core Logic)...
echo [3/6] Running Tests: Group 1 (Core Logic)...
echo [3/6] Running Tests: Group 1 (Core Logic)...
uv run pytest tests/ -k "not interactive and not chaos and not stress and not inline" --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Core Tests failed.
    goto :FAIL
)

echo.
echo [4/6] Running Tests: Group 2 (Inline Editing)...
uv run python -m pytest tests/test_inline_edit.py --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Inline Editing Tests failed.
    goto :FAIL
)

echo.
echo [5/6] Running Tests: Group 3 (Interactive)...
uv run python -m pytest tests/test_interactive/ --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Interactive Tests failed.
    goto :FAIL
)

echo.
echo [6/6] Running Tests: Group 4 (Chaos and Stress)...
uv run python -m pytest tests/test_chaos/ tests/test_stress/ --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Chaos/Stress Tests failed.
    goto :FAIL
)

echo.
echo ========================================================
echo  ALL CHECKS PASSED! READY FOR DEPLOY.
echo ========================================================
exit /b 0

:FAIL
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo  VERIFICATION FAILED. DO NOT COMMIT.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REM Play a beep sound
echo 
exit /b 1
