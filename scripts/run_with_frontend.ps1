# Start backend API + dashboard UI (two new PowerShell windows)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
}
if (-not (Test-Path "$root\dashboard-ui\.env.local")) {
    Copy-Item "$root\dashboard-ui\.env.local.example" "$root\dashboard-ui\.env.local"
}
if (-not (Test-Path "$root\dashboard-ui\node_modules")) {
    Push-Location "$root\dashboard-ui"
    npm install
    Pop-Location
}

Write-Host "Starting backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root'; uvicorn backend_core.main:app --host 127.0.0.1 --port 8000 --reload"
)

Start-Sleep -Seconds 3

Write-Host "Starting dashboard on http://localhost:3000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\dashboard-ui'; npm run dev -- -p 3000"
)

Write-Host ""
Write-Host "Open: http://localhost:3000" -ForegroundColor Green
Write-Host "API:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Optional live data: python -m edge_ai (separate terminal)" -ForegroundColor Yellow
