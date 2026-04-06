@echo off
cd /d "%~dp0\.."
echo.
echo ===== Git Setup =====
echo.

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. Install from: https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b 1
)

git --version
echo.

if exist .git (
    echo Git already initialized
) else (
    echo Initializing git repository...
    git init
)

echo.
echo Adding files...
git add .
echo.

echo Creating commit...
git commit -m "AI Cyber Threat Intelligence Dashboard - Ready for deployment"
echo.

echo Setting main branch...
git branch -M main
echo.

echo ===== Next Steps =====
echo.
echo 1. Create a repo on GitHub: https://github.com/new
echo 2. Copy the repo URL (e.g. https://github.com/YOUR_USERNAME/YOUR_REPO.git)
echo 3. Run these commands:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
echo    git push -u origin main
echo.
echo 4. Then follow DEPLOY.md to deploy to Vercel + Render
echo.
pause
