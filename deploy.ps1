# Goethe Booking Bot - Deploy Script
# Run this in PowerShell to deploy to GitHub + Railway + Netlify

param(
    [string]$GitHubRepo = "goethe-booking-bot",
    [string]$GitHubUser = ""
)

$projectDir = "C:\Users\brosp\Downloads\goethe-bot"
cd $projectDir

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "     GOETHE BOOKING BOT - DEPLOYMENT          " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. GitHub ──
Write-Host "── Step 1: GitHub ──────────────────────────" -ForegroundColor Yellow
Write-Host ""

# Check if git is installed
try { git --version | Out-Null; Write-Host "✓ Git found" -ForegroundColor Green }
catch { Write-Host "✗ Git not found! Install from https://git-scm.com/download/win" -ForegroundColor Red; pause; exit }

# Init repo
if (Test-Path ".git") {
    Write-Host "✓ Git repo already initialized" -ForegroundColor Green
} else {
    git init
    git add -A
    git commit -m "Initial commit - Goethe Booking Bot"
    Write-Host "✓ Git repo initialized" -ForegroundColor Green
}

Write-Host ""
Write-Host "Now create a GitHub repository:"
Write-Host "  1. Go to https://github.com/new" -ForegroundColor White
Write-Host "  2. Repo name: $GitHubRepo (or any name)" -ForegroundColor White
Write-Host "  3. Make it Public (free)" -ForegroundColor White
Write-Host "  4. Do NOT initialize with README (we already have one)" -ForegroundColor White
Write-Host "  5. Click 'Create repository'" -ForegroundColor White
Write-Host ""
$createNow = Read-Host "Have you created the GitHub repo? (y/n)"

if ($createNow -eq "y") {
    if (-not $GitHubUser) { $GitHubUser = Read-Host "Enter your GitHub username" }
    $remoteUrl = "https://github.com/$GitHubUser/$GitHubRepo.git"
    git remote add origin $remoteUrl 2>$null
    git branch -M main
    git push -u origin main
    Write-Host "✓ Code pushed to GitHub!" -ForegroundColor Green
}

Write-Host ""
Write-Host "── Step 2: Backend → Railway.app (Free) ─────" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Go to https://railway.app" -ForegroundColor White
Write-Host "  2. Sign in with GitHub" -ForegroundColor White
Write-Host "  3. Click 'New Project' → 'Deploy from GitHub'" -ForegroundColor White
Write-Host "  4. Select your repo: $GitHubUser/$GitHubRepo" -ForegroundColor White
Write-Host "  5. Railway auto-detects Dockerfile → builds automatically" -ForegroundColor White
Write-Host "  6. Wait 3-5 min for build" -ForegroundColor White
Write-Host "  7. Click 'Generate Domain' to get URL" -ForegroundColor White
Write-Host ""
Write-Host "  Your backend URL will be:" -ForegroundColor Cyan
Write-Host "  https://goethe-booking-bot.up.railway.app" -ForegroundColor Green
Write-Host ""

$gotRailwayUrl = Read-Host "Did you get the Railway URL? (y/n)"

if ($gotRailwayUrl -eq "y") {
    $railwayUrl = Read-Host "Paste your Railway URL (e.g., https://xxx.up.railway.app)"
    Write-Host ""
    Write-Host "── Step 3: Frontend → Netlify (Free) ───────" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Go to https://app.netlify.com/drop" -ForegroundColor White
    Write-Host "  2. Drag the 'frontend' folder onto the page:" -ForegroundColor White
    Write-Host "     $projectDir\frontend" -ForegroundColor Cyan
    Write-Host "  3. Netlify deploys instantly" -ForegroundColor White
    Write-Host "  4. Open your Netlify URL" -ForegroundColor White
    Write-Host "  5. Enter your backend URL in the input box:" -ForegroundColor White
    Write-Host "     $railwayUrl" -ForegroundColor Green
    Write-Host "  6. Click 'Connect'" -ForegroundColor White
    Write-Host "  7. Click 'Start Bot'" -ForegroundColor White
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Frontend: https://your-site.netlify.app" -ForegroundColor Green
    Write-Host "  Backend:  $railwayUrl" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "── Quick Alternative: ngrok (Instant Test) ──" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Run this in another PowerShell window:" -ForegroundColor White
    Write-Host "  powershell -File ngrok_setup.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Then open the Netlify frontend and enter" -ForegroundColor White
    Write-Host "  the ngrok URL as your backend." -ForegroundColor White
}

Write-Host ""
pause
