# Phase 1 — Status Tracker

**Project:** Orzen Vision  
**Phase:** 1 — Architecture, Infrastructure & Edge Pipeline  
**Timeline:** 2 weeks · **Budget:** ₹30K–₹40K (Direct)  
<<<<<<< HEAD
**Last updated:** 2026-05-21 (handoff automation + dashboard-ui)
=======
**Last updated:** 2026-05-20 (post handoff fixes)
>>>>>>> origin/main

---

## Latest project updates

| Date | Update |
|------|--------|
<<<<<<< HEAD
| 2026-05-21 | **Handoff automation** — `complete_phase1_handoff.ps1`, `rotate_edge_key.py`, `seed_sample_alerts.py`, config refresh + multi-cam verify scripts |
| 2026-05-21 | **Dashboard UI** — `dashboard-ui/` Next.js app consuming `/api/*` |
| 2026-05-21 | **Alembic scaffold** — `alembic/` baseline migration `001` |
| 2026-05-20 | **SQLite dev mode** — local run without Docker/Postgres (`DATABASE_URL=sqlite:///./data/orzen_dev.db`) |
| 2026-05-20 | **End-to-end verified** — edge pipeline, heartbeat, live-visitors, recognitions, footfall, edge config |
| 2026-05-20 | **Footfall fix** — unique constraint `uq_footfall_brand_store_day`; `scripts/merge_footfall_daily.py` |
| 2026-05-20 | **Jetson 1-pager** — [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) |
=======
| 2026-05-20 | **SQLite dev mode** — local run without Docker/Postgres (`DATABASE_URL=sqlite:///./data/orzen_dev.db`) |
| 2026-05-20 | **End-to-end verified** — edge pipeline, heartbeat, live-visitors, recognitions, footfall, edge config |
| 2026-05-20 | **Footfall fix** — unique constraint `uq_footfall_brand_store_day`; `scripts/merge_footfall_daily.py` (1 duplicate merged on dev DB) |
| 2026-05-20 | **Handoff tooling** — `scripts/verify_phase1_handoff.ps1`, `scripts/setup_local.ps1` runs seed + merge |
| 2026-05-20 | **Jetson 1-pager** — [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) (flash, Docker, RTSP, monitoring) |
| 2026-05-20 | **Docs** — [PHASE1.md](./PHASE1.md) handoff steps; README links to this tracker |
>>>>>>> origin/main

---

## Summary

| Status | Count | Meaning |
|--------|------:|---------|
<<<<<<< HEAD
| **Done** | **26** | Built + verified or automated |
| **Partial** | **4** | Needs hardware / Docker / live run |
| **Not started** | **4** | Deferred (K8s, batch upload, DeepStream SGIE, encryption) |

| Milestone | Progress |
|-----------|----------|
| **Phase 1 dev deliverable** | **~92%** |
| **Client production readiness** | **~75%** |
| **Commercial scope (40 rows)** | **26 done · 4 partial · 4 not started** |

**Run full handoff:** `.\scripts\complete_phase1_handoff.ps1` (API must be on `:8000`)

---

## Tooling & scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup_local.ps1` | `.env`, seed, merge, edge key, sample alerts |
| `scripts/complete_phase1_handoff.ps1` | All automatable checks |
| `scripts/verify_phase1_handoff.ps1` | Health, JWT, APIs, edge config |
| `scripts/verify_config_refresh.py` | Config version bump E2E |
| `scripts/verify_multi_camera_config.py` | 2-camera JSON load (no webcam) |
| `scripts/verify_redis_websocket.py` | Redis → `/ws/live` (optional) |
| `scripts/verify_postgres.ps1` | Docker Postgres smoke test |
| `scripts/rotate_edge_key.py` | Set `EDGE_API_KEY` in `.env` |
| `scripts/seed_sample_alerts.py` | Demo alerts for dashboard |
=======
| **Done** | **22** | Built; most verified on your Windows dev machine |
| **Partial** | **5** | Implemented; needs your run (JWT script, multi-cam, Postgres, NVR RTSP) |
| **Not started** | **4** | Deferred (K8s, Alembic, batch upload, DeepStream SGIE) |

