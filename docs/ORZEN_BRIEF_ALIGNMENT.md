# Orzen Vision — brief alignment

Source: `Orzen_Vision_Freelance_Brief.docx` (jewellery retail AI camera analytics).

**Phase 1 progress:** [PHASE1_STATUS.md](./PHASE1_STATUS.md) (commercial deliverable ~92% · full brief ~25%).

This repo implements the **edge inference + recognition + tracking + backend APIs + PostgreSQL** slice. Dashboard, WhatsApp, HRMS/POS/CRM, and LLM layers are **out of scope here** but listed below for integration points.

---

## Mandatory capabilities vs this repo

| Brief requirement | Status | Notes / integration point |
|-------------------|--------|---------------------------|
| **VIP recognition + real-time alert** | Partial | `Visitor.is_vip`, `AlertEngine` (`vip_detected`), `GET /api/alerts` |
| **Watch-list / blacklist** | Not started | Needs `watchlist` flag, documented case metadata, alert `watchlist_match` |
| **Employee vs customer** | Not started | Needs `employees` table + HRMS sync; exclude staff from footfall |
| **Customer profile on arrival** | Partial | `Visitor` + recognitions; no CRM fields (categories, LTV, notes) yet |
| **Consent (enrol, opt-out, audit)** | Not started | DPDP: `ConsentRecord` + retention job; embeddings-only already aligned |
| **Indian demographics tuning** | Partial | InsightFace `buffalo_l`; brief asks fine-tune — production may need custom model |
| **Multi-store chain memory** | Partial | `brand_id` + tenant tables done; cross-store embedding match in Phase 2 |
| **Real-time walk-in count** | Done | `GET /api/live-visitors` |
| **Demographics (anonymous aggregate)** | Not started | Age/gender model + aggregate tables (no PII) |
| **Journey / zones / dwell** | Not started | Zone config + person tracking + timestamps per zone |
| **Repeat visitor / frequency** | Partial | `visit_count`, `repeat_visitor` alert, recognitions API |
| **Heat maps** | Not started | Zone dwell aggregates → API for dashboard |
| **HRMS staff tracking** | Not started | External HRMS → employee registry + presence API |
| **Staff–customer ratio / coverage** | Not started | Depends on zones + employee tracks |
| **WhatsApp alerts** | Not started | Backend webhook/worker consuming `alerts` + Gupshup/AiSensy |
| **Dashboards** | Partial | `dashboard-ui/` starter (Phase 1); full brief UX in Phase 4 |
| **LLM reasoning** | Out of scope | Orzen-provided model; query API over analytics DB |
| **HRMS / POS / CRM / ERP** | Not started | OpenAPI + sync jobs; VIP/watchlist from CRM |
| **Predictive (footfall, VIP)** | Not started | Batch jobs on `footfall_daily` + calendar features |
| **Edge-first, metadata only** | Done | RTSP on edge; embeddings + metadata to Postgres; no video upload |
| **Multi-tenant SaaS** | Partial (Phase 1) | `brand_id` + brands/stores/cameras/edge_devices; India cloud deploy TBD |
| **DPDP (retention, deletion, audit)** | Partial | Embeddings-only; need retention policy + audit log tables |

---

## Technical architecture (brief §3)

| Brief | This repo |
|-------|-----------|
| Jetson / DeepStream edge | Portable Python edge (`edge_ai/`); DeepStream adapter TBD |
| YOLO person + face | InsightFace detect+embed; ByteTrack for faces |
| FastAPI + PostgreSQL + Redis | Yes (`backend_core/`, `shared/`, optional Redis pub/sub) |
| ClickHouse / TimescaleDB | Not used; hourly footfall via SQL `date_trunc` on Postgres |
| Kubernetes | Not in repo; Docker Compose for dev |
| Hikvision / CP Plus / Dahua | RTSP URLs via OpenCV (`RTSPStream`) |

---

## API contract (dashboard-facing)

Strict contract implemented in `backend_core/schemas/contract.py`:

- `GET /api/live-visitors` → `{ count, timestamp }`
- `GET /api/recognitions` → `[{ id, type, time }]`
- `GET /api/footfall` → `{ daily, hourly }`
- `GET /api/alerts` → `[{ type, message, time }]`

Extend with Orzen-specific types when watchlist/employee/consent land, e.g. `type`: `watchlist`, `employee_present`.

---

## Recommended build phases (backend + edge only)

### Phase 1 — Recognition & compliance core (aligns with brief priority)
- `brand_id` on all tenant-scoped tables
- Visitor roles: `customer` | `vip` | `watchlist` | `employee`
- `ConsentRecord` + embedding retention / deletion jobs
- Alerts: `watchlist_match`, enrich VIP payload for CRM hook
- Cross-store match: `find_best_match` scoped by `brand_id`

### Phase 2 — Floor analytics
- Zone definitions per store
- Person detection (YOLO) + track IDs linked to face tracks
- Dwell events → TimescaleDB or partitioned Postgres
- APIs: zone dwell, journey, entry-to-engagement (feeds dashboard)

### Phase 3 — Integrations & delivery
- HRMS sync (employee photos → embeddings)
- CRM sync (VIP/watchlist enrolment)
- WhatsApp alert dispatcher (reads `alerts`)
- Webhook/OpenAPI for ERP

### Phase 4 — Intelligence
- Footfall / VIP prediction jobs
- LLM query service over read replicas (Orzen model)

---

## Privacy checklist (brief §4)

| Rule | Implementation target |
|------|------------------------|
| Explicit VIP consent | `ConsentRecord` before `register_visitor` |
| Embeddings only | Already: `Visitor.embedding` JSONB |
| Encryption at rest/transit | Infra (RDS TLS, disk encryption); app-level field encryption optional |
| 12-month default retention | Scheduled purge job |
| Opt-out / delete within 30 days | `delete_visitor_data(visitor_id)` |
| Audit every PII access | `audit_log` table on API + admin actions |
| Watchlist 24-month max | TTL on watchlist rows |
| Employee consent | HRMS contract flag → `employee.consent_at` |

---

## What to build next (suggested)

1. **Schema**: `brand_id`, visitor `kind`, `ConsentRecord`, `AuditLog`
2. **Recognition**: watchlist match + employee exclusion from footfall
3. **Alerts**: map brief alert types to `alert_type` enum
4. **CRM hook**: stub `GET /api/visitors/{id}/profile` for manager UI (optional)

Confirm with Orzen which phase to fund first; dashboard and WhatsApp can parallelize once Phase 1 APIs are stable.
