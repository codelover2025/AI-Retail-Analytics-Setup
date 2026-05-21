# Run all automatable Phase 1 handoff checks
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== Phase 1 complete handoff ===" -ForegroundColor Cyan

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

New-Item -ItemType Directory -Force -Path data | Out-Null
python scripts/seed_phase1.py
python scripts/merge_footfall_daily.py
python scripts/rotate_edge_key.py
python scripts/seed_sample_alerts.py

$apiUp = $false
try {
    $h = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
    if ($h.status -eq "ok") { $apiUp = $true }
} catch {}

if (-not $apiUp) {
    Write-Host ""
    Write-Host "API not running on :8000 — start in another terminal:" -ForegroundColor Yellow
    Write-Host "  uvicorn backend_core.main:app --reload --port 8000"
    Write-Host ""
    Write-Host "Then re-run: .\scripts\complete_phase1_handoff.ps1"
    exit 1
}

.\scripts\verify_phase1_handoff.ps1
python scripts/verify_config_refresh.py
python scripts/verify_multi_camera_config.py
python scripts/verify_redis_websocket.py

Write-Host ""
Write-Host "Optional (Docker):" -ForegroundColor Cyan
Write-Host "  .\scripts\verify_postgres.ps1"
Write-Host "Manual (hardware):" -ForegroundColor Cyan
Write-Host "  Multi-camera live: MULTI_CAMERA_ENABLED=true in .env, python -m edge_ai"
Write-Host '  Jetson: docs/JETSON_DEPLOY.md'
