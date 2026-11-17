# StegaShield - Unified Development Environment Launcher (PowerShell)
# Usage: .\scripts\dev.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  StegaShield Dev Launcher (Windows)      " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$ROOT_DIR = Resolve-Path "$PSScriptRoot\.."
$BACKEND_DIR = "$ROOT_DIR\backend"
$FRONTEND_DIR = "$ROOT_DIR\frontend"

# Check Python environment
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.12+ is required but not found in PATH."
    exit 1
}

# Check Node environment
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js (v18+) and npm are required but not found in PATH."
    exit 1
}

Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $BACKEND_DIR -PassThru

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
$FrontendProcess = Start-Process npm -ArgumentList "run dev" -WorkingDirectory $FRONTEND_DIR -PassThru

Write-Host "`nStegaShield is running!" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop both processes.`n" -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping StegaShield services..." -ForegroundColor Red
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-Process -Id $BackendProcess.Id -Force }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-Process -Id $FrontendProcess.Id -Force }
    Write-Host "Done." -ForegroundColor Gray
}
