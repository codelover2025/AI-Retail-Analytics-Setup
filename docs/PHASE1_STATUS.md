# Phase 1 — Status Tracker

**Project:** Orzen Vision ([Orzen_Vision_Freelance_Brief.docx](../Orzen_Vision_Freelance_Brief.docx))  
**Phase:** 1 — Architecture, Infrastructure & Edge Pipeline  
**Timeline:** 2 weeks · **Budget:** ₹30K–₹40K (Direct)  
**Last updated:** 2026-05-21 — **Phase 1 commercial scope: COMPLETE**

---

## Summary


| Status          | Count  |
| --------------- | ------ |
| **Done**        | **34** |
| **Partial**     | **0**  |
| **Not started** | **0**  |



| Milestone                                      | Progress              |
| ---------------------------------------------- | --------------------- |
| **Phase 1 commercial scope** (8 work packages) | **100%**              |
| **Full Orzen brief** (all §2 product features) | **~28%** — Phases 2–5 |


```powershell
# Run all automatable checks (API on :8000)
.\scripts\complete_phase1_handoff.ps1
```

---

## Latest project updates (completion pass)


| Date       | Update                                                                      |
| ---------- | --------------------------------------------------------------------------- |
| 2026-05-21 | **Admin API** — `POST /api/v1/admin/{brands,stores,cameras,edge-devices}`   |
| 2026-05-21 | **Batch edge events** — `POST /api/v1/edge/events`                          |
| 2026-05-21 | **Audit logs** — `audit_logs` table + admin action logging                  |
| 2026-05-21 | **RTSP vendors** — Hikvision / Dahua / CP Plus URL builders                 |
| 2026-05-21 | **DeepStream** — multi-source config generator + SGIE/PGIE templates        |
| 2026-05-21 | **K8s India** — `deploy/kubernetes/` + [DEPLOY_INDIA.md](./DEPLOY_INDIA.md) |
| 2026-05-21 | **GPU config** — `INSIGHTFACE_CTX_ID` + CUDA provider auto-detect           |
| 2026-05-21 | **Verify suite** — admin, edge events, deepstream, multi-cam live           |


---

## Phase 1 commercial scope → status (all Done)

### 1. Backend architecture setup


| #   | Item                | Status                                          |
| --- | ------------------- | ----------------------------------------------- |
| 1.1 | FastAPI + `/api/v1` | **Done**                                        |
| 1.2 | Service layer       | **Done**                                        |
| 1.3 | Config + env        | **Done**                                        |
| 1.4 | Strict API contract | **Done**                                        |
| 1.5 | WebSocket + Redis   | **Done** — `verify_redis_websocket.py`          |
| 1.6 | K8s / India cloud   | **Done** — [DEPLOY_INDIA.md](./DEPLOY_INDIA.md) |


### 2. Database schema design


| #   | Item                       | Status   |
| --- | -------------------------- | -------- |
| 2.1 | Analytics tables           | **Done** |
| 2.2 | Tenant tables              | **Done** |
| 2.3 | `brand_id` isolation       | **Done** |
| 2.4 | SQLite + PostgreSQL        | **Done** |
| 2.5 | Alembic migrations         | **Done** |
| 2.6 | Footfall unique constraint | **Done** |


### 3. Multi-tenant SaaS foundation


| #   | Item                    | Status                             |
| --- | ----------------------- | ---------------------------------- |
| 3.1 | Brand → Store → Camera  | **Done**                           |
| 3.2 | Edge device registry    | **Done**                           |
| 3.3 | Tenant-scoped APIs      | **Done**                           |
| 3.4 | Config version          | **Done**                           |
| 3.5 | Admin provisioning API  | **Done** — `/api/v1/admin/`*       |
| 3.6 | Audit / DPDP foundation | **Done** — `audit_logs` + TLS docs |


### 4. Authentication & security


| #   | Item                  | Status   |
| --- | --------------------- | -------- |
| 4.1 | Edge `X-Edge-Key`     | **Done** |
| 4.2 | Dashboard `X-API-Key` | **Done** |
| 4.3 | JWT issuance          | **Done** |
| 4.4 | JWT on v1 analytics   | **Done** |
| 4.5 | Secrets in `.env`     | **Done** |


### 5. Edge–cloud communication


| #   | Item                          | Status                                |
| --- | ----------------------------- | ------------------------------------- |
| 5.1 | `GET /api/v1/edge/config`     | **Done**                              |
| 5.2 | `POST /api/v1/edge/heartbeat` | **Done**                              |
| 5.3 | Edge client                   | **Done**                              |
| 5.4 | Status in DB                  | **Done**                              |
| 5.5 | Config refresh E2E            | **Done**                              |
| 5.6 | Batch event upload            | **Done** — `POST /api/v1/edge/events` |


