@echo off
cd /d "%~dp0\.."
echo.
echo ===== GitHub Setup =====
echo.
echo This will initialize git and prepare for GitHub push.
echo.
set /p GITHUB_USER="Enter your GitHub username: "
set /p REPO_NAME="Enter your repo name (e.g. ai-cyber-threat-dashboard): "
echo.
echo Initializing git...
git init
git add .
git commit -m "Initial commit: AI Cyber Threat Intelligence Dashboard"
git branch -M main
echo.
echo Adding remote: https://github.com/%GITHUB_USER%/%REPO_NAME%.git
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo.
echo Ready to push! Run:
echo   git push -u origin main
echo.
echo Then follow DEPLOY.md to deploy to Vercel + Render.
echo.
pause
