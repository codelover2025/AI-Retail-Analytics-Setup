# Phase 2 — Facial Recognition & Identity (Reduced / Optimized)

**Focus:** Harden recognition on top of Phase 1 edge + API — not full Orzen brief (no zones, WhatsApp, watchlist CRM, consent suite in this slice).

**Status tracker:** [PHASE2_STATUS.md](./PHASE2_STATUS.md)  
**Phase 1 baseline:** [phase 1/PHASE1_STATUS.md](./phase%201/PHASE1_STATUS.md)

---

## Commercial scope (your target)

| # | Deliverable | Intent |
|---|-------------|--------|
| 1 | **Face detection pipeline** (refined from Phase 1) | Stable detect/track under store lighting; fewer false positives |
| 2 | **Face embedding generation** | Consistent 512-d vectors, quality-gated before storage |
| 3 | **Basic recognition & matching** | Same person re-identified across tracks/sessions |
| 4 | **Repeat visitor identification** | Return visits within configurable window; API + alerts |
| 5 | **Basic customer identity creation** | Named profiles (not only `Visitor-{uuid}` auto IDs) |
| 6 | **Employee identification** | Manual enroll + tag; exclude or label staff in analytics |

---

## What Phase 1 already provides

| Area | Location | Phase 2 action |
|------|----------|----------------|
| InsightFace detect + embed | `edge_ai/detection/face_detector.py` | Tune `DET_SIZE`, score thresholds, GPU path |
| Embedding normalize/store | `edge_ai/embeddings/face_embedder.py` | Quality gate (min face size, blur optional) |
| ByteTrack face tracks | `edge_ai/tracking/byte_tracker.py` | Link track lifecycle to matcher `clear_track` |
| Cosine match + new visitor | `edge_ai/recognition/face_matcher.py` | Optional FAISS/pgvector; cross-session match |
| Visit + recognition rows | `shared/database/repository.py` | Enrich with `person_kind`, identity fields |
| Repeat alert | `edge_ai/alert_engine/events.py` + `was_repeat_within_window` | Harden window logic; dashboard type `repeat_visitor` |
| Recognition API types | `backend_core/services/analytics.py` | Add `employee`, named `customer` types |
| Multi-tenant | `brand_id` on `Visitor` | Keep all identity scoped by brand |

---

## Phase 2 build plan

### 1. Face detection pipeline (refine)

**Goals**

- Drop low-confidence / tiny faces before embed.
- Config per store: `MIN_FACE_SCORE`, `MIN_BBOX_AREA`, `DET_SIZE`.
- Log detection FPS and match latency on edge (heartbeat payload).

**Tasks**

- [ ] Add detection quality filter in `pipeline.py` before `FaceMatcher.identify`.
- [ ] Document tuning in `docs/phase 2/JETSON_TUNING.md` (Jetson vs Windows CPU).
- [ ] Optional: average embedding over N frames per track before match (reduce jitter).

**Files:** `edge_ai/pipeline.py`, `edge_ai/detection/face_detector.py`, `shared/config.py`

---

### 2. Face embedding generation

**Goals**

- One canonical embedding per enrollment (mean of 3–5 frames).
- Store version + model name in `Visitor.metadata_` for future model upgrades.

**Tasks**

- [ ] `FaceEmbedder.enroll_from_frames(frames[]) -> np.ndarray`
- [ ] Persist `embedding_model` (e.g. `insightface_buffalo_l`) and `embedding_dim` in metadata.
- [ ] Reject enroll if inter-frame similarity &lt; threshold (same person check).

**Files:** `edge_ai/embeddings/face_embedder.py`, `shared/database/models.py`

---

### 3. Basic recognition & matching

**Goals**

- Reliable same-person match within `RECOGNITION_THRESHOLD`.
- Track-level lock (already in `FaceMatcher._track_visitor`) + DB match on new track.
- Brand-scoped gallery only (`brand_id` filter — already implicit).

**Tasks**

- [ ] Refactor `find_best_match` to skip `is_employee` / inactive identities when matching customers.
- [ ] Add match audit fields on `Recognition`: `match_score`, `gallery_visitor_id`.
- [ ] Optional Phase 2b: FAISS index file per brand on edge (scale &gt; 5k faces).

**Files:** `shared/database/repository.py`, `edge_ai/recognition/face_matcher.py`

---

### 4. Repeat visitor identification

**Goals**

- Define repeat: same `visitor_id`, second+ visit within `REPEAT_VISIT_WINDOW_HOURS` (env, default 24h).
- Expose in API and alerts consistently.

**Tasks**

- [ ] Verify `was_repeat_within_window` in repository (align with `visit_count` semantics).
- [ ] API: `GET /api/v1/identity/visitors/{id}/visits` or query param `?repeat_only=true` on recognitions.
- [ ] Dashboard: repeat badge on recognition feed (optional UI slice).
- [ ] Metric: `repeat_visitors_today` on footfall summary (optional).

**Files:** `shared/database/repository.py`, `backend_core/services/analytics.py`, `edge_ai/alert_engine/events.py`

