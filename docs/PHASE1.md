# Phase 1 — Architecture, Infrastructure & Edge Pipeline

**Timeline:** 2 weeks · **Your focus now**

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

## Phase 1 acceptance checklist

- [ ] `seed_phase1.py` creates brand + store + cameras + edge device
- [ ] Heartbeat updates `edge_devices.last_heartbeat_at` in Postgres
- [ ] Config API returns camera RTSP list for the store
- [ ] Analytics APIs return data scoped to `brand_id`
- [ ] Two RTSP streams run without crashing (multi-camera mode)
- [ ] JWT issued and accepted on `/api/v1/analytics/*`

## Next: Phase 2

Face recognition tuning, VIP/watchlist/employee, consent workflows — see `docs/ORZEN_BRIEF_ALIGNMENT.md`.
