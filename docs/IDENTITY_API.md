# Identity API + Dashboard

Backend layer for facial recognition **data only** (no matching / embeddings generation).

## Database tables

| Table | Purpose |
|-------|---------|
| `customers` | `id`, `first_seen`, `last_seen`, `visit_count` |
| `employees` | `id`, `name`, `embedding`, `active`, `created_at`, `updated_at` |
| `person_recognitions` | AI logs → exposed as `/api/recognitions` |
| `face_embeddings` | Optional embeddings linked to customers |

## API contract (strict)

### `GET /api/customers`

```json
[
  {
    "id": "uuid",
    "first_seen": "2026-05-27T10:00:00+00:00",
    "last_seen": "2026-05-27T12:00:00+00:00",
    "visit_count": 4
  }
]
```

### `GET /api/recognitions`

```json
[
  {
    "id": "uuid",
    "person_id": "uuid",
    "type": "repeat_visitor",
    "timestamp": "2026-05-27T12:00:00+00:00",
    "camera_id": "cam-001"
  }
]
```

### `GET /api/repeat-visitors`

```json
[
  {
    "person_id": "uuid",
    "visit_count": 3,
    "first_seen": "2026-05-25T10:00:00+00:00",
    "last_seen": "2026-05-27T12:00:00+00:00"
  }
]
```

### AI ingestion

`POST /api/ingest/recognition` with body:

```json
{
  "person_id": "uuid",
  "type": "new_visitor",
  "timestamp": "2026-05-27T12:00:00+00:00",
  "camera_id": "cam-001",
  "embedding": [0.1, 0.2]
}
```

Requires `X-API-Key` when `API_KEY` is set in `.env`.

### Employee enroll from photos (multipart)

`POST /api/employees/upload`

- Form: `name` (required), `employee_id` (optional UUID)
- Files: `photos` — one or more JPEG/PNG face images

`POST /api/employees/{employee_id}/re-enroll` — replace embedding from new photos.

`PATCH /api/employees/{employee_id}` — `{ "name": "...", "active": false }` to deactivate.

### Customer enroll from photos

`POST /api/customers/{customer_id}/enroll-photo` — multipart `photos`.

Embeddings are generated server-side via InsightFace (`shared/face_enrollment.py`).

## Run

```powershell
.\scripts\setup_local.ps1
python scripts/seed_identity_demo.py
uvicorn backend_core.main:app --reload --port 8000
cd dashboard-ui && npm run dev
```

Dashboard pages: **Customers**, **Logs**, **Repeat / New**, **Employees**.

Phase 1 retail analytics (`/api/live-visitors`, footfall) unchanged. Store visitor list uses `/api/store-recognitions`.