### 6. RTSP / IP cameras


| #   | Item                        | Status                                   |
| --- | --------------------------- | ---------------------------------------- |
| 6.1 | OpenCV RTSP / webcam        | **Done**                                 |
| 6.2 | Reconnect                   | **Done**                                 |
| 6.3 | Frame skip                  | **Done**                                 |
| 6.4 | Hikvision / Dahua / CP Plus | **Done** — `rtsp_vendors.py` + admin API |
| 6.5 | Cameras from cloud          | **Done**                                 |


### 7. Jetson / DeepStream


| #   | Item                       | Status                                                                |
| --- | -------------------------- | --------------------------------------------------------------------- |
| 7.1 | DeepStream config template | **Done**                                                              |
| 7.2 | Jetson Docker              | **Done**                                                              |
| 7.3 | `PIPELINE_BACKEND` switch  | **Done**                                                              |
| 7.4 | DeepStream runner          | **Done** — generates config; pyds → deepstream-app or OpenCV fallback |
| 7.5 | SGIE face template         | **Done** — `config/sgie_face.txt` (model wire-up Phase 2)             |
| 7.6 | GPU / CPU selection        | **Done** — `INSIGHTFACE_CTX_ID`, CUDA providers                       |


### 8. Multi-camera


| #   | Item                 | Status                                   |
| --- | -------------------- | ---------------------------------------- |
| 8.1 | `CAMERAS_JSON`       | **Done**                                 |
| 8.2 | Orchestrator         | **Done**                                 |
| 8.3 | Shared model lock    | **Done**                                 |
| 8.4 | 2+ streams           | **Done** — `verify_multi_camera_live.py` |
| 8.5 | DeepStream batch mux | **Done** — `config_generator.py`         |


---

## New API endpoints (Phase 1 completion)


| Method | Path                         | Auth                             |
| ------ | ---------------------------- | -------------------------------- |
| POST   | `/api/v1/admin/brands`       | `X-API-Key`                      |
| POST   | `/api/v1/admin/stores`       | `X-API-Key`                      |
| POST   | `/api/v1/admin/cameras`      | `X-API-Key` (vendor or rtsp_url) |
| POST   | `/api/v1/admin/edge-devices` | `X-API-Key` (returns new key)    |
| POST   | `/api/v1/edge/events`        | `X-Edge-Key`                     |


---

## Verification scripts


| Script                        | Covers                         |
| ----------------------------- | ------------------------------ |
| `complete_phase1_handoff.ps1` | Full suite                     |
| `verify_phase1_handoff.ps1`   | Health, JWT, analytics, edge   |
| `verify_admin_api.py`         | Admin + Hikvision RTSP builder |
| `verify_edge_events.py`       | Batch upload                   |
| `verify_deepstream_config.py` | Multi-source DeepStream config |
| `verify_multi_camera_live.py` | 2-camera orchestrator          |
| `verify_redis_websocket.py`   | Redis → WebSocket              |
| `verify_postgres.ps1`         | Docker Postgres                |
| `verify_config_refresh.py`    | Config version bump            |


---

## Brief ↔ Phase 1 (unchanged scope boundary)

Phase 1 **does not** include full brief §2 (VIP CRM, zones, WhatsApp, LLM). Those are Phases 2–5.


| Brief §3 item                         | Phase 1                             |
| ------------------------------------- | ----------------------------------- |
| Edge-first, metadata only             | **Done**                            |
| Multi-tenant SaaS                     | **Done**                            |
| FastAPI + PostgreSQL + Redis          | **Done**                            |
| Camera RTSP (Hikvision/Dahua/CP Plus) | **Done** (URL builders + ingestion) |
| Jetson + DeepStream path              | **Done** (scaffold + config gen)    |


---

## Client sign-off checklist

- All 34 Phase 1 scope items implemented
- `complete_phase1_handoff.ps1` passes (with API + optional Docker Redis)
- Dashboard UI (`dashboard-ui/`) consumes APIs
- **On-site only:** physical Jetson + store NVR RTSP (use [JETSON_DEPLOY.md](./JETSON_DEPLOY.md))

---

## Next: Phase 2

VIP, watchlist, employee ID, consent workflows, Indian demographic tuning — [ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md).

---

## Related docs


| Doc                                                    | Purpose           |
| ------------------------------------------------------ | ----------------- |
| [PHASE1.md](./PHASE1.md)                               | Commands          |
| [DEPLOY_INDIA.md](./DEPLOY_INDIA.md)                   | K8s / India cloud |
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md)                 | Edge appliance    |
| [ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md) | Full product map  |


