@echo off
cd /d "%~dp0\.."
if "%~1"=="" (
    echo Usage: scripts\run_train.bat path\to\data.csv
    echo Example: scripts\run_train.bat data\UNSW_NB15_traintest.csv
    pause
    exit /b 1
)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python training/train.py --data "%~1" --out-dir training/outputs --epochs 50
) else if exist python_portable\python.exe (
    python_portable\python.exe training/train.py --data "%~1" --out-dir training/outputs --epochs 50
) else (
    python training/train.py --data "%~1" --out-dir training/outputs --epochs 50
)
pause
