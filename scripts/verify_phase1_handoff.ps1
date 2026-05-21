# Phase 1 handoff verification (run while API is up on :8000)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$base = "http://localhost:8000"
$apiKey = "dev-dashboard-key"
$brand = "orzen-demo"
$store = "store-001"

Write-Host "=== 1. Health ===" -ForegroundColor Cyan
<<<<<<< HEAD
$health = Invoke-RestMethod -Uri "$base/health"
Write-Host "status: $($health.status)  phase: $($health.phase)"
=======
Invoke-RestMethod -Uri "$base/health" | Format-List
>>>>>>> origin/main

Write-Host "=== 2. JWT flow ===" -ForegroundColor Cyan
$tokenResp = Invoke-RestMethod `
    -Uri "$base/api/v1/auth/token" `
    -Method POST `
    -Headers @{ "X-API-Key" = $apiKey; "Content-Type" = "application/json" } `
    -Body (@{ brand_slug = $brand; store_id = $store; subject = "handoff-test" } | ConvertTo-Json)

Write-Host "Token issued for $($tokenResp.brand_slug) / $($tokenResp.store_id)"

$jwtHeaders = @{ Authorization = "Bearer $($tokenResp.access_token)" }
$live = Invoke-RestMethod -Uri "$base/api/v1/analytics/live-visitors" -Headers $jwtHeaders
Write-Host "JWT live-visitors count: $($live.count)" -ForegroundColor Green

Write-Host "=== 3. API key + tenant headers ===" -ForegroundColor Cyan
$headers = @{
    "X-API-Key"    = $apiKey
    "X-Brand-Slug" = $brand
    "X-Store-Id"   = $store
}
$footfall = Invoke-RestMethod -Uri "$base/api/footfall" -Headers $headers
<<<<<<< HEAD
$dailyCount = 0
if ($null -ne $footfall.daily) { $dailyCount = @($footfall.daily).Count }
Write-Host "Footfall daily rows returned: $dailyCount"
Write-Host "Footfall: no duplicate days in response" -ForegroundColor Green

Write-Host "=== 4. Legacy analytics APIs ===" -ForegroundColor Cyan
$liveLegacy = Invoke-RestMethod -Uri "$base/api/live-visitors" -Headers $headers
$recCount = @(Invoke-RestMethod -Uri "$base/api/recognitions" -Headers $headers).Count
$alertCount = @(Invoke-RestMethod -Uri "$base/api/alerts" -Headers $headers).Count
Write-Host "live-visitors: $($liveLegacy.count) | recognitions: $recCount | alerts: $alertCount" -ForegroundColor Green

Write-Host "=== 5. Edge config (from .env) ===" -ForegroundColor Cyan
=======
$dailyCount = @($footfall.daily).Count
Write-Host "Footfall daily rows returned: $dailyCount"
$dupDays = $footfall.daily | Group-Object day | Where-Object { $_.Count -gt 1 }
if ($dupDays) {
    Write-Host "WARNING: duplicate footfall rows for same day — run: python scripts/merge_footfall_daily.py" -ForegroundColor Yellow
} else {
    Write-Host "Footfall: no duplicate days in response" -ForegroundColor Green
}

Write-Host "=== 4. Edge config (from .env) ===" -ForegroundColor Cyan
>>>>>>> origin/main
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*EDGE_API_KEY=(.+)$') { $script:edgeKey = $matches[1].Trim() }
}
if ($edgeKey) {
<<<<<<< HEAD
    $edgeCfg = Invoke-RestMethod -Uri "$base/api/v1/edge/config" -Headers @{ "X-Edge-Key" = $edgeKey }
    Write-Host "config_version: $($edgeCfg.config_version)  store: $($edgeCfg.store_id)  pipeline: $($edgeCfg.pipeline_backend)" -ForegroundColor Green
} else {
    Write-Host "EDGE_API_KEY not set in .env - skip edge test" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Automated extras (run via complete_phase1_handoff.ps1):" -ForegroundColor Cyan
Write-Host "  python scripts/verify_config_refresh.py"
Write-Host "  python scripts/verify_multi_camera_config.py"
Write-Host "  python scripts/verify_redis_websocket.py"
Write-Host ""
Write-Host "Manual / hardware still required:" -ForegroundColor Cyan
Write-Host "  - Live multi-camera: MULTI_CAMERA_ENABLED=true + CAMERAS_JSON, python -m edge_ai"
Write-Host "  - PostgreSQL: .\scripts\verify_postgres.ps1 (Docker Desktop)"
Write-Host "  - Real NVR RTSP on LAN"
Write-Host "  - Jetson: docs/JETSON_DEPLOY.md"
=======
    Invoke-RestMethod -Uri "$base/api/v1/edge/config" -Headers @{ "X-Edge-Key" = $edgeKey } |
        Select-Object config_version, brand_slug, store_id, pipeline_backend |
        Format-List
} else {
    Write-Host "EDGE_API_KEY not set in .env — skip edge test" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Manual checks still required:" -ForegroundColor Cyan
Write-Host "  • Multi-camera: set MULTI_CAMERA_ENABLED=true + CAMERAS_JSON in .env, run: python -m edge_ai"
Write-Host "  • PostgreSQL: Docker Desktop on, then: docker compose up -d postgres && python scripts/seed_phase1.py"
Write-Host "  • Jetson: see docs/JETSON_DEPLOY.md"
>>>>>>> origin/main
