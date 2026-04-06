@echo off
REM Run from project root: scripts\copy_artifacts.bat
cd /d "%~dp0\.."
if not exist "training\outputs\model.pt" (
    echo No training/outputs/model.pt found. Train first: python training/train.py --data path/to/data.csv --out-dir training/outputs
    exit /b 1
)
if not exist "backend\artifacts" mkdir "backend\artifacts"
copy /Y "training\outputs\model.pt" "backend\artifacts\"
copy /Y "training\outputs\scaler.joblib" "backend\artifacts\"
copy /Y "training\outputs\classes.pt" "backend\artifacts\"
if exist "training\outputs\feature_names.txt" copy /Y "training\outputs\feature_names.txt" "backend\artifacts\"
echo Artifacts copied to backend\artifacts
