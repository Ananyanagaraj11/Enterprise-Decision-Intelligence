@echo off
cd /d "%~dp0\.."
echo Starting FastAPI backend on http://localhost:8000
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
) else if exist python_portable\python.exe (
    python_portable\python.exe -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
) else (
    python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
    if errorlevel 1 py -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
)
pause
