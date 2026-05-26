# How to Run — Orzen Vision (Phase 1)

Step-by-step guide to run the **API**, **dashboard**, and **edge pipeline** on your machine.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 or 3.12 | API + edge AI |
| Node.js | 18+ | Dashboard |
| Git | Any | Clone repo |
| Webcam | Optional | Live edge demo (`RTSP_URL=0`) |
| Docker Desktop | Optional | PostgreSQL + Redis |

---

## 1. First-time setup (once)

Open PowerShell in the project root (`AI-Retail-Analytics-Setup`):

```powershell
# 1) Python dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt

# 2) Environment + database seed
copy .env.example .env
.\scripts\setup_local.ps1
```

`setup_local.ps1` will:

- Create `data/orzen_dev.db` (SQLite)
- Seed brand `orzen-demo`, store `store-001`, camera, edge device
- Print **`EDGE_API_KEY=edge_...`** — add that line to `.env` if not added automatically

```powershell
# 3) Dashboard dependencies
cd dashboard-ui
copy .env.local.example .env.local
npm install
cd ..
```

### Default `.env` (local demo)

```env
DATABASE_URL=sqlite:///./data/orzen_dev.db
API_KEY=dev-dashboard-key
BRAND_SLUG=orzen-demo
STORE_ID=store-001
RTSP_URL=0
BACKEND_URL=http://localhost:8000
```

### Default `dashboard-ui/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=dev-dashboard-key
NEXT_PUBLIC_BRAND_SLUG=orzen-demo
NEXT_PUBLIC_STORE_ID=store-001
```

---

## 2. Quick run (recommended — API + dashboard)

From project root:

```powershell
.\scripts\run_with_frontend.ps1
```

This opens **two windows**:

| Window | Service | URL |
|--------|---------|-----|
| 1 | Backend API | http://127.0.0.1:8000 |
| 2 | Dashboard | http://localhost:3000 |

**API documentation (Swagger):** http://127.0.0.1:8000/docs

---

## 3. Manual run (three terminals)

Use this if you prefer separate control.

### Terminal 1 — Backend API

```powershell
cd D:\AI-Retail-Analytics-Setup
uvicorn backend_core.main:app --host 127.0.0.1 --port 8000 --reload
```

Check: http://127.0.0.1:8000/health → `{"status":"ok","phase":1}`

### Terminal 2 — Dashboard (frontend)

```powershell
cd D:\AI-Retail-Analytics-Setup\dashboard-ui
npm run dev
```

Open: **http://localhost:3000**

### Terminal 3 — Edge AI (optional, live camera data)

```powershell
cd D:\AI-Retail-Analytics-Setup
python -m edge_ai
```

- First run downloads InsightFace model (~275 MB).
- Uses webcam if `RTSP_URL=0` in `.env`.
- Sends heartbeat to API every ~30s.
- Refresh dashboard — **live visitors** count should update.

---

## 4. Run with Docker (PostgreSQL)

1. Start **Docker Desktop**.
2. Edit `.env` — use PostgreSQL URL, comment out SQLite:

```env
DATABASE_URL=postgresql+psycopg2://retail:retail@localhost:5432/retail_analytics
```

3. Run:

```powershell
docker compose up -d postgres redis
python scripts/seed_phase1.py
uvicorn backend_core.main:app --host 127.0.0.1 --port 8000 --reload
```

Edge + dashboard: same as §3 terminals 2–3.

Verify Postgres:

```powershell
.\scripts\verify_postgres.ps1
```

---

## 5. Run everything in Docker

```powershell
docker compose up --build
```

| Service | Port |
|---------|------|
| backend-core | 8000 |
| postgres | 5432 |
| redis | 6379 |

Edge container needs camera/RTSP access — usually run edge **on host** with `python -m edge_ai` instead.

---

## 6. RTSP / store camera

### Webcam (dev)

```env
RTSP_URL=0
```

### IP camera / NVR (Hikvision example)

```env
RTSP_URL=rtsp://admin:password@192.168.1.64:554/Streaming/Channels/102
```

### Multiple cameras

```env
MULTI_CAMERA_ENABLED=true
CAMERAS_JSON=[{"camera_id":"cam-001","rtsp_url":"rtsp://..."},{"camera_id":"cam-002","rtsp_url":"rtsp://..."}]
```

---

## 7. Verify installation

API must be running on port 8000:

```powershell
.\scripts\complete_phase1_handoff.ps1
```

All checks should show **PASS** (Redis test is optional without Docker).

---

## 8. Test APIs

### Browser (address bar)

Use `api_key` query param (must match `API_KEY` in `.env`):

```
http://127.0.0.1:8000/api/live-visitors?api_key=dev-dashboard-key
```

Restart **uvicorn** after changing `.env`.

### Alternative (header — production style)

Prefer headers in production (do not put API keys in URLs or logs). Values must match `API_KEY`, `BRAND_SLUG`, and `STORE_ID` in `.env`.

**Swagger UI:** http://127.0.0.1:8000/docs → **Authorize** → enter `dev-dashboard-key` as `X-API-Key`, then call endpoints from the UI.

**PowerShell:**

```powershell
$headers = @{
  "X-API-Key"    = "dev-dashboard-key"
  "X-Brand-Slug" = "orzen-demo"
  "X-Store-Id"   = "store-001"
}

