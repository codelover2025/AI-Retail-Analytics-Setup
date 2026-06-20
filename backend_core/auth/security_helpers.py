"""Security helpers for rate limiting and audit trails (Phase 5)."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from shared.database.audit_models import AuditLog

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Lightweight, sliding-window rate limiting middleware.
    Protects sensitive AI and Assistant endpoints.
    """

    def __init__(self, app: Any, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Simple in-memory rate limit store: maps client_ip -> list of timestamps
        self._store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Rate limit only AI assistant and voice endpoints
        if not request.url.path.startswith("/api/v1/ai"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown-ip"
        now = time.time()
        
        # Clean expired timestamps (older than 60 seconds)
        timestamps = self._store.get(client_ip, [])
        timestamps = [ts for ts in timestamps if now - ts < 60.0]
        
        if len(timestamps) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded for client IP: %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Maximum 60 requests per minute are allowed on AI endpoints."
                }
            )

        timestamps.append(now)
        self._store[client_ip] = timestamps
        
        return await call_next(request)


def log_audit_event(
    db: Session,
    brand_id: Optional[uuid.UUID],
    actor: str,
    action: str,
    resource: str,
    ip_address: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """Inserts a record into the audit_logs table for DPDP compliance."""
    try:
        log = AuditLog(
            brand_id=brand_id,
            actor=actor,
            action=action,
            resource=resource,
            ip_address=ip_address or "0.0.0.0",
            details=details or {}
        )
        db.add(log)
        db.commit()
        return log
    except Exception as exc:
        db.rollback()
        logger.error("Failed to write audit log event: %s", exc)
        raise
