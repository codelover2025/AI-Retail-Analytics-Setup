# Edge identity pipeline (Phase 2 AI)

Modular facial recognition — **no HTTP APIs** in this package.

## Flow

```
RTSP frame → FaceProcessor (InsightFace, score ≥ 0.6, 512-d)
          → ByteTrack (in parent pipeline.py)
          → IdentityService.resolve()
          → IdentityEvent { person_id, type, camera_id, timestamp }
```

## Modules

| File | Role |
|------|------|
| `face_processor.py` | InsightFace detect + embed, quality gate |
| `matcher.py` | Cosine similarity vs customer/employee galleries |
| `identity_service.py` | Match → person_id; `repeat_visitor` only if `visit_count > 1` |
| `store.py` | Load/save embeddings + `person_id` in `Visitor.metadata` |
| `enroll.py` | CLI manual enrollment |

## Config (`.env`)

```env
MIN_FACE_SCORE=0.6
MIN_BBOX_AREA=1600
RECOGNITION_THRESHOLD=0.55
FRAME_SKIP=2
```

Recognitions persist `match_score` + `identity_type`. Employees skip footfall and `visit_count`.

## Enroll employee (manual)

```powershell
python -m edge_ai.pipeline.enroll path\to\face.jpg --kind employee --label E001
```

## Output example

```json
{
  "person_id": 42,
  "type": "repeat_visitor",
  "camera_id": "cam-001",
  "timestamp": "2026-05-21T12:00:00+00:00",
  "visitor_id": "uuid-...",
  "match_score": 0.61,
  "is_new_person": false
}
```