Invoke-RestMethod http://127.0.0.1:8000/api/live-visitors -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/recognitions -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/footfall -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/alerts -Headers $headers
```

**curl:**

```bash
curl -s -H "X-API-Key: dev-dashboard-key" -H "X-Brand-Slug: orzen-demo" -H "X-Store-Id: store-001" \
  http://127.0.0.1:8000/api/live-visitors
```

Edge config (use key from `.env`):

```powershell
$k = (Get-Content .env | Where-Object { $_ -match '^EDGE_API_KEY=' }) -replace 'EDGE_API_KEY=',''
Invoke-RestMethod http://127.0.0.1:8000/api/v1/edge/config -Headers @{ "X-Edge-Key" = $k.Trim() }
```

---

## 9. Stop services

| Service | How to stop |
|---------|-------------|
| API / dashboard | `Ctrl+C` in each terminal |
| Docker | `docker compose down` |
| Edge pipeline | `Ctrl+C` in edge terminal |

---

## 10. Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` port 5432 | Use SQLite in `.env` or start Docker Postgres |
| `Connection refused` port 8000 | Start API first (`uvicorn ...`) |
| Dashboard empty / errors | Check API is up; `NEXT_PUBLIC_API_KEY` = `API_KEY` in `.env` |
| `Invalid edge API key` | Run `python scripts/rotate_edge_key.py` and update `.env` |
| InsightFace slow / CUDA warning | Normal on Windows CPU; first run downloads model |
| Port 3000 in use | Dashboard may use 3001 — read terminal output |
| No alerts on dashboard | Run `python scripts/seed_sample_alerts.py` |
| Docker not starting | Open Docker Desktop and wait until running |

---

## 11. URLs cheat sheet

| What | URL |
|------|-----|
| Dashboard | http://localhost:3000 |
| API health | http://127.0.0.1:8000/health |
| API Swagger | http://127.0.0.1:8000/docs |
| Live visitors API | http://127.0.0.1:8000/api/live-visitors |

---

## 12. More docs

| Document | Topic |
|----------|--------|
| [CLIENT_DEMO_GUIDE.md](./CLIENT_DEMO_GUIDE.md) | Demo for client |
| [API_REFERENCE_PHASE1.md](./API_REFERENCE_PHASE1.md) | API contract |
| [JETSON_DEPLOY.md](./JETSON_DEPLOY.md) | Store edge device |
| [DEPLOY_INDIA.md](./DEPLOY_INDIA.md) | Production cloud |
| [PHASE1.md](./PHASE1.md) | Phase 1 technical notes |

---

*Orzen Vision — How to Run v1.0*
