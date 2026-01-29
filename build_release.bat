@echo off
setlocal
chcp 65001 >nul

echo.
echo ========================================================
echo  FTIV Release Build (Python 3.13 + Nuitka)
echo ========================================================

set VENV_PYTHON=.venv313\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual Environment .venv313 not found!
    echo Please ensure .venv313 exists and has Nuitka installed.
    pause
    exit /b 1
)

echo.
echo [1/1] Running build_release.py...
"%VENV_PYTHON%" build_release.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build Failed!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  BUILD SUCCESSFUL!
echo  Check the 'dist' folder for the release package.
echo ========================================================
pause
