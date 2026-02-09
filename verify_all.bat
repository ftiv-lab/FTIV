@echo off
setlocal
chcp 65001 >nul

set "COV_FAIL_UNDER=35"
if not "%FTIV_COV_FAIL_UNDER%"=="" set "COV_FAIL_UNDER=%FTIV_COV_FAIL_UNDER%"

echo ========================================================
echo  Antigravity Verification (Powered by UV)
echo ========================================================
echo Coverage Gate: %COV_FAIL_UNDER% percent
echo Coverage Override: set FTIV_COV_FAIL_UNDER
echo Coverage Scope: ui, managers, windows, models, utils

echo.
echo [1/7] Running Ruff Linter...
uv run ruff check .
if %errorlevel% neq 0 (
    echo [ERROR] Ruff found issues.
    goto :FAIL
)

echo.
echo [2/7] Running UI Reference Audit...
uv run tools/check_ui_refs.py
if %errorlevel% neq 0 (
    echo [ERROR] UI Reference Audit failed.
    goto :FAIL
)


echo.
echo [3/7] Running Type Checks (Mypy)...
uv run mypy ui managers windows models
if %errorlevel% neq 0 (
    echo [ERROR] Mypy found type errors.
    goto :FAIL
)


echo.
echo [4/7] Running Tests: Group 1 (Core Logic with Coverage)...
uv run pytest tests/ -k "not interactive and not chaos and not stress and not inline" --cov=ui --cov=managers --cov=windows --cov=models --cov=utils --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=%COV_FAIL_UNDER% --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Core Tests failed or coverage below %COV_FAIL_UNDER%%.
    goto :FAIL
)

echo.
echo [5/7] Running Tests: Group 2 (Inline Editing)...
uv run pytest tests/test_inline_edit.py --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Inline Editing Tests failed.
    goto :FAIL
)

echo.
echo [6/7] Running Tests: Group 3 (Interactive)...
uv run pytest tests/test_interactive/ --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Interactive Tests failed.
    goto :FAIL
)

echo.
echo [7/7] Running Tests: Group 4 (Chaos and Stress)...
uv run pytest tests/test_chaos/ tests/test_stress/ --maxfail=1 --showlocals -v
if %errorlevel% neq 0 (
    echo [ERROR] Chaos/Stress Tests failed.
    goto :FAIL
)

echo.
echo ========================================================
echo  ALL CHECKS PASSED! READY FOR DEPLOY.
echo  Coverage Reports: htmlcov/index.html, coverage.xml
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
