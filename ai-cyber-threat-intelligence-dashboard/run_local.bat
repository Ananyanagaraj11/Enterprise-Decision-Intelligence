@echo off
cd /d "%~dp0"
echo Starting backend (serves frontend on port 8000)...
echo.
py -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 2>nul || python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
if errorlevel 1 (
    echo.
    echo Python not found. Do this first:
    echo 1. Settings - Apps - App execution aliases - Turn OFF "python.exe" and "python3.exe"
    echo 2. Install Python from https://www.python.org/downloads/ - check "Add to PATH"
    echo 3. Close this window, open a new terminal, run: run_local.bat
    pause
)
