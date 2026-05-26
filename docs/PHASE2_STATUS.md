# Phase 2 status — Facial Recognition & Identity (Reduced)

**Scope doc:** [PHASE2.md](./PHASE2.md)  
**Last updated:** 2026-05-21  
**Code:** `edge_ai/pipeline/`

Legend: **Done** · **Partial** · **Not started** · N/A (out of AI-only scope)

---

## Executive summary

| Scope | Completion | Notes |
|-------|------------|--------|
| **Your 5-point AI / identity spec** | **100%** | All items in `edge_ai/pipeline/` |
| **Small gaps (bbox, match_score, employee footfall, API type)** | **100%** | Closed 2026-05-21 |
| **Full PHASE2.md commercial plan** | **~65%** | HTTP identity APIs, Jetson doc, FAISS still open |
| **AI-only slice (no APIs/UI)** | **~95%** | Optional: FAISS at scale |

---

## Your 5-point spec — completeness

| # | Requirement | Status |
|---|-------------|--------|
| 1 | InsightFace + 512-d + skip &lt; 0.6 | **Done** |
| 2 | Cosine match 0.5–0.6, person_id or new | **Done** |
| 3 | Match / new / `visit_count > 1` repeat | **Done** |
| 4 | Employee gallery + override | **Done** |
| 5 | Structured `IdentityEvent` output | **Done** |

---

## Small gaps — all closed

| Gap | Fix |
|-----|-----|
| `MIN_BBOX_AREA` | `shared/config.py` + `FaceProcessor.bbox_area()` |
| `match_score` on DB | `Recognition.match_score` + migration in `init_db` |
| Employee footfall | `record_visit(count_footfall=False, increment_visit=False)` for `employee` |
| API `employee` type | `RecognitionType` + `analytics._recognition_type()` |
| Embedding model metadata | `Visitor.metadata`: `embedding_model`, `embedding_dim` |
| `enroll_from_frames()` | `FaceEmbedder.enroll_from_frames()` |
| Employee VIP alerts | Skipped in `AlertEngine` for `person_kind=employee` |

---

## Commercial checklist (PHASE2.md)

### 1. Face detection pipeline

| ID | Task | Status |
|----|------|--------|
| 1.1 | Min score filter | **Done** |
| 1.2 | `MIN_FACE_SCORE` + `MIN_BBOX_AREA` | **Done** |
| 1.3 | Multi-frame embed average per track | Not started |
| 1.4 | Jetson/CPU tuning doc | Not started |

### 2. Face embedding generation

| ID | Task | Status |
|----|------|--------|
| 2.1 | `enroll_from_frames()` | **Done** |
| 2.2 | Model name in metadata | **Done** |
| 2.3 | Enrollment same-person validation | **Done** (in `enroll_from_frames`) |
| 2.4 | CLI enroll | **Done** |

### 3. Recognition & matching

| ID | Task | Status |
|----|------|--------|
| 3.1–3.3 | Detect, cosine, track lock | **Done** |
| 3.4 | `match_score` on `Recognition` | **Done** |
| 3.5 | Employee vs customer galleries | **Done** |
| 3.6 | FAISS (optional) | Not started |

### 4. Repeat visitor

| ID | Task | Status |
|----|------|--------|
| 4.1–4.3, 4.5 | Edge + API typing | **Done** |
| 4.4 | History API | Not started (HTTP scope) |

### 5. Customer identity

| ID | Task | Status |
|----|------|--------|
| 5.1–5.2, 5.6 | Auto ID + metadata + CLI | **Done** |
| 5.3–5.5 | HTTP APIs | Not started |

### 6. Employee identification

| ID | Task | Status |
|----|------|--------|
| 6.1, 6.3–6.5 | Metadata, CLI, pipeline tag, footfall | **Done** |
| 6.2, 6.6 | HTTP API | Partial — **API type `employee` done**; REST enroll not started |

---

## Verify

```powershell
$env:PYTHONPATH="."
python scripts\test_identity_matcher.py
python scripts\test_identity_visit_count.py
python scripts\test_face_processor_quality.py
python -c "from shared.database.session import init_db; init_db(); print('db ok')"
```

---

*Orzen Vision — Phase 2 status v3.0*