| Milestone | Progress |
|-----------|----------|
| **Phase 1 dev deliverable** (edge + API + DB + tenant + docs) | **~88%** |
| **Client production readiness** (Postgres, 2+ cams, Jetson, JWT signed off) | **~72%** |
| **Commercial scope items** (40 tracked rows below) | **22 done · 5 partial · 4 not started** (+ 7 analytics rows, 6 done) |

**Recommendation:** Safe to **demo Phase 1** locally. Run `.\scripts\verify_phase1_handoff.ps1` then optional Postgres + multi-camera before client sign-off.

---

## Tooling & scripts (new)

| Script | Purpose |
|--------|---------|
| `scripts/setup_local.ps1` | Windows one-shot: `.env`, seed, footfall merge |
| `scripts/seed_phase1.py` | Brand, store, camera, edge device + API key |
| `scripts/merge_footfall_daily.py` | Merge duplicate footfall rows + unique index |
| `scripts/verify_phase1_handoff.ps1` | Health, JWT, footfall, edge config checks |
| `scripts/run_test_pipeline.py` | Synthetic frames without webcam |

---

## Your commercial scope → status

### 1. Backend architecture setup

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.1 | FastAPI application structure | **Done** | `backend_core/main.py`, `/api/v1` |
| 1.2 | Service layer separation | **Done** | `analytics.py`, `edge_cloud.py` |
| 1.3 | Shared config + env | **Done** | `shared/config.py`, `.env.example` |
| 1.4 | API contract schemas | **Done** | `backend_core/schemas/contract.py` |
| 1.5 | WebSocket stub (Redis alerts) | **Partial** | Not tested with Redis running |
| 1.6 | Production deploy (K8s / India cloud) | **Not started** | With client infra Phase 1+ |

### 2. Database schema design

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.1 | Analytics tables | **Done** | visitors, recognitions, footfall, alerts, live |
| 2.2 | Multi-tenant tables | **Done** | brands, stores, cameras, edge_devices |
| 2.3 | `brand_id` tenant isolation | **Done** | All analytics rows scoped |
| 2.4 | SQLite dev + PostgreSQL prod | **Done** | SQLite active on your PC |
| 2.5 | Alembic migrations | **Not started** | `create_all` only; add before prod |
| 2.6 | Footfall unique (brand, store, day) | **Done** | Constraint + merge script executed |

### 3. Multi-tenant SaaS foundation

| # | Item | Status | Notes |
|---|------|--------|-------|
| 3.1 | Brand → Store → Camera | **Done** | `orzen-demo` / `store-001` / `cam-001` |
| 3.2 | Edge device registry | **Done** | Hashed `EDGE_API_KEY` |
| 3.3 | Tenant-scoped analytics | **Done** | `brand_id` filters in repository |
| 3.4 | Config version per store | **Done** | Heartbeat returns `config_version` |
| 3.5 | Admin provisioning API/UI | **Partial** | `seed_phase1.py` only |
| 3.6 | Encryption at rest / RLS | **Not started** | DPDP / cloud infra (brief §4) |

### 4. Authentication & security setup

| # | Item | Status | Notes |
|---|------|--------|-------|
| 4.1 | Edge API key (`X-Edge-Key`) | **Done** | Verified config API |
| 4.2 | Dashboard API key (`X-API-Key`) | **Done** | Verified all `/api/*` analytics |
| 4.3 | JWT issuance (`POST /api/v1/auth/token`) | **Partial** | Run `verify_phase1_handoff.ps1` to confirm |
| 4.4 | JWT on `/api/v1/analytics/*` | **Partial** | Same script |
| 4.5 | Secrets in `.env` | **Done** | `.env` gitignored |

### 5. Edge–cloud communication setup

