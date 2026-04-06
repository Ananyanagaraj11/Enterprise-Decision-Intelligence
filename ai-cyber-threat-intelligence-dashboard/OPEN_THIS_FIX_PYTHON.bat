@echo off
title Fix Python - then run backend
cd /d "%~dp0"

echo.
echo ============================================================
echo   WINDOWS IS BLOCKING "python" - THAT IS WHY YOU SEE THE ERROR
echo ============================================================
echo.
echo I am opening 2 things for you:
echo   1. Windows Settings (Apps - then click "Manage app execution aliases")
echo   2. Python download page
echo.
echo DO THIS NOW:
echo   1. In Settings: Turn OFF "python.exe" and "python3.exe" (App Installer)
echo   2. On python.org: Download Python, run installer, CHECK "Add to PATH"
echo   3. CLOSE THIS WINDOW and open a NEW terminal
echo   4. Run:  python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
echo.
echo ============================================================
echo.

start "" "ms-settings:appsfeatures"
timeout /t 2 /nobreak >nul
start "" "https://www.python.org/downloads/"

echo Press any key after you turned OFF the two aliases and installed Python...
pause >nul
