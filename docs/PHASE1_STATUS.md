# Phase 1 — Status Tracker

**Project:** Orzen Vision  
**Phase:** 1 — Architecture, Infrastructure & Edge Pipeline  
**Timeline:** 2 weeks · **Budget:** ₹30K–₹40K (Direct)  
**Last updated:** 2026-05-21 (handoff automation + dashboard-ui)

---

## Latest project updates

| Date | Update |
|------|--------|
| 2026-05-21 | **Handoff automation** — `complete_phase1_handoff.ps1`, `rotate_edge_key.py`, `seed_sample_alerts.py`, config refresh + multi-cam verify scripts |
| 2026-05-21 | **Dashboard UI** — `dashboard-ui/` Next.js app consuming `/api/*` |
| 2026-05-21 | **Alembic scaffold** — `alembic/` baseline migration `001` |
| 2026-05-20 | **SQLite dev mode** — local run without Docker/Postgres (`DATABASE_URL=sqlite:///./data/orzen_dev.db`) |
| 2026-05-20 | **End-to-end verified** — edge pipeline, heartbeat, live-visitors, recognitions, footfall, edge config |
| 2026-05-20 | **Footfall fix** — unique constraint `uq_footfall_brand_store_day`; `scripts/merge_footfall_daily.py` |
| 2026-05-20 | **Jetson 1-pager** — [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) |

---

## Summary

| Status | Count | Meaning |
|--------|------:|---------|
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

---

## Verified on your machine

- [x] SQLite + `setup_local.ps1` / `seed_phase1.py`
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
- [ ] Jetson hardware deploy ([JETSON_DEPLOY.md](./JETSON_DEPLOY.md))

---

## Handoff checklist

| # | Task | Status | Action |
|---|------|--------|--------|
| 1 | Footfall duplicate rows | **Done** | `merge_footfall_daily.py` |
| 2 | JWT flow | **Done** | `verify_phase1_handoff.ps1` |
| 3 | Config refresh E2E | **Done** | `verify_config_refresh.py` |
| 4 | Sample alerts | **Done** | `seed_sample_alerts.py` |
| 5 | Edge API key in `.env` | **Done** | `rotate_edge_key.py` |
| 6 | Multi-camera config | **Done** (config) | Live run: `MULTI_CAMERA_ENABLED=true` |
| 7 | PostgreSQL smoke test | **You run** | `verify_postgres.ps1` |
| 8 | Redis WebSocket | **You run** | `docker compose up -d redis` + verify script |
| 9 | Jetson ops doc | **Done** | [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) |

---

## Still open (before Phase 2)

| Priority | Item |
|----------|------|
| Medium | Live multi-camera + real NVR RTSP |
| Medium | PostgreSQL Docker smoke test |
| Low | Redis WebSocket test (install deps + Redis) |
| Low | K8s / India cloud production deploy |
| Not started | Batch event upload API, DeepStream SGIE, encryption/RLS |
| Phase 2 | VIP workflows, consent, zone analytics, WhatsApp, HRMS, LLM |

---

## Phase 2 preview (out of Phase 1 scope)

- VIP / watchlist / employee recognition  
- Consent & DPDP audit workflows  
- Indian demographic model tuning  
- Zone analytics, dwell, heatmaps  
- WhatsApp, HRMS, LLM  

See **[ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md)**.

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [PHASE1.md](./PHASE1.md) | Run, test, handoff commands |
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) | Jetson Orin deployment |
| [../dashboard-ui/README.md](../dashboard-ui/README.md) | Dashboard setup |
| [../README.md](../README.md) | Repo overview |