| # | Item | Status | Notes |
|---|------|--------|-------|
| 5.1 | `GET /api/v1/edge/config` | **Done** | Cameras + pipeline settings |
| 5.2 | `POST /api/v1/edge/heartbeat` | **Done** | ~30s interval, 200 OK |
| 5.3 | Edge client | **Done** | `edge_ai/cloud_client.py` |
| 5.4 | Device status in DB | **Done** | `last_heartbeat_at`, `last_metrics` |
| 5.5 | Config refresh on version bump | **Partial** | `config_refresh` flag; not E2E tested |
| 5.6 | Batch event upload API | **Not started** | Edge writes DB directly today |

### 6. RTSP / IP camera integration

| # | Item | Status | Notes |
|---|------|--------|-------|
| 6.1 | RTSP + webcam (OpenCV) | **Done** | `RTSP_URL=0` verified |
| 6.2 | Reconnect on failure | **Done** | `rtsp_stream.py` |
| 6.3 | Frame skip tuning | **Done** | `FRAME_SKIP` |
| 6.4 | Hikvision / Dahua / CP Plus | **Partial** | URL format OK; no real NVR test yet |
| 6.5 | Cameras from cloud config | **Done** | Edge pulls from API |

### 7. NVIDIA Jetson / DeepStream pipeline setup

| # | Item | Status | Notes |
|---|------|--------|-------|
| 7.1 | DeepStream config template | **Done** | `edge_ai/deepstream/config/` |
| 7.2 | Jetson Docker Compose | **Done** | `deploy/jetson/` |
| 7.3 | `PIPELINE_BACKEND` switch | **Done** | `opencv` \| `deepstream` |
| 7.4 | DeepStream runner on device | **Partial** | Stub; needs Jetson + `pyds` |
| 7.5 | SGIE face plugin | **Not started** | Phase 2 |
| 7.6 | GPU on dev laptop | **Not started** | CPU InsightFace (expected on Windows) |

### 8. Multi-camera handling & optimization

| # | Item | Status | Notes |
|---|------|--------|-------|
| 8.1 | `CAMERAS_JSON` config | **Done** | `camera_config.py` |
| 8.2 | Multi-camera orchestrator | **Done** | `multi_camera_pipeline.py` |
| 8.3 | Shared model + lock | **Done** | Jetson RAM optimization |
| 8.4 | 2+ live streams tested | **Partial** | Code ready; you run with 2 RTSP/webcams |
| 8.5 | DeepStream batch mux | **Not started** | Jetson production path |

---

## Analytics pipeline (Phase 1 dev — pre–Phase 2 product)

| # | Item | Status | Verified on your PC |
|---|------|--------|---------------------|
| A.1 | InsightFace detect + embed | **Done** | Yes (`buffalo_l`, CPU) |
| A.2 | ByteTrack | **Done** | Yes |
| A.3 | Cosine match → DB | **Done** | Yes |
| A.4 | `GET /api/live-visitors` | **Done** | Yes (`count: 2`) |
| A.5 | `GET /api/recognitions` | **Done** | Yes (`new_visitor`, `repeat_visitor`) |
| A.6 | `GET /api/footfall` | **Done** | Yes (after merge: single row per day) |
| A.7 | `GET /api/alerts` | **Partial** | Empty in last test |
>>>>>>> origin/main

---

## Verified on your machine

- [x] SQLite + `setup_local.ps1` / `seed_phase1.py`
<<<<<<< HEAD
- [x] `merge_footfall_daily.py`
- [x] `rotate_edge_key.py` + `EDGE_API_KEY` in `.env`
- [x] `seed_sample_alerts.py` — `/api/alerts` returns data
- [x] `verify_phase1_handoff.ps1` — JWT + API key flows
- [x] `verify_config_refresh.py` — `config_refresh=true`
- [x] `verify_multi_camera_config.py` — 2 cameras in JSON
- [x] `dashboard-ui/` — Next.js dashboard (Phase 1 UI)
- [x] Alembic baseline (`alembic upgrade head` on fresh DB)
- [ ] `verify_redis_websocket.py` — needs `pip install redis websockets` + Redis running
- [ ] `verify_postgres.ps1` — Docker Desktop + `docker compose up -d postgres`
- [ ] Live multi-camera — `python -m edge_ai` with 2 RTSP/webcams
- [ ] Real NVR RTSP (Hikvision/Dahua) on LAN
=======
- [x] `merge_footfall_daily.py` (1 duplicate merged)
- [x] `uvicorn` — `/health` → `ok`, phase `1`
- [x] `python -m edge_ai` — config + heartbeat 200, InsightFace loaded
- [x] `/api/live-visitors`, `/api/recognitions`, `/api/footfall`
- [x] `/api/v1/edge/config` with `EDGE_API_KEY` from `.env`
- [ ] `.\scripts\verify_phase1_handoff.ps1` (JWT + automated checks)
- [ ] Multi-camera (`CAMERAS_JSON` + `MULTI_CAMERA_ENABLED=true`)
- [ ] PostgreSQL via Docker (`docker compose up -d postgres`)
>>>>>>> origin/main
- [ ] Jetson hardware deploy ([JETSON_DEPLOY.md](./JETSON_DEPLOY.md))

