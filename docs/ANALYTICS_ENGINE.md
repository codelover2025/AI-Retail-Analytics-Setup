# Multi-Camera Analytics Engine (Phase 3)

**No APIs · No UI** — edge-only structured session output.

## Run

```powershell
# Configure cameras (2+ for multi-worker demo)
$env:CAMERAS_JSON='[{"camera_id":"cam_1","rtsp_url":"0"},{"camera_id":"cam_2","rtsp_url":"0"}]'
$env:MULTI_CAMERA_ENABLED="true"
$env:MAX_CAMERAS_PER_WORKER="3"

python -m edge_ai.analytics
```

Output: `./data/analytics_sessions.jsonl` (one JSON object per completed session).

## Architecture

```
Orchestrator
 └── WorkerGroup (≤ MAX_CAMERAS_PER_WORKER cameras)
      ├── Shared InsightFace model (locked)
      ├── Shared embedding gallery (CosineMatcher / FAISS)
      ├── Per-camera IdentityService (independent track state)
      ├── Reader threads → frame queue → processor thread
      └── AnalyticsEngine (entry/exit, dwell, zones, interaction)
```

## Output shape

```json
{
  "person_id": 42,
  "camera_id": "cam_1",
  "entry_time": "2026-05-21T12:00:00+00:00",
  "exit_time": "2026-05-21T12:05:30+00:00",
  "dwell_time": 330.0,
  "zones": ["entry", "billing"],
  "zone_time": {"entry": 120.0, "billing": 210.0},
  "interaction": true,
  "identity_type": "repeat_visitor"
}
```

## Zones

Copy `zones.json.example` → `zones.json`, or set `ZONES_JSON` in `.env`.

Centroid of face bbox → polygon assignment.

## Performance knobs

| Env | Default | Purpose |
|-----|---------|---------|
| `FRAME_SKIP` | 2 | Process every Nth frame |
| `MAX_FACES_PER_FRAME` | 5 | Cap detections |
| `MAX_CAMERAS_PER_WORKER` | 3 | Worker group size |
| `ANALYTICS_QUEUE_SIZE` | 32 | Frame queue depth |
| `ANALYTICS_EXIT_TIMEOUT_SECONDS` | 4 | Exit if not seen |
| `ANALYTICS_BATCH_INTERVAL_SECONDS` | 5 | DB commit interval |

## Rules

- No cross-camera identity merge
- No DB writes inside hot loop (batch commit only)
- Stable heuristics for 20–50 cameras (queue drop under load)

## Test (offline)

```powershell
$env:PYTHONPATH="."
python scripts/test_analytics_engine.py
```
