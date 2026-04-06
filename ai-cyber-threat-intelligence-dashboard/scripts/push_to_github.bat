@echo off
cd /d "%~dp0\.."
echo.
echo ===== Push to GitHub =====
echo.

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. Please install Git or use GitHub Desktop.
    echo.
    echo Option 1: Install Git from https://git-scm.com/download/win
    echo Option 2: Use GitHub Desktop from https://desktop.github.com/
    echo.
    pause
    exit /b 1
)

echo Git found. Initializing repository...
if not exist .git (
    git init
    echo Repository initialized.
)

echo.
echo Adding all files...
git add .

echo.
echo Creating commit...
git commit -m "Complete AI Cyber Threat Intelligence Dashboard - ML model, FastAPI backend, interactive dashboard, CSV analysis, deployment configs"

echo.
echo Setting main branch...
git branch -M main

echo.
echo Adding remote (if not exists)...
git remote remove origin 2>nul
git remote add origin https://github.com/Ananyanagaraj11/ai-cyber-threat-dashboard.git

echo.
echo ===== Ready to Push =====
echo.
echo Run this command to push (you'll need to enter your GitHub credentials):
echo   git push -u origin main
echo.
echo Or use GitHub Desktop: File -^> Add Local Repository -^> Choose this folder -^> Push
echo.
pause
