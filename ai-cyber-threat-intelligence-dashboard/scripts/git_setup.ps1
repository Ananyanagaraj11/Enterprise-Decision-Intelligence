# Git Setup Script for PowerShell
# Run this after installing Git: https://git-scm.com/download/win

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "`n===== Git Setup =====" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git not found. Install from: https://git-scm.com/download/win" -ForegroundColor Red
    Write-Host "Then run this script again." -ForegroundColor Yellow
    pause
    exit
}

# Initialize if needed
if (Test-Path .git) {
    Write-Host "Git already initialized" -ForegroundColor Yellow
} else {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
    Write-Host "Done" -ForegroundColor Green
}

# Add all files
Write-Host "`nAdding files..." -ForegroundColor Cyan
git add .
Write-Host "Done" -ForegroundColor Green

# Commit
Write-Host "`nCreating commit..." -ForegroundColor Cyan
git commit -m "AI Cyber Threat Intelligence Dashboard - Ready for deployment"
Write-Host "Done" -ForegroundColor Green

# Set main branch
Write-Host "`nSetting main branch..." -ForegroundColor Cyan
git branch -M main
Write-Host "Done" -ForegroundColor Green

Write-Host "`n===== Next Steps =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a repo on GitHub: https://github.com/new" -ForegroundColor Yellow
Write-Host "2. Copy the repo URL (e.g. https://github.com/YOUR_USERNAME/YOUR_REPO.git)" -ForegroundColor Yellow
Write-Host "3. Run these commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "4. Then follow DEPLOY.md to deploy to Vercel + Render" -ForegroundColor Yellow
Write-Host ""
pause
