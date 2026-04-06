@echo off
cd /d "%~dp0\.."
echo.
echo ===== LIVE DEMO =====
echo Starting backend on port 8000 (dashboard at http://localhost:8000)...
echo.

start "Cyber-Threat-Backend" cmd /c "cd /d "%~dp0\.." && (if exist python_portable\python.exe (python_portable\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000) else (python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000)) & pause"

timeout /t 4 /nobreak >nul

where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ngrok not found. Install from https://ngrok.com/download
    echo.
    echo Your LOCAL demo URL:  http://localhost:8000
    echo Open it in the browser to use the app.
    echo.
    pause
    exit /b 0
)

echo.
echo Creating public LIVE DEMO URL (ngrok)...
echo Share the HTTPS URL below - anyone can open it.
echo.
ngrok http 8000
