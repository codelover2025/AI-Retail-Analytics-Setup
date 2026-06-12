# Enterprise Dashboard — Audit & Implementation Roadmap

**Last updated:** 2026-05-29  
**Scope:** Frontend only — consume existing Phase 4 APIs.

---

## Current State Audit

### Existing assets (reuse)

| Asset | Location | Status |
|-------|----------|--------|
| StatCard, DataTable, ErrorBanner, LoadingState | `components/` | Reuse |
| Charts (Recharts) | `charts/` | Reuse + lazy-load |
| API client + tenant headers | `services/api.ts` | Extend |
| Analytics hooks | `hooks/useDashboard`, `useFootfall`, `useMultiCameraAnalytics` | Extend |
| Identity pages | `app/customers`, `employees`, `recognitions` | Keep |
| Multi-camera page | `app/multi-camera` | Keep (camera drill-down) |

### Gaps before Phase 4 UI

| Gap | Resolution |
|-----|------------|
| No dark mode | `next-themes` + CSS variables |
| No ShadCN | `components/ui/*` primitives |
| No API caching | `lib/query-cache.ts` + `useCachedQuery` |
| No SSE/WebSocket client | `hooks/useSSE`, `hooks/useWebSocket` |
| Single flat nav | Grouped enterprise sidebar |
| No multi-store view | Module 1 → `/api/dashboard/*` |
| No executive/POS view | Module 2 → `/api/pos/analytics` |
| No report center UI | Module 6 → `/api/reports/*` |

### Backend APIs mapped to modules

| Module | Primary endpoints |
|--------|-------------------|
| 1 Multi-store | `GET /api/dashboard/overview`, `/stores`, `/comparison`, `/cameras` |
| 2 Executive | `GET /api/pos/analytics`, `/api/dashboard/comparison`, `/api/dashboard/overview` |
| 3 Staff | `GET /api/interactions`, `/api/hrms/*`, `/api/employees` |
| 4 Realtime | `GET /stream/*` (SSE), `WS /ws/live`, `/api/live-visitors`, `/api/alerts` |
| 5 Heatmap | `GET /api/heatmap/zone`, `/occupancy`, `/dwell`, `/hourly` |
| 6 Reports | `POST /api/reports/generate`, `GET /export/{id}`, `/schedule` |
| 7 Integrations | `GET /api/v1/health/detailed`, `/api/hrms/sync/*`, `/api/pos/sync`, `/api/crm/*` |
| 8 Admin | `POST /api/v1/admin/stores`, `/cameras`, identity employees |
| 9 RBAC | `GET /api/rbac/users`, `PATCH .../role`, audit logs |

---

## Implementation Phases

### Phase A — Foundation ✅ (this sprint)
- Design tokens (light/dark)
- ShadCN primitives
- `PageShell`, `FilterBar`, `KpiGrid`
- API service layer + query cache
- Enterprise navigation shell

### Phase B — Core analytics (Modules 1–2)
- Multi-store dashboard with filters
- Executive CEO view with revenue/conversion

### Phase C — Operations (Modules 3–5)
- Staff performance, interactions, attendance
- Realtime SSE panels
- Interactive heatmap

### Phase D — Platform (Modules 6–9)
- Report center (generate/schedule/download)
- Integration status center
- Admin + RBAC matrix

### Phase E — Polish (Modules 10–12)
- Tablet/mobile breakpoints
- Route-level code splitting
- Chart virtualization for 50+ cameras

---

## Module checklist

- [x] M11 Design system
- [x] M12 Performance primitives
- [x] M1 Multi-store dashboard
- [x] M2 Executive dashboard
- [x] M3 Staff analytics
- [x] M4 Realtime monitoring
- [x] M5 Heatmap
- [x] M6 Report center
- [x] M7 Integration center
- [x] M8 Admin panel
- [x] M9 Role management
- [x] M10 Responsive layout

---

## Conventions

- All pages use `PageShell` + `FilterBar` where applicable
- Charts loaded via `next/dynamic({ ssr: false })`
- API reads go through `useCachedQuery` (60s default TTL)
- No new backend routes from frontend work
