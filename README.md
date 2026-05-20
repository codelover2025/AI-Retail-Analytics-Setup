# Orzen Vision — edge + API (retail analytics core)

Product brief: **`Orzen_Vision_Freelance_Brief.docx`**.  
**Phase 1 (current):** **[docs/PHASE1.md](docs/PHASE1.md)** · Full roadmap: **[docs/ORZEN_BRIEF_ALIGNMENT.md](docs/ORZEN_BRIEF_ALIGNMENT.md)**

This repo is the **edge inference + face recognition + tracking + FastAPI + PostgreSQL** foundation for Orzen Vision (jewellery retail). Phase 1 adds **multi-tenant SaaS**, **edge↔cloud auth/heartbeat**, and **multi-camera** RTSP. Dashboards, WhatsApp, HRMS/POS/CRM, and LLM are later phases.

Pipeline: **RTSP/webcam → InsightFace detect/embed → ByteTrack → cosine match → PostgreSQL → FastAPI**.

## Layout

| Path | Role |
|------|------|
| `edge_ai/` | RTSP ingestion, detection, ByteTrack, embeddings, recognition, VIP/repeat alerts |
| `backend_core/` | FastAPI app, **strict** response schemas (`schemas/contract.py`), `services/` |
| `shared/` | Settings, SQLAlchemy models, repository (used by edge + API) |

Python package names use underscores (`edge_ai`, `backend_core`); Docker Compose service names use hyphens (`edge-ai`, `backend-core`).

## API contract (requires `X-API-Key` when `API_KEY` is set)

### `GET /api/live-visitors`

```json
{ "count": 3, "timestamp": "2026-05-19T12:00:00+00:00" }
```

`timestamp` is the latest `last_seen_at` among live rows (or “now” if none).

### `GET /api/recognitions`

```json
[
  { "id": "uuid-string", "type": "vip", "time": "2026-05-19T12:00:00+00:00" }
]
```

`type` is one of: `vip`, `new_visitor`, `repeat_visitor`, `visitor`.

### `GET /api/footfall`

```json
{
  "daily": [
    { "day": "2026-05-19", "unique_visitors": 120, "total_detections": 450 }
  ],
  "hourly": [
    { "bucket_start": "2026-05-19T12:00:00+00:00", "count": 42 }
  ]
}
```

Hourly buckets are `COUNT(*)` of **recognition** rows per UTC hour (last 168 buckets by default).

### `GET /api/alerts`

```json
[
  { "type": "vip_detected", "message": "VIP visitor detected: …", "time": "2026-05-19T12:00:00+00:00" }
]
```

## Run locally

1. PostgreSQL (or Docker Compose `postgres` only).
2. Copy `.env.example` → `.env` and set `DATABASE_URL`, `RTSP_URL` (`0` = default webcam index).
3. Install deps:

```bash
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

4. API: `uvicorn backend_core.main:app --reload --host 0.0.0.0 --port 8000`
5. Edge: `python -m edge_ai` (or `docker compose up edge-ai`)

**CI / no GPU:** `python scripts/run_test_pipeline.py --frames 20` uses `MockFaceDetector` (no InsightFace).

## Docker

```bash
docker compose up --build
```

- **backend-core**: `http://localhost:8000`
- **edge-ai**: runs `python -m edge_ai` (same image includes InsightFace + ONNX Runtime).

## Data stored

- Visitor **embeddings** (JSONB), optional metadata; no full video.
- Recognitions, live visitor rows (pruned after `MAX_LIVE_VISITOR_SECONDS`), daily footfall rollups, alerts.

## WebSocket (optional)

`GET /ws/live` — Redis pub/sub for alerts when `REDIS_URL` is set; otherwise heartbeat only.
