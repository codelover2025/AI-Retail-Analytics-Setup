# Jetson / edge tuning (Phase 2)

## Environment

```env
INSIGHTFACE_CTX_ID=0
DET_SIZE=640
MIN_FACE_SCORE=0.6
MIN_BBOX_AREA=1600
RECOGNITION_THRESHOLD=0.55
TRACK_EMBED_MIN_FRAMES=3
USE_FAISS=true
FAISS_MIN_GALLERY_SIZE=50
```

Map `track_embed_min_frames` → `TRACK_EMBED_MIN_FRAMES` in `.env` if using pydantic alias — default field: `track_embed_min_frames`.

## Recommendations

| Setting | Jetson Orin | Windows CPU dev |
|---------|-------------|-----------------|
| `INSIGHTFACE_CTX_ID` | `0` | `-1` |
| `FRAME_SKIP` | `2–4` | `2` |
| `DET_SIZE` | `640` | `640` (lower if slow) |
| `track_embed_min_frames` | `3` | `3` |
| `use_faiss` | `true` when gallery > 50 | optional |

## CLI enroll (no API)

```bash
python -m edge_ai.pipeline.enroll --image staff.jpg --kind employee --label E001
```

## Gallery scale

- &lt; 50 faces: linear cosine scan  
- ≥ 50 faces: FAISS inner-product index (`pip install faiss-cpu`)
