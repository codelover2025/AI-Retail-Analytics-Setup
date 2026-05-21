# Orzen Vision — Phase 1 Client Demo Guide (15 minutes)

Use this script for a **live demo** or **recorded walkthrough** when handing Phase 1 to Orzen.

---

## Before the demo (5 min prep)

### Requirements

- Windows 10/11 or Linux  
- Python 3.11+  
- Node.js 18+  
- Webcam (optional, for live edge demo)  
- Docker Desktop (optional, for Postgres/Redis demo)

### One-time setup

```powershell
cd D:\AI-Retail-Analytics-Setup   # your repo path

pip install -r requirements.txt -r requirements-ml.txt

.\scripts\setup_local.ps1
# Saves EDGE_API_KEY into .env — keep this private

cd dashboard-ui
copy .env.local.example .env.local
npm install
cd ..
```

---

## Demo flow

### Step 1 — Start API + Dashboard (2 min)

**Option A — one script (two windows):**

```powershell
.\scripts\run_with_frontend.ps1
```

**Option B — manual:**

```powershell
# Terminal 1
uvicorn backend_core.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2
cd dashboard-ui
npm run dev
```

Open:

- **Dashboard:** http://localhost:3000  
- **API docs:** http://127.0.0.1:8000/docs  

**Say:** *"This is the operator view. It polls the backend every 10 seconds for live store metrics."*

---

### Step 2 — Dashboard walkthrough (3 min)

Show pages:

| Page | What to show |
|------|----------------|
| **Home** | Live visitor count, footfall charts, recent recognitions |
| **Visitors** | Recognition list (`new_visitor`, `repeat_visitor`) |
| **Alerts** | Sample alerts (from `seed_sample_alerts.py`) |
| **Analytics** | Daily / hourly footfall |

**Say:** *"Phase 4 will expand this to multi-store owner view, exports, and mobile polish per the brief."*

---

### Step 3 — API contract (3 min)

In browser or PowerShell:

```powershell
$headers = @{
  "X-API-Key"    = "dev-dashboard-key"
  "X-Brand-Slug" = "orzen-demo"
  "X-Store-Id"   = "store-001"
}

Invoke-RestMethod http://127.0.0.1:8000/api/live-visitors -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/recognitions -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/footfall -Headers $headers
```

Or use **Swagger** at `/docs`.

**Say:** *"These four endpoints are fixed for your frontend team — contract in API_REFERENCE_PHASE1.md."*

---

### Step 4 — Edge appliance (5 min)

Show edge is registered:

```powershell
Get-Content .env | Select-String EDGE_API_KEY
$k = $env:EDGE_API_KEY  # or paste from .env

Invoke-RestMethod http://127.0.0.1:8000/api/v1/edge/config -Headers @{ "X-Edge-Key" = $k }
```

Start edge (webcam):

```powershell
python -m edge_ai
```

**Say:** *"The edge pulls camera config from cloud, sends heartbeat every 30s, and runs face detection locally. Only metadata goes to the server — no video upload."*

Refresh dashboard — live count should update.

---

### Step 5 — Multi-tenant & admin (2 min)

Show Swagger or curl:

- `POST /api/v1/admin/cameras` with Hikvision vendor → RTSP URL built automatically  
- Mention `brand_id` isolates jewellery chains  

**Say:** *"New stores and cameras are provisioned via admin API; production will use your ops console in a later phase."*

---

## Automated proof (for technical reviewer)

```powershell
.\scripts\complete_phase1_handoff.ps1
```

All steps should print `PASS` (Redis test optional if Docker not running).

---

## Troubleshooting (demo day)

| Issue | Fix |
|-------|-----|
| Port 8000 in use | Stop other uvicorn; change port in `.env` + dashboard `.env.local` |
| Dashboard empty | API not running; wrong `NEXT_PUBLIC_API_KEY` |
| Edge InsightFace slow | First run downloads model (~275 MB); normal |
| No webcam | Use `python scripts/run_test_pipeline.py --frames 10` |
| Postgres error | Use SQLite: `DATABASE_URL=sqlite:///./data/orzen_dev.db` in `.env` |

---

## What not to demo as Phase 1

- WhatsApp alerts  
- VIP CRM enrolment UI  
- Zone heatmaps  
- LLM chat  

Point to [ORZEN_BRIEF_ALIGNMENT.md](./ORZEN_BRIEF_ALIGNMENT.md) for roadmap.

---

## After demo

Send client:

1. [CLIENT_DELIVERY_PHASE1.md](./CLIENT_DELIVERY_PHASE1.md)  
2. [API_REFERENCE_PHASE1.md](./API_REFERENCE_PHASE1.md)  
3. Git tag or zip (see delivery doc §7)  
4. Credentials via secure channel  