---

## Handoff checklist

| # | Task | Status | Action |
|---|------|--------|--------|
<<<<<<< HEAD
| 1 | Footfall duplicate rows | **Done** | `merge_footfall_daily.py` |
| 2 | JWT flow | **Done** | `verify_phase1_handoff.ps1` |
| 3 | Config refresh E2E | **Done** | `verify_config_refresh.py` |
| 4 | Sample alerts | **Done** | `seed_sample_alerts.py` |
| 5 | Edge API key in `.env` | **Done** | `rotate_edge_key.py` |
| 6 | Multi-camera config | **Done** (config) | Live run: `MULTI_CAMERA_ENABLED=true` |
| 7 | PostgreSQL smoke test | **You run** | `verify_postgres.ps1` |
| 8 | Redis WebSocket | **You run** | `docker compose up -d redis` + verify script |
| 9 | Jetson ops doc | **Done** | [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) |
=======
| 1 | Footfall duplicate rows | **Done** | Merged + unique index; new visits use single row per day |
| 2 | JWT flow | **Run script** | `.\scripts\verify_phase1_handoff.ps1` |
| 3 | Multi-camera | **You run** | See [PHASE1.md](./PHASE1.md) § multi-camera |
| 4 | PostgreSQL smoke test | **You run** | Docker Desktop → `docker compose up -d postgres` |
| 5 | Jetson ops doc | **Done** | [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) |
>>>>>>> origin/main

---

## Still open (before Phase 2)

| Priority | Item |
|----------|------|
<<<<<<< HEAD
| Medium | Live multi-camera + real NVR RTSP |
| Medium | PostgreSQL Docker smoke test |
| Low | Redis WebSocket test (install deps + Redis) |
| Low | K8s / India cloud production deploy |
| Not started | Batch event upload API, DeepStream SGIE, encryption/RLS |
| Phase 2 | VIP workflows, consent, zone analytics, WhatsApp, HRMS, LLM |
=======
| High | Run `verify_phase1_handoff.ps1` and tick JWT in checklist above |
| High | PostgreSQL smoke test on Docker |
| Medium | Multi-camera test with 2 RTSP URLs |
| Medium | Real NVR RTSP (Hikvision/Dahua) on LAN |
| Low | Alembic, Redis WebSocket test, K8s/India cloud |
| Phase 2 | VIP, watchlist, employee, consent, Indian tuning |
>>>>>>> origin/main

---

## Phase 2 preview (out of Phase 1 scope)

- VIP / watchlist / employee recognition  
- Consent & DPDP audit workflows  
- Indian demographic model tuning  
- Zone analytics, dwell, heatmaps  
<<<<<<< HEAD
- WhatsApp, HRMS, LLM  
=======
- Dashboard, WhatsApp, HRMS, LLM  
>>>>>>> origin/main

See **[ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md)**.

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [PHASE1.md](./PHASE1.md) | Run, test, handoff commands |
<<<<<<< HEAD
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) | Jetson Orin deployment |
| [../dashboard-ui/README.md](../dashboard-ui/README.md) | Dashboard setup |
=======
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) | Jetson Orin deployment 1-pager |
| [ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md) | Full Orzen brief vs repo |
>>>>>>> origin/main
| [../README.md](../README.md) | Repo overview |
