@echo off
setlocal
chcp 65001 >nul

set VENV_PYTHON=.venv314\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual Environment .venv314 not found!
    echo Please make sure you are in the correct directory.
    pause
    exit /b 1
)

echo ========================================================
echo  Antigravity One-Click Verification (Python 3.14.2)
echo ========================================================

echo.
echo [1/6] Running Ruff Linter...
"%VENV_PYTHON%" -m ruff check .
if %errorlevel% neq 0 (
    echo [ERROR] Ruff found issues.
    goto :FAIL
)

echo.
echo [2/6] Running UI Reference Audit...
"%VENV_PYTHON%" tools/check_ui_refs.py
if %errorlevel% neq 0 (
    echo [ERROR] UI Reference Audit failed.
    goto :FAIL
)


echo.
echo [3/6] Running Tests: Group 1 (Core Logic)...
"%VENV_PYTHON%" -m pytest tests/ -k "not mindmap and not interactive and not chaos and not stress"
if %errorlevel% neq 0 (
    echo [ERROR] Core Tests failed.
    goto :FAIL
)

echo.
echo [4/6] Running Tests: Group 2 (MindMap)...
"%VENV_PYTHON%" -m pytest tests/mindmap/ tests/ -k "mindmap"
if %errorlevel% neq 0 (
    echo [ERROR] MindMap Tests failed.
    goto :FAIL
)

echo.
echo [5/6] Running Tests: Group 3 (Interactive)...
"%VENV_PYTHON%" -m pytest tests/test_interactive/
if %errorlevel% neq 0 (
    echo [ERROR] Interactive Tests failed.
    goto :FAIL
)

echo.
echo [6/6] Running Tests: Group 4 (Chaos and Stress)...
"%VENV_PYTHON%" -m pytest tests/test_chaos/ tests/test_stress/
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
