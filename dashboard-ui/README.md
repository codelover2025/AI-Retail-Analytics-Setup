# Orzen Vision — Dashboard UI

Next.js dashboard that consumes the Phase 1 FastAPI analytics APIs.

## Prerequisites

- Backend running: `uvicorn backend_core.main:app --reload --port 8000`
- Seed data: `.\scripts\setup_local.ps1` (optional edge pipeline for live data)

## Setup

```bash
cd dashboard-ui
cp .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000** (if the terminal says port **3001**, use that URL instead).

If the page stays blank: stop all `npm run dev` windows, delete `dashboard-ui/.next`, and start again. Keep the backend on **http://localhost:8000** (not `0.0.0.0` in the browser).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | FastAPI base URL |
| `NEXT_PUBLIC_API_KEY` | — | `X-API-Key` (match backend `API_KEY`) |
| `NEXT_PUBLIC_BRAND_SLUG` | `orzen-demo` | Tenant header |
| `NEXT_PUBLIC_STORE_ID` | `store-001` | Store header |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | `10000` | Live polling interval |

## API endpoints (fixed contract)

- `GET /api/live-visitors`
- `GET /api/recognitions`
- `GET /api/footfall`
- `GET /api/alerts`

## Branding

Official logos are copied from `../Orzen Logo/` into `public/branding/`:

- `orzen-logo-primary.png` — sidebar & mobile header (Standard Black)
- `orzen-icon.png` — favicon / app icon (Brand Mark)

Component: `components/OrzenLogo.tsx`

## Structure

| Path | Role |
|------|------|
| `app/` | Routes (Dashboard, Visitors, Alerts, Analytics) |
| `components/` | Stat cards, tables, alerts, layout |
| `charts/` | Recharts visualizations |
| `services/` | Axios client + API fetchers |
| `hooks/` | Polling hooks |
| `utils/` | Formatting + KPI processors |
| `../analytics-services/` | Footfall, dwell proxy, reports |

## Real-time updates

Uses **polling** every 10s (configurable). WebSocket support can be added when Redis alerts channel is enabled on the backend.
