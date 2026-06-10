"""
Health check API — Module 12 (Phase 4).

Endpoints:
  GET /api/v1/health/detailed — per-subsystem health status
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.config import Settings, get_settings
from shared.database.session import get_db

router = APIRouter(prefix="/api/v1/health", tags=["health"])

_start_time = time.monotonic()


@router.get("/detailed", summary="Detailed subsystem health check")
async def detailed_health(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """
    Returns health status for each subsystem:
    - Database (PostgreSQL/SQLite)
    - Redis
    - WhatsApp provider
    - HRMS provider
    - POS provider
    - CRM provider
    """
    results: dict = {
        "status": "ok",
        "version": "4.0.0",
        "phase": 4,
        "env": settings.app_env,
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subsystems": {},
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        results["subsystems"]["database"] = {"status": "ok", "type": db.bind.dialect.name}  # type: ignore
    except Exception as exc:
        results["subsystems"]["database"] = {"status": "error", "error": str(exc)[:100]}
        results["status"] = "degraded"

    # Redis check
    try:
        if settings.redis_url:
            import redis  # type: ignore
            r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
            r.ping()
            r.close()
            results["subsystems"]["redis"] = {"status": "ok"}
        else:
            results["subsystems"]["redis"] = {"status": "not_configured"}
    except Exception as exc:
        results["subsystems"]["redis"] = {"status": "error", "error": str(exc)[:80]}
        results["status"] = "degraded"

    # WhatsApp provider
    wa_provider = settings.whatsapp_provider
    wa_configured = bool(settings.whatsapp_phone_number_id and settings.whatsapp_access_token)
    results["subsystems"]["whatsapp"] = {
        "status": "ok" if wa_configured else "not_configured",
        "provider": wa_provider,
    }

    # HRMS provider
    hrms_provider = settings.hrms_provider
    results["subsystems"]["hrms"] = {
        "status": "configured" if hrms_provider else "not_configured",
        "provider": hrms_provider or "stub",
    }

    # POS provider
    pos_provider = settings.pos_provider
    results["subsystems"]["pos"] = {
        "status": "configured" if pos_provider else "not_configured",
        "provider": pos_provider or "stub",
    }

    # CRM provider
    crm_provider = settings.crm_provider
    results["subsystems"]["crm"] = {
        "status": "configured" if crm_provider else "not_configured",
        "provider": crm_provider or "stub",
    }

    return results
