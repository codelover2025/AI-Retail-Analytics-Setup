# Orzen Vision — Phase 1 Client Delivery Pack

**Client:** Orzen (Kriyora)  
**Deliverable:** Phase 1 — Architecture, Infrastructure & Edge Pipeline  
**Timeline:** 2 weeks  
**Repository:** AI-Retail-Analytics-Setup  
**Delivery date:** _______________

---

## 1. Executive summary

Phase 1 delivers the **technical foundation** for Orzen Vision: a multi-tenant backend, edge camera pipeline, cloud APIs, operator dashboard, and deployment scaffolds for India cloud and Jetson stores.

This phase does **not** include the full product in the Orzen brief (VIP CRM workflows, zone analytics, WhatsApp, HRMS, LLM). Those are **Phases 2–5** per the agreed roadmap.

**Phase 1 commercial scope: 100% complete** (34/34 items). See internal tracker: [PHASE1_STATUS.md](./PHASE1_STATUS.md).

---

## 2. What you are receiving

### 2.1 Source code & modules

| Deliverable | Location | Description |
|-------------|----------|-------------|
| Edge AI pipeline | `edge_ai/` | RTSP/webcam ingest, InsightFace, ByteTrack, recognition, alerts |
| Backend API | `backend_core/` | FastAPI, JWT + API keys, tenant isolation |
| Shared database layer | `shared/` | Models, multi-tenant schema, repositories |
| Dashboard UI | `dashboard-ui/` | Next.js store dashboard (live stats, alerts, charts) |
| Docker / Compose | `docker-compose.yml`, `Dockerfile` | API + edge + Postgres + Redis |
| Jetson deploy | `deploy/jetson/` | Edge appliance Docker for NVIDIA Orin |
| Kubernetes (India) | `deploy/kubernetes/` | Production API scaffold (Mumbai / Central India) |
| Automation scripts | `scripts/` | Seed, verify, handoff, demo |
| DB migrations | `alembic/` | Baseline schema migration |

### 2.2 Documentation (include in handover)

| Document | Audience | Purpose |
|----------|----------|---------|
| **This file** | Client / PM | What was delivered & acceptance |
| [CLIENT_DEMO_GUIDE.md](./CLIENT_DEMO_GUIDE.md) | Client technical team | Run demo in 15 minutes |
| [API_REFERENCE_PHASE1.md](./API_REFERENCE_PHASE1.md) | Frontend / integrators | API contract |
| [PHASE1.md](./PHASE1.md) | Developers | Technical setup |
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) | Store IT | Edge appliance on Orin |
| [DEPLOY_INDIA.md](./DEPLOY_INDIA.md) | DevOps | Cloud deploy India region |
| [ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md) | PM | Full brief vs phases map |
| [PHASE1_STATUS.md](./PHASE1_STATUS.md) | Internal | Item-level completion proof |
| `Orzen_Vision_Freelance_Brief.docx` | Reference | Original product brief |
| `dashboard-ui/README.md` | Frontend | Dashboard env & routes |

### 2.3 Runnable services

| Service | URL (local demo) | Role |
|---------|------------------|------|
| REST API | http://127.0.0.1:8000 | Analytics + admin + edge |
| API docs (Swagger) | http://127.0.0.1:8000/docs | Interactive API test |
| Dashboard | http://localhost:3000 | Store operator UI |
| Edge pipeline | CLI: `python -m edge_ai` | Processes camera → DB/API |

---

## 3. Phase 1 scope (what was contracted)

Aligned with **Phase 1 — Architecture, Infrastructure & Edge Pipeline** (₹30K–₹40K / 2 weeks):

1. **Backend architecture** — FastAPI, services, strict JSON contracts  
2. **Database schema** — Analytics + multi-tenant (brand → store → camera → edge device)  
3. **Multi-tenant SaaS foundation** — `brand_id` isolation, provisioning APIs  
4. **Authentication & security** — Edge API key, dashboard API key, JWT  
5. **Edge–cloud communication** — Config pull, heartbeat, batch events API  
6. **RTSP / IP cameras** — OpenCV ingest, Hikvision/Dahua/CP Plus URL builders  
7. **Jetson / DeepStream** — Config templates, runner, multi-stream mux generator  
8. **Multi-camera** — Orchestrator, shared model lock, JSON camera config  

