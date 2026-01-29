@echo off
echo ========================================================
echo  RUNNING STRESS ^& CHAOS TESTS
echo ========================================================

call .venv314\Scripts\activate.bat

echo.
echo [1/1] Running Stress Tests (pytest tests/test_stress)...
python -m pytest tests/test_stress
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] STRESS TESTS FAILED!
    exit /b 1
)

echo.
echo [2/2] Running Chaos Experiments (pytest tests/test_chaos)...
python -m pytest tests/test_chaos
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] CHAOS TESTS FAILED!
    exit /b 1
)

echo.
echo ========================================================
echo  ALL STRESS ^& CHAOS CHECKS PASSED!
echo ========================================================
