@echo off
cd /d "%~dp0\.."
echo Installing portable Python into this project (no system install needed)...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install_portable_python.ps1"
echo.
pause
