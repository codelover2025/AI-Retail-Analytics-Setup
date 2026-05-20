# Phase 1 — Architecture, Infrastructure & Edge Pipeline

**Timeline:** 2 weeks · **Your focus now**  
**Done vs left:** [PHASE1_STATUS.md](./PHASE1_STATUS.md)

## Deliverables in this repo

| Item | Location |
|------|----------|
| Multi-tenant schema | `shared/database/tenant_models.py` |
| `brand_id` isolation on analytics | `shared/database/models.py` |
| JWT + edge API key auth | `backend_core/auth/` |
| Edge heartbeat + config pull | `POST/GET /api/v1/edge/*` |
| Dashboard token | `POST /api/v1/auth/token` |
| Analytics APIs (tenant-scoped) | `/api/*` and `/api/v1/analytics/*` |
| RTSP ingestion | `edge_ai/camera_ingestion/rtsp_stream.py` |
| Multi-camera orchestrator | `edge_ai/multi_camera_pipeline.py` |
| Edge cloud client | `edge_ai/cloud_client.py` |
| DeepStream / Jetson scaffold | `edge_ai/deepstream/`, `deploy/jetson/` |
| Seed tenant data | `scripts/seed_phase1.py` |

## Quick start

### Option A — Windows / no Docker (SQLite)

```powershell
pip install -r requirements.txt -r requirements-ml.txt
.\scripts\setup_local.ps1
# Copy EDGE_API_KEY from output into .env

uvicorn backend_core.main:app --reload --port 8000
python -m edge_ai
```

`.env` must use: `DATABASE_URL=sqlite:///./data/orzen_dev.db` (default in `.env.example`).

### Option B — Docker (PostgreSQL, production-like)

1. **Start Docker Desktop** (required on Windows).
2. Then:

```bash
docker compose up -d postgres redis
pip install -r requirements.txt -r requirements-ml.txt
cp .env.example .env
# Edit .env: uncomment PostgreSQL DATABASE_URL, comment SQLite line
python scripts/seed_phase1.py
uvicorn backend_core.main:app --reload --port 8000
python -m edge_ai
```

### `Connection refused` on port 5432?

PostgreSQL is not running. Either start Docker + `docker compose up -d postgres`, or switch `.env` to SQLite (Option A).

## Auth flows

### Edge appliance
```http
X-Edge-Key: edge_xxxx
GET  /api/v1/edge/config
POST /api/v1/edge/heartbeat
```

### Dashboard / frontend (Phase 4)
```http
POST /api/v1/auth/token
X-API-Key: <API_KEY>
{"brand_slug":"orzen-demo","store_id":"store-001"}

Authorization: Bearer <jwt>
GET /api/v1/analytics/live-visitors
```

Dev fallback (no JWT): `X-API-Key` + `X-Brand-Slug` + `X-Store-Id` headers.

## Multi-camera

`CAMERAS_JSON` defines N RTSP sources. One thread per camera; **shared InsightFace model** behind a lock to save GPU/RAM on Jetson.

## Jetson / DeepStream

- Dev laptop: `PIPELINE_BACKEND=opencv`
- Jetson: use `deploy/jetson/docker-compose.jetson.yml`
- DeepStream SGIE face plugin: **Phase 2** (runner validates `pyds` only)

## Phase 1 handoff (items 148–152 in PHASE1_STATUS)

### 1. Fix footfall duplicate rows

```powershell
python scripts/merge_footfall_daily.py
```

Merges existing duplicates and adds unique index on `(brand_id, store_id, day)`. New code uses a single upsert path in `AnalyticsRepository`.

### 2. Test JWT flow

```powershell
.\scripts\verify_phase1_handoff.ps1
```

Or manually:

```powershell
$token = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/token" -Method POST `
  -Headers @{ "X-API-Key" = "dev-dashboard-key"; "Content-Type" = "application/json" } `
  -Body '{"brand_slug":"orzen-demo","store_id":"store-001"}'

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analytics/live-visitors" `
  -Headers @{ Authorization = "Bearer $($token.access_token)" }
```

### 3. Test multi-camera

In `.env`:

```env
MULTI_CAMERA_ENABLED=true
CAMERAS_JSON=[{"camera_id":"cam-001","rtsp_url":"0"},{"camera_id":"cam-002","rtsp_url":"0"}]
```

Then `python -m edge_ai` (two webcam indices only work if you have two cameras; otherwise use two RTSP URLs).

### 4. PostgreSQL smoke test

1. Start **Docker Desktop**.
2. In `.env`, use PostgreSQL URL (comment out SQLite line).
3. Run:

```powershell
docker compose up -d postgres
python scripts/seed_phase1.py
uvicorn backend_core.main:app --reload --port 8000
```

### 5. Jetson ops doc

See **[JETSON_DEPLOY.md](./JETSON_DEPLOY.md)** — flash, deploy, RTSP, heartbeat monitoring.

---

## Phase 1 acceptance checklist

- [x] `seed_phase1.py` creates brand + store + cameras + edge device
- [x] Heartbeat updates `edge_devices.last_heartbeat_at`
- [x] Config API returns camera RTSP list for the store
- [x] Analytics APIs return data scoped to `brand_id`
- [ ] Two RTSP streams run without crashing (multi-camera mode)
- [ ] JWT issued and accepted on `/api/v1/analytics/*` — run `verify_phase1_handoff.ps1`

## Next: Phase 2

Face recognition tuning, VIP/watchlist/employee, consent workflows — see `docs/ORZEN_BRIEF_ALIGNMENT.md`.
