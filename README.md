# Orzen Vision — edge + API (retail analytics core)

Product brief: **`Orzen_Vision_Freelance_Brief.docx`**

## Client delivery (Phase 1)

| Document | Purpose |
|----------|---------|
| **[docs/CLIENT_DELIVERY_PHASE1.md](docs/CLIENT_DELIVERY_PHASE1.md)** | **What to deliver to Orzen + sign-off** |
| [docs/CLIENT_DEMO_GUIDE.md](docs/CLIENT_DEMO_GUIDE.md) | 15-minute demo script |
| [docs/API_REFERENCE_PHASE1.md](docs/API_REFERENCE_PHASE1.md) | API contract |
| [DELIVERY_README.txt](DELIVERY_README.txt) | Quick pointer for zip handover |

Internal: [docs/PHASE1_STATUS.md](docs/PHASE1_STATUS.md) · [docs/PHASE1.md](docs/PHASE1.md) · [docs/ORZEN_BRIEF_ALIGNMENT.md](docs/ORZEN_BRIEF_ALIGNMENT.md)

---

Pipeline: **RTSP/webcam → InsightFace → ByteTrack → cosine match → DB → FastAPI → Dashboard**

## Layout

| Path | Role |
|------|------|
| `edge_ai/` | RTSP, detection, tracking, recognition, alerts |
| `backend_core/` | FastAPI, auth, analytics + edge + admin APIs |
| `dashboard-ui/` | Next.js dashboard — [dashboard-ui/README.md](dashboard-ui/README.md) |
| `shared/` | Config, database models, repositories |
| `deploy/` | Jetson + Kubernetes (India) |
| `scripts/` | Setup, verify, demo |

## Run with frontend (recommended for demo)

```powershell
.\scripts\setup_local.ps1
.\scripts\run_with_frontend.ps1
```

- Dashboard: http://localhost:3000  
- API: http://127.0.0.1:8000/docs  

## Run API + edge only

```powershell
pip install -r requirements.txt -r requirements-ml.txt
.\scripts\setup_local.ps1
uvicorn backend_core.main:app --host 127.0.0.1 --port 8000 --reload
python -m edge_ai
```

## API contract (dashboard)

| Endpoint | Response |
|----------|----------|
| `GET /api/live-visitors` | `{ count, timestamp }` |
| `GET /api/recognitions` | `[{ id, type, time }]` |
| `GET /api/footfall` | `{ daily, hourly }` |
| `GET /api/alerts` | `[{ type, message, time }]` |

Details: [docs/API_REFERENCE_PHASE1.md](docs/API_REFERENCE_PHASE1.md)

## Docker

```bash
docker compose up --build
```

## Phase scope

**Phase 1 (this delivery):** Architecture, edge pipeline, multi-tenant API, starter dashboard.  
**Phases 2–5:** VIP/watchlist, zones, WhatsApp, full dashboard, LLM — see [ORZEN_BRIEF_ALIGNMENT.md](docs/ORZEN_BRIEF_ALIGNMENT.md).
