"""
RBAC middleware and dependency — Module 10 (Phase 4).

Roles hierarchy (broadest → narrowest):
  super_admin > brand_admin > store_manager > staff_viewer

Usage:
    @router.get("/admin-only")
    def admin(user = Depends(require_role("brand_admin"))):
        ...
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend_core.auth.jwt_tokens import decode_access_token
from shared.config import Settings, get_settings
from shared.database.audit_models import AuditLog

logger = logging.getLogger(__name__)

# Role hierarchy — higher index = more privilege
ROLE_HIERARCHY = ["staff_viewer", "store_manager", "brand_admin", "super_admin"]

bearer_scheme = HTTPBearer(auto_error=False)


def _role_level(role: str) -> int:
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1


class UserContext:
    """Resolved user context from JWT with RBAC role."""

    def __init__(
        self,
        user_id: Optional[str],
        brand_id: Optional[str],
        store_id: Optional[str],
        role: str,
        email: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.brand_id = brand_id
        self.store_id = store_id
        self.role = role
        self.email = email

    def has_role(self, required_role: str) -> bool:
        return _role_level(self.role) >= _role_level(required_role)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    """Dependency — resolves JWT to UserContext with role."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    try:
        payload = decode_access_token(settings, credentials.credentials)
        return UserContext(
            user_id=payload.get("user_id"),
            brand_id=payload.get("brand_id"),
            store_id=payload.get("store_id"),
            role=payload.get("role", "staff_viewer"),
            email=payload.get("email"),
        )
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc


def require_role(minimum_role: str) -> Callable:
    """
    Dependency factory — enforces minimum role requirement.

    Example:
        @router.post("/admin")
        def create(user = Depends(require_role("brand_admin"))):
    """

    def _dependency(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(minimum_role):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Role '{minimum_role}' required; you have '{user.role}'",
            )
        return user

    return _dependency


def log_audit_event(
    db,
    *,
    actor: str,
    action: str,
    brand_id=None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Write to the existing AuditLog table."""
    try:
        entry = AuditLog(
            brand_id=brand_id,
            actor=actor,
            action=action,
            resource=resource,
            ip_address=ip_address,
            details=details or {},
        )
        db.add(entry)
        db.flush()
    except Exception as exc:
        logger.warning("Audit log write failed: %s", exc)
