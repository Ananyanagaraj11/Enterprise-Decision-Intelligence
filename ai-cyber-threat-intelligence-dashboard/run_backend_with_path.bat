@echo off
cd /d "%~dp0"

set "PY="
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
)
if defined PY (
    echo Using: %PY%
    echo Starting backend...
    "%PY%" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
    goto :eof
)

echo.
echo No Python found in AppData\Local\Programs\Python.
echo.
echo 1. Install Python from https://www.python.org/downloads/
echo 2. In installer: CHECK "Add python.exe to PATH"
echo 3. Run this file again
echo.
start "" "https://www.python.org/downloads/"
pause
