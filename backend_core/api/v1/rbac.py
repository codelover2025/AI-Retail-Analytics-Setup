"""
RBAC API — Module 10 (Phase 4).

Endpoints:
  POST /api/auth/register     — create user (super_admin only)
  POST /api/auth/login        — issue JWT with role claim
  GET  /api/rbac/users        — list users (brand_admin+)
  PATCH /api/rbac/users/{id}/role — change role (super_admin)
  GET  /api/rbac/audit-logs   — audit trail (brand_admin+)
"""

from __future__ import annotations

# Workaround for passlib + bcrypt compatibility on Python 3.13+
import bcrypt
import types
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = types.ModuleType("__about__")
    bcrypt.__about__.__version__ = getattr(bcrypt, "__version__", "unknown")
_orig_hashpw = bcrypt.hashpw
bcrypt.hashpw = lambda pw, salt: _orig_hashpw(pw[:72] if len(pw) > 72 else pw, salt)

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.auth.jwt_tokens import create_access_token
from backend_core.auth.rbac import (
    UserContext,
    log_audit_event,
    require_role,
)
from shared.config import Settings, get_settings
from shared.database.audit_models import AuditLog
from shared.database.rbac_models import User
from shared.database.session import get_db

router = APIRouter(tags=["rbac"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: str = Field(..., description="super_admin|brand_admin|store_manager|staff_viewer")
    brand_id: Optional[str] = None
    store_id: Optional[str] = None
    brand_slug: Optional[str] = None
    store_external_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangeRoleRequest(BaseModel):
    role: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/api/auth/register", status_code=201, summary="Register a new platform user")
def register_user(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    caller: UserContext = Depends(require_role("super_admin")),
    settings: Settings = Depends(get_settings),
):
    """Create a new user (requires super_admin role)."""
    from passlib.context import CryptContext  # type: ignore
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    valid_roles = {"super_admin", "brand_admin", "store_manager", "staff_viewer"}
    if body.role not in valid_roles:
        raise HTTPException(400, f"role must be one of {valid_roles}")

    existing = db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(409, "Email already registered")

    # Resolve brand_slug if brand_id not provided
    brand_id = None
    if body.brand_id:
        brand_id = uuid.UUID(body.brand_id)
    elif body.brand_slug:
        from shared.database.tenant_models import Brand
        brand = db.scalar(select(Brand).where(Brand.slug == body.brand_slug))
        if brand:
            brand_id = brand.id

    # Resolve store_external_id if store_id not provided
    store_id = body.store_id
    if not store_id and body.store_external_id and brand_id:
        from shared.database.tenant_models import Store
        store = db.scalar(
            select(Store).where(Store.brand_id == brand_id, Store.external_id == body.store_external_id)
        )
        if store:
            store_id = str(store.id)

    user = User(
        brand_id=brand_id,
        store_id=store_id,
        email=body.email,
        hashed_password=pwd_ctx.hash(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    log_audit_event(
        db,
        actor=caller.email or "system",
        action="user.register",
        brand_id=brand_id,
        resource=f"user:{user.id}",
        details={"email": body.email, "role": body.role},
    )
    db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.post("/api/rbac/register", status_code=201, summary="Register a new platform user (rbac alias)")
def register_user_rbac(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    caller: UserContext = Depends(require_role("super_admin")),
    settings: Settings = Depends(get_settings),
):
    """Register a new platform user (alias for frontend compatibility)."""
    return register_user(body, db, caller, settings)


@router.post("/api/auth/login", summary="Login and receive JWT")
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Authenticate with email/password and receive a signed JWT."""
    from passlib.context import CryptContext  # type: ignore
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not pwd_ctx.verify(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account deactivated")

    user.last_login_at = datetime.utcnow()
    db.commit()

    brand_slug = ""
    if user.brand_id:
        from shared.database.tenant_models import Brand
        brand = db.get(Brand, user.brand_id)
        if brand:
            brand_slug = brand.slug

    token = create_access_token(
        settings,
        brand_id=str(user.brand_id) if user.brand_id else "",
        brand_slug=brand_slug,
        store_id=user.store_id or "",
        role=user.role,
        extra={"user_id": str(user.id), "email": user.email},
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role}


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/api/rbac/users", summary="List platform users")
def list_users(
    caller: UserContext = Depends(require_role("brand_admin")),
    db: Session = Depends(get_db),
):
    """List all users for the caller's brand (brand_admin+)."""
    stmt = select(User)
    if caller.role != "super_admin" and caller.brand_id:
        stmt = stmt.where(User.brand_id == uuid.UUID(caller.brand_id))
    stmt = stmt.order_by(User.created_at.desc())
    users = list(db.scalars(stmt).all())
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "store_id": u.store_id,
            "created_at": u.created_at.isoformat(),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]


@router.patch("/api/rbac/users/{user_id}/role", summary="Change user role")
def change_user_role(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    caller: UserContext = Depends(require_role("super_admin")),
    db: Session = Depends(get_db),
):
    """Change a user's role (super_admin only)."""
    valid_roles = {"super_admin", "brand_admin", "store_manager", "staff_viewer"}
    if body.role not in valid_roles:
        raise HTTPException(400, f"role must be one of {valid_roles}")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    old_role = user.role
    user.role = body.role
    log_audit_event(
        db,
        actor=caller.email or "system",
        action="user.role_change",
        resource=f"user:{user_id}",
        details={"from": old_role, "to": body.role},
    )
    db.commit()
    return {"id": str(user.id), "role": user.role}


@router.post("/api/rbac/users/{user_id}/role", summary="Change user role (POST)")
def change_user_role_post(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    caller: UserContext = Depends(require_role("brand_admin")),
    db: Session = Depends(get_db),
):
    """Change a user's role (brand_admin+)."""
    valid_roles = {"super_admin", "brand_admin", "store_manager", "staff_viewer"}
    if body.role not in valid_roles:
        raise HTTPException(400, f"role must be one of {valid_roles}")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    # Only super_admin can assign super_admin or change a super_admin's role.
    if body.role == "super_admin" and caller.role != "super_admin":
        raise HTTPException(403, "Only super_admin can assign the super_admin role")
    if user.role == "super_admin" and caller.role != "super_admin":
        raise HTTPException(403, "Only super_admin can modify a super_admin user")

    # brand_admin can only modify users within the same brand.
    if caller.role != "super_admin":
        if not caller.brand_id or user.brand_id != uuid.UUID(caller.brand_id):
            raise HTTPException(403, "You can only change roles for users in your own brand")

    old_role = user.role
    user.role = body.role
    log_audit_event(
        db,
        actor=caller.email or "system",
        action="user.role_change",
        brand_id=user.brand_id,
        resource=f"user:{user_id}",
        details={"from": old_role, "to": body.role},
    )
    db.commit()
    return {"id": str(user.id), "role": user.role}


@router.delete("/api/rbac/users/{user_id}", summary="Deactivate user")
def deactivate_user(
    user_id: uuid.UUID,
    caller: UserContext = Depends(require_role("brand_admin")),
    db: Session = Depends(get_db),
):
    """Deactivate a user (brand_admin+)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    # Only super_admin can deactivate a super_admin.
    if user.role == "super_admin" and caller.role != "super_admin":
        raise HTTPException(403, "Only super_admin can deactivate a super_admin user")

    # brand_admin can only deactivate users within the same brand.
    if caller.role != "super_admin":
        if not caller.brand_id or user.brand_id != uuid.UUID(caller.brand_id):
            raise HTTPException(403, "You can only deactivate users in your own brand")

    user.is_active = False
    log_audit_event(
        db,
        actor=caller.email or "system",
        action="user.deactivate",
        brand_id=user.brand_id,
        resource=f"user:{user_id}",
        details={"email": user.email},
    )
    db.commit()
    return {"id": str(user.id), "is_active": user.is_active}


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

@router.get("/api/rbac/audit-logs", summary="Audit log trail")
def get_audit_logs(
    limit: int = 100,
    caller: UserContext = Depends(require_role("brand_admin")),
    db: Session = Depends(get_db),
):
    """Return recent audit log entries (brand_admin+)."""
    stmt = select(AuditLog)
    if caller.role != "super_admin" and caller.brand_id:
        stmt = stmt.where(AuditLog.brand_id == uuid.UUID(caller.brand_id))
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    rows = list(db.scalars(stmt).all())
    return [
        {
            "id": str(r.id),
            "actor": r.actor,
            "action": r.action,
            "resource": r.resource,
            "ip_address": r.ip_address,
            "details": r.details,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
