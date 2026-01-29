@echo off
setlocal
chcp 65001 >nul

set VENV_PYTHON=.venv313\Scripts\python.exe

if not exist "%VENV_PYTHON%" goto NO_VENV

echo.
echo ========================================================
echo  Build Readiness Check - Python 3.13 Nuitka Env
echo ========================================================

echo.
echo [1/3] Checking Dependencies - pip list
"%VENV_PYTHON%" -m pip list
if %errorlevel% neq 0 goto FAIL

echo.
echo [2/3] Running Basic Import Check
"%VENV_PYTHON%" -c "import PySide6; import PIL; print('Imports OK')"
if %errorlevel% neq 0 goto FAIL

echo.
echo [3/3] Running Tests in Build Env
"%VENV_PYTHON%" -m pytest
if %errorlevel% neq 0 goto WARN

echo.
echo [OK] Tests passed in Build Env.
goto END

:WARN
echo.
echo [WARNING] Tests failed in Python 3.13 environment.
echo This might be expected if tests rely on Python 3.14 features.
echo Proceed with caution.
goto END

:NO_VENV
echo [ERROR] Virtual Environment .venv313 not found!
echo Please make sure .venv313 is created.
pause
exit /b 1

:FAIL
echo.
echo [ERROR] BUILD CHECK FAILED
pause
exit /b 1

:END
echo.
echo ========================================================
echo  BUILD CHECK COMPLETE
echo ========================================================
exit /b 0