---

### 5. Basic customer identity creation

**Goals**

- Create/update customer with display name, optional phone/external ID, and face enrollment.
- Auto-created anonymous visitors remain; staff can **claim** / merge later (Phase 2 lite).

**Schema (proposed)**

```text
Visitor (extend existing)
  person_kind: customer | employee   # enum/string
  status: active | archived
  display_name, external_id, metadata_
  embedding, embedding_updated_at
```

**API (proposed)**

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/identity/customers` | `X-API-Key` + tenant headers |
| GET | `/api/v1/identity/customers` | List/search by name |
| GET | `/api/v1/identity/customers/{id}` | Profile + visit_count |
| PATCH | `/api/v1/identity/customers/{id}` | Update name/metadata |
| POST | `/api/v1/identity/customers/{id}/enroll` | multipart: 1–3 face images **or** base64 embedding |

**Edge behavior**

- On match → link track to existing `visitor_id`.
- On no match → create `person_kind=customer`, `display_name` null until enriched via API.

**Files:** new `backend_core/api/v1/identity.py`, `backend_core/services/identity.py`, migration/alembic or `scripts/migrate_phase2.py`

---

### 6. Employee identification (manual registration + tagging)

**Goals**

- Register staff with face embedding + employee code/name.
- Pipeline tags recognitions as `employee`; **exclude from unique footfall** (brief alignment).
- Optional alert: `employee_present` (not in reduced scope unless requested).

**Schema (proposed)**

Use same `Visitor` table with `person_kind=employee` **or** separate `employees` table pointing to `visitor_id` — recommended:

```text
Employee
  id, brand_id, store_id (optional home store)
  employee_code, full_name, department
  visitor_id → Visitor.embedding
  active, enrolled_at, enrolled_by
```

**API (proposed)**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/identity/employees` | Create + enroll face |
| GET | `/api/v1/identity/employees` | List active staff |
| PATCH | `/api/v1/identity/employees/{id}` | Deactivate / update |
| POST | `/api/v1/identity/employees/{id}/re-enroll` | Replace embedding |

**Pipeline**

- [ ] `FaceMatcher`: if best match is employee → set recognition type `employee`, skip `increment_unique_footfall`.
- [ ] `AnalyticsService._recognition_type` → return `"employee"`.
- [ ] Admin UI or script: `scripts/enroll_employee.py --image path.jpg --code E001`

**Files:** `shared/database/models.py`, `edge_ai/recognition/face_matcher.py`, `edge_ai/pipeline.py`, `backend_core/schemas/contract.py` (extend `RecognitionType`)

---

## Out of scope (this reduced Phase 2)

Keep for later phases / separate SOW:

- Watchlist / blacklist + case metadata  
- VIP CRM sync, WhatsApp alerts  
- DPDP consent workflows + retention jobs  
- Zone journey / dwell / heatmaps  
- HRMS auto-sync (manual employee enroll only here)  
- Indian demographic fine-tune / custom model training  
- LLM / predictive analytics  

See [phase 1/ORZEN_BRIEF_ALIGNMENT.md](./phase%201/ORZEN_BRIEF_ALIGNMENT.md) for full product map.

---

## Suggested timeline (2 weeks, optimized)

| Week | Focus |
|------|--------|
| **1** | Schema + identity APIs (customer + employee enroll); pipeline `person_kind`; footfall exclusion |
| **2** | Detection/embedding refinement; repeat visitor APIs; tests + `PHASE2_STATUS` sign-off |

---

## Acceptance criteria (sign-off)

1. Enroll customer via API with 1+ face photos → subsequent edge run matches same `visitor_id`.  
2. Enroll employee via API → edge labels recognition `employee` and does **not** increment daily unique footfall.  
3. Same customer on two visits within 24h → `repeat_visitor` alert and API `type: repeat_visitor`.  
4. New anonymous visitor still auto-created when no gallery match.  
5. `GET /api/recognitions` includes types: `new_visitor`, `repeat_visitor`, `visitor`, `employee` (and existing `vip` if enabled).  
6. Documentation: enrollment guide + env tuning in `docs/HOW_TO_RUN.md` (identity section).

---

## Environment variables (Phase 2 additions)

```env
# Recognition
RECOGNITION_THRESHOLD=0.45
REPEAT_VISIT_WINDOW_HOURS=24
MIN_FACE_SCORE=0.5
MIN_BBOX_AREA=1600

# Enrollment
ENROLLMENT_MIN_FRAMES=3
ENROLLMENT_FRAME_SIMILARITY=0.6
```

---

## Related code entry points

```
edge_ai/pipeline.py              # Main loop: detect → track → match → record
edge_ai/recognition/face_matcher.py
edge_ai/embeddings/face_embedder.py
shared/database/models.py        # Visitor, Recognition
shared/database/repository.py    # find_best_match, record_visit
backend_core/services/analytics.py
backend_core/schemas/contract.py # RecognitionType enum
```

---

*Orzen Vision — Phase 2 (Reduced) v1.0*
