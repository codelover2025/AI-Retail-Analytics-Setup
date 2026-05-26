# Orzen Vision — Phase 1 API Reference

**Base URL (local):** `http://127.0.0.1:8000`  
**OpenAPI:** `/docs`

---

## Authentication

### Dashboard / analytics (choose one)

**A. API key + tenant headers**

```http
X-API-Key: <API_KEY>
X-Brand-Slug: orzen-demo
X-Store-Id: store-001
```

**B. JWT**

```http
POST /api/v1/auth/token
X-API-Key: <API_KEY>
Content-Type: application/json

{"brand_slug":"orzen-demo","store_id":"store-001","subject":"dashboard"}
```

Response: `{ "access_token": "...", "token_type": "bearer" }`

Then:

```http
Authorization: Bearer <access_token>
```

### Edge appliance

```http
X-Edge-Key: <EDGE_API_KEY>
```

---

## Analytics APIs (fixed contract for dashboard)

### `GET /api/live-visitors`

**Response:**

```json
{
  "count": 2,
  "timestamp": "2026-05-20T05:16:27.878507+00:00"
}
```

### `GET /api/recognitions`

Query: `limit` (default 100, max 500)

**Response:**

```json
[
  {
    "id": "uuid",
    "type": "new_visitor",
    "time": "2026-05-20T05:13:00.983854+00:00"
  }
]
```

`type`: `vip` | `new_visitor` | `repeat_visitor` | `visitor`

### `GET /api/footfall`

Query: `from_day` (optional, `YYYY-MM-DD`)

**Response:**

```json
{
  "daily": [
    {
      "day": "2026-05-20",
      "unique_visitors": 4,
      "total_detections": 2
    }
  ],
  "hourly": [
    {
      "bucket_start": "2026-05-20T05:00:00+00:00",
      "count": 3
    }
  ]
}
```

### `GET /api/alerts`

Query: `limit`, `unacknowledged_only`

**Response:**

```json
[
  {
    "type": "vip_detected",
    "message": "VIP visitor detected: …",
    "time": "2026-05-20T05:00:00+00:00"
  }
]
```

Same shapes under `/api/v1/analytics/*` with JWT.

---

## Edge APIs

### `GET /api/v1/edge/config`

Returns cameras, pipeline settings, `config_version`.

### `POST /api/v1/edge/heartbeat`

Query: `config_version` (optional)

Body:

```json
{
  "software_version": "1.0.0",
  "pipeline_backend": "opencv",
  "cameras_active": 1,
  "fps_avg": 12.5
}
```

### `POST /api/v1/edge/events`

Batch metadata upload (alternative to edge writing DB directly).

```json
{
  "live_visitors": [
    {
      "camera_id": "cam-001",
      "track_id": 1,
      "bbox": [10, 10, 100, 100],
      "confidence": 0.9
    }
  ],
  "recognitions": [],
  "alerts": [
    {
      "alert_type": "test",
      "message": "Edge batch event"
    }
  ]
}
```

---

## Admin provisioning APIs

Requires `X-API-Key`.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/admin/brands` | Create brand |
| POST | `/api/v1/admin/stores` | Create store |
| POST | `/api/v1/admin/cameras` | Add camera (RTSP URL or Hikvision/Dahua builder) |
| POST | `/api/v1/admin/edge-devices` | Register edge device (returns new API key) |

**Camera with Hikvision builder:**

```json
{
  "brand_slug": "orzen-demo",
  "store_id": "store-001",
  "external_id": "cam-entrance",
  "vendor": "hikvision",
  "host": "192.168.1.64",
  "username": "admin",
  "password": "secret",
  "channel": 102,
  "name": "Entrance"
}
```

---

## WebSocket (optional)

`WS /ws/live?store_id=store-001`

Streams Redis alert channel `alerts:{store_id}` when `REDIS_URL` is configured.

---

## Health

`GET /health` → `{ "status": "ok", "phase": 1 }`
