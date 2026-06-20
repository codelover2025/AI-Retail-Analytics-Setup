# Phase 1 local setup (Windows) — SQLite, no Docker required
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example (SQLite mode)"
} elseif (-not (Select-String -Path .env -Pattern "sqlite" -Quiet)) {
    Write-Host "Tip: set DATABASE_URL=sqlite:///./data/orzen_dev.db in .env if Postgres is not running"
}

New-Item -ItemType Directory -Force -Path data | Out-Null
python scripts/seed_phase1.py
python scripts/merge_footfall_daily.py
python scripts/rotate_edge_key.py
python scripts/seed_sample_alerts.py
python scripts/seed_identity_demo.py
Write-Host ""
Write-Host "Next:"
Write-Host "  uvicorn backend_core.main:app --reload --port 8000"
Write-Host "  python -m edge_ai"
