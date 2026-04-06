@echo off
cd /d "%~dp0"

REM Try to run with real Python (works after you install from python.org and turn off Store aliases)
py -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 2>nul
if %errorlevel% equ 0 goto :done

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 2>nul
if %errorlevel% equ 0 goto :done

echo.
echo Python was not found. What is wrong:
echo  - Windows is using the "Microsoft Store" stub instead of real Python.
echo  - You need to install Python and turn off the Store alias.
echo.
echo Do this (see FIX_PYTHON.md for full steps):
echo  1. Win key, type: Manage app execution aliases - open it
echo  2. Turn OFF: python.exe and python3.exe (App Installer)
echo  3. Install Python from https://www.python.org/downloads/
echo     - CHECK "Add python.exe to PATH"
echo  4. Close this window, open a NEW terminal, run: run_backend.bat
echo.
echo Opening FIX_PYTHON.md and python.org...
start "" "%~dp0FIX_PYTHON.md"
start "" "https://www.python.org/downloads/"
pause

:done
