@echo off
cd /d "%~dp0\.."
echo Project folder: %CD%
echo.

REM Use python if available, else py (Python Launcher)
set PY=python
where python >nul 2>nul
if errorlevel 1 (
    set PY=py
    where py >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python is not installed or not on PATH.
        echo.
        echo EASIEST FIX - use portable Python (no system install):
        echo   Run:  scripts\install_portable_python.bat
        echo   Then use run_backend.bat and run_dashboard.bat.
        echo.
        echo Or install Python from https://www.python.org/downloads/
        echo   Check "Add python.exe to PATH". See INSTALL_PYTHON.md
        pause
        exit /b 1
    )
)

echo Using: %PY%
echo.

if exist venv\Scripts\activate.bat (
    echo Activating existing venv...
    call venv\Scripts\activate.bat
) else (
    echo Creating venv...
    %PY% -m venv venv
    if errorlevel 1 (
        echo Failed to create venv.
        echo Run instead: scripts\install_portable_python.bat  (no system Python needed)
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
)

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    python -m pip install -r requirements.txt
)
echo.
echo Setup done. To run later: venv\Scripts\activate then use run_backend.bat / run_dashboard.bat
pause
