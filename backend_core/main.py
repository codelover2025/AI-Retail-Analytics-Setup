import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_core.api.identity_routes import router as identity_router
from backend_core.api.routes import router as api_router
from backend_core.api.multi_camera_routes import router as multi_camera_router
from backend_core.api.v1 import api_v1
from backend_core.api.websocket import router as ws_router
from backend_core.api.stream import router as stream_router  # Phase 4 SSE
from shared.config import get_settings
from shared.database.session import init_db

# Phase 4 routers (included at app level — paths: /api/dashboard/..., /stream/...)
from backend_core.api.v1.dashboard import router as dashboard_router
from backend_core.api.v1.reports import router as reports_router
from backend_core.api.v1.heatmap import router as heatmap_router
from backend_core.api.v1.alerts import router as alerts_router
from backend_core.api.v1.hrms import router as hrms_router
from backend_core.api.v1.pos import router as pos_router
from backend_core.api.v1.crm import router as crm_router
from backend_core.api.v1.rbac import router as rbac_router
from backend_core.api.v1.health import router as health_router

# Phase 5 routers & security middleware
from backend_core.api.v1.ai_assistant import router as ai_assistant_router
from backend_core.api.v1.voice import router as voice_router
from backend_core.api.v1.analytics_ai import router as analytics_ai_router
from backend_core.api.v1.recommendation_alert import router as recs_alerts_router
from backend_core.auth.security_helpers import RateLimitingMiddleware

settings = get_settings()

# ---------------------------------------------------------------------------
# Structured logging (Phase 4)
# ---------------------------------------------------------------------------

_log_handlers: list[logging.Handler] = []

if settings.log_format == "json":
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore

        handler = logging.StreamHandler()
        handler.setFormatter(
            jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        )
        _log_handlers.append(handler)
    except ImportError:
        pass

if not _log_handlers:
    logging.basicConfig(level=settings.log_level)
else:
    logging.basicConfig(level=settings.log_level, handlers=_log_handlers)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Orzen Vision API",
    description="Phase 4: Enterprise retail analytics — dashboard, realtime, reports, heatmap, RBAC, integrations",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=60)
# ---------------------------------------------------------------------------
# Routers (Phase 1-3 unchanged + Phase 4 additions)
# ---------------------------------------------------------------------------

app.include_router(api_v1)             # Phase 1-3: /api/v1/...
app.include_router(identity_router)    # Phase 2 identity
app.include_router(api_router)         # Phase 3 multi-camera
app.include_router(multi_camera_router)
app.include_router(ws_router)          # Phase 1 WebSocket
app.include_router(stream_router)      # Phase 4 SSE: /stream/...

# Phase 4: /api/dashboard/..., /api/reports/..., etc.
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(heatmap_router)
app.include_router(alerts_router)
app.include_router(hrms_router)
app.include_router(pos_router)
app.include_router(crm_router)
app.include_router(rbac_router)
app.include_router(health_router)

# Phase 5 API routers
app.include_router(ai_assistant_router)
app.include_router(voice_router)
app.include_router(analytics_ai_router)
app.include_router(recs_alerts_router)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

_startup_time = time.monotonic()


@app.on_event("startup")
def on_startup() -> None:
    init_db()

    # Phase 4 and Phase 5 migrations (additive, idempotent)
    try:
        from shared.database.migrations import ensure_phase4_columns, ensure_phase5_columns
        ensure_phase4_columns()
        ensure_phase5_columns()
        logger.info("Phase 4 and Phase 5 migrations applied")
    except Exception as exc:
        logger.error("Migration error: %s", exc)

    # Start report scheduler (APScheduler)
    try:
        from backend_core.services.report_scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:
        logger.warning("Report scheduler startup skipped: %s", exc)

    logger.info(
        "Orzen Vision API v4.0 started | env=%s | log_format=%s",
        settings.app_env,
        settings.log_format,
    )


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health():
    """Basic liveness probe."""
    return {
        "status": "ok",
        "phase": 5,
        "version": "5.0.0",
        "uptime_seconds": round(time.monotonic() - _startup_time, 1),
    }


@app.get("/api/v1/health", tags=["health"])
def health_v1():
    """Legacy health endpoint (v1 compat)."""
    return {"status": "ok", "phase": 5}


def run() -> None:
    import uvicorn

    uvicorn.run("backend_core.main:app", host="0.0.0.0", port=8000, reload=False)
