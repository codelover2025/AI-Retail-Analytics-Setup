# PostgreSQL smoke test — requires Docker Desktop
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== PostgreSQL smoke test ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "SKIP: docker not in PATH" -ForegroundColor Yellow
    exit 0
}

docker compose up -d postgres
Start-Sleep -Seconds 8

$envBackup = Get-Content .env -Raw
$pgUrl = "postgresql+psycopg2://retail:retail@localhost:5432/retail_analytics"
if ($envBackup -match "DATABASE_URL=.*") {
    $newEnv = $envBackup -replace "DATABASE_URL=.*", "DATABASE_URL=$pgUrl"
} else {
    $newEnv = $envBackup + "`nDATABASE_URL=$pgUrl`n"
}
Set-Content -Path .env.pgtest -Value $newEnv -NoNewline

$env:DATABASE_URL = $pgUrl
python scripts/seed_phase1.py
python scripts/merge_footfall_daily.py

$health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
if ($health.status -eq "ok") {
    Write-Host "PASS: API health ok (restart uvicorn with Postgres DATABASE_URL for full test)" -ForegroundColor Green
} else {
    Write-Host "Start API with Postgres URL in .env, then re-run verify_phase1_handoff.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To switch permanently, in .env comment SQLite and set:" -ForegroundColor Cyan
Write-Host "  DATABASE_URL=$pgUrl"
