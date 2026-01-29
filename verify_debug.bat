@echo off
setlocal
chcp 65001 >nul

set VENV_PYTHON=.venv314\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual Environment .venv314 not found!
    exit /b 1
)

echo ========================================================
echo  FTIV DEBUG VERIFICATION (Crash Detection)
echo ========================================================

rem Enable stress test mode or debug flags if needed
set FTIV_TEST_MODE=1
set PYTHONFAULTHANDLER=1
set PYTHONUNBUFFERED=1

rem Create logs directory if not exists
if not exist logs mkdir logs

echo [DEBUG] Running Tests with faulthandler...
echo [DEBUG] Output redirected to logs/test_execution.log

"%VENV_PYTHON%" -X faulthandler -m pytest -v -s > logs/test_execution.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Tests failed or crashed. Check logs/test_execution.log
    echo.
    echo --- Last 20 lines of log ---
    powershell -command "Get-Content logs/test_execution.log -Tail 20"
    exit /b 1
)

echo.
echo [SUCCESS] Debug verification passed.
endlocal