**Bonus included (not replacing Phase 4):** Starter **dashboard-ui** consuming the four analytics APIs.

---

## 4. Explicitly out of scope (Phases 2–5)

Do **not** expect these in Phase 1 sign-off:

| Capability | Planned phase |
|------------|---------------|
| VIP / watchlist / employee recognition (production) | Phase 2 |
| Consent management & full DPDP workflows | Phase 2 |
| Indian demographic model fine-tuning | Phase 2 |
| Zone dwell, journey maps, heatmaps | Phase 3 |
| Staff–customer attribution, HRMS | Phase 3–4 |
| WhatsApp Business API alerts | Phase 4 |
| POS / CRM / ERP integrations | Phase 4 |
| Full owner dashboard (multi-store, export, mobile polish) | Phase 4 |
| LLM / voice queries / forecasting | Phase 5 |

---

## 5. Acceptance criteria (sign-off checklist)

Client can verify Phase 1 by completing these checks:

- [ ] Repository received (zip or Git access) with folders in §2.1  
- [ ] `.\scripts\setup_local.ps1` runs without errors  
- [ ] `.\scripts\complete_phase1_handoff.ps1` passes with API on port 8000  
- [ ] Dashboard opens at http://localhost:3000 and shows live visitors / footfall / alerts  
- [ ] `GET /api/live-visitors` returns `{ count, timestamp }` with valid API key  
- [ ] Edge device: `GET /api/v1/edge/config` works with `X-Edge-Key`  
- [ ] Optional: `python -m edge_ai` with webcam increases live visitor count  
- [ ] Documentation pack in §2.2 reviewed  

**On-site (store hardware — documented, not remote deliverable):**

- [ ] Jetson deployed using [JETSON_DEPLOY.md](./JETSON_DEPLOY.md)  
- [ ] Real NVR RTSP URL tested on LAN  

---

## 6. Credentials & secrets handover

Provide the client **securely** (not in git):

| Item | Where generated | Notes |
|------|-----------------|-------|
| `EDGE_API_KEY` | `scripts/seed_phase1.py` or `rotate_edge_key.py` | One per edge appliance |
| `API_KEY` | `.env` → `API_KEY=...` | Dashboard + admin API |
| `JWT_SECRET` | `.env` | Change in production |
| `DATABASE_URL` | `.env` | SQLite dev; Postgres prod |

Template: `.env.example` (no real secrets).

---

## 7. Recommended delivery format

**Option A — Git**

- Private repo access, tag: `phase-1-delivery-v1.0`  
- README + `docs/CLIENT_DELIVERY_PHASE1.md` as entry point  

**Option B — Zip archive**

Include:

```
Orzen-Vision-Phase1/
  source/          (full repo minus .env, data/, node_modules/, __pycache__)
  docs/            (all docs/ files + brief docx)
  DELIVERY_README.txt → link to docs/CLIENT_DELIVERY_PHASE1.md
```

**Exclude from zip:** `.env`, `data/*.db`, `dashboard-ui/node_modules`, `.insightface/`, `__pycache__`

**Option C — Demo call**

- Screen-share: [CLIENT_DEMO_GUIDE.md](./CLIENT_DEMO_GUIDE.md) flow (15 min)  
- Hand over credentials after call  

---

## 8. Known limitations (disclose to client)

1. **Dev laptop** uses CPU inference; production edge uses Jetson GPU.  
2. **SQLite** is for local demo; production should use **PostgreSQL** ([DEPLOY_INDIA.md](./DEPLOY_INDIA.md)).  
3. **DeepStream SGIE face plugin** is templated; full GPU face pipeline is Phase 2.  
4. **Dashboard** is Phase 1 starter UI, not the full brief §2 dashboard spec.  
5. **No raw video** stored in cloud — only embeddings and metadata (brief-aligned).  

---

## 9. Support & next phase

| Item | Detail |
|------|--------|
| Phase 1 warranty | Define in contract (e.g. 14 days bug-fix on delivered scope) |
| Phase 2 kickoff | Facial recognition & identity ([ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md)) |
| Contact | Your delivery email / handover call |

---

## 10. Sign-off

| Role | Name | Signature | Date |
|------|------|-------------|------|
| Delivered by (vendor) | | | |
| Accepted by (Orzen) | | | |

---

*Orzen Vision — Phase 1 delivery pack v1.0*
