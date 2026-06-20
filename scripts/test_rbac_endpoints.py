"""Tests for user RBAC endpoints."""
from __future__ import annotations

# Workaround for passlib + bcrypt compatibility on Python 3.13+
import bcrypt
import types
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = types.ModuleType("__about__")
    bcrypt.__about__.__version__ = getattr(bcrypt, "__version__", "unknown")
_orig_hashpw = bcrypt.hashpw
bcrypt.hashpw = lambda pw, salt: _orig_hashpw(pw[:72] if len(pw) > 72 else pw, salt)

import sys
import uuid
from pathlib import Path

# Resolve root path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend_core.main import app
from backend_core.auth.rbac import get_current_user, UserContext
from shared.database.models import Base
from shared.database.rbac_models import User
from shared.database.tenant_models import Brand, Store
from shared.database.audit_models import AuditLog
from shared.database.session import get_db

# Setup file-based test database
db_path = Path("./test_rbac.db")
if db_path.exists():
    try:
        db_path.unlink()
    except Exception:
        pass

test_engine = create_engine("sqlite:///./test_rbac.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

# Make sure only the needed tables are created
Brand.__table__.create(bind=test_engine)
User.__table__.create(bind=test_engine)
AuditLog.__table__.create(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Global context mocker helper
current_caller = UserContext(user_id=None, brand_id=None, store_id=None, role="staff_viewer", email="test@system.com")

def override_get_current_user():
    return current_caller

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_rbac_flow():
    global current_caller
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    db = TestingSessionLocal()

    # Seed Brands
    brand_a_id = uuid.uuid4()
    brand_b_id = uuid.uuid4()
    
    brand_a = Brand(id=brand_a_id, slug="brand-a", name="Brand A")
    brand_b = Brand(id=brand_b_id, slug="brand-b", name="Brand B")
    db.add_all([brand_a, brand_b])
    db.commit()

    # Seed users
    u_super = User(id=uuid.uuid4(), email="super@system.com", hashed_password="dummy", role="super_admin", is_active=True)
    u_brand_a = User(id=uuid.uuid4(), brand_id=brand_a_id, email="admin_a@brand-a.com", hashed_password="dummy", role="brand_admin", is_active=True)
    u_brand_b = User(id=uuid.uuid4(), brand_id=brand_b_id, email="admin_b@brand-b.com", hashed_password="dummy", role="brand_admin", is_active=True)
    u_staff_a = User(id=uuid.uuid4(), brand_id=brand_a_id, email="staff_a@brand-a.com", hashed_password="dummy", role="staff_viewer", is_active=True)
    
    db.add_all([u_super, u_brand_a, u_brand_b, u_staff_a])
    db.commit()

    print("--- 1. Testing Registration Endpoint ---")
    
    # 1.a Non-super_admin registration should fail
    current_caller = UserContext(
        user_id=str(u_brand_a.id),
        brand_id=str(brand_a_id),
        store_id=None,
        role="brand_admin",
        email=u_brand_a.email
    )
    
    r = client.post("/api/rbac/register", json={
        "email": "new_staff@brand-a.com",
        "password": "supersecurepassword",
        "role": "staff_viewer"
    })
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    
    # 1.b Super admin registration should succeed
    current_caller = UserContext(
        user_id=str(u_super.id),
        brand_id=None,
        store_id=None,
        role="super_admin",
        email=u_super.email
    )
    
    r = client.post("/api/rbac/register", json={
        "email": "new_staff@brand-a.com",
        "password": "supersecurepassword",
        "role": "staff_viewer",
        "brand_slug": "brand-a"
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}"
    
    # Verify registered user brand_id was resolved from brand_slug
    reg_user = db.scalar(select(User).where(User.email == "new_staff@brand-a.com"))
    assert reg_user is not None
    assert reg_user.brand_id == brand_a_id
    
    # Verify registration audit log
    audit_reg = db.scalar(select(AuditLog).where(AuditLog.action == "user.register"))
    assert audit_reg is not None
    assert audit_reg.actor == u_super.email
    assert f"user:{reg_user.id}" in audit_reg.resource

    print("--- 2. Testing Role Update (POST /api/rbac/users/{id}/role) ---")
    
    # 2.a brand_admin promoting/demoting user in own brand (A) should succeed
    current_caller = UserContext(
        user_id=str(u_brand_a.id),
        brand_id=str(brand_a_id),
        store_id=None,
        role="brand_admin",
        email=u_brand_a.email
    )
    
    r = client.post(f"/api/rbac/users/{u_staff_a.id}/role", json={"role": "store_manager"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    
    db.refresh(u_staff_a)
    assert u_staff_a.role == "store_manager"
    
    # Verify role change audit log
    audit_role = db.scalar(select(AuditLog).where(AuditLog.action == "user.role_change"))
    assert audit_role is not None
    assert audit_role.actor == u_brand_a.email
    assert audit_role.details.get("to") == "store_manager"
    
    # 2.b brand_admin trying to promote to super_admin should fail (403)
    r = client.post(f"/api/rbac/users/{u_staff_a.id}/role", json={"role": "super_admin"})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    
    # 2.c brand_admin modifying user in brand B should fail (403)
    r = client.post(f"/api/rbac/users/{u_brand_b.id}/role", json={"role": "store_manager"})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    
    # 2.d brand_admin modifying super_admin user should fail (403)
    r = client.post(f"/api/rbac/users/{u_super.id}/role", json={"role": "brand_admin"})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"

    # 2.e super_admin promoting brand_admin to super_admin should succeed
    current_caller = UserContext(
        user_id=str(u_super.id),
        brand_id=None,
        store_id=None,
        role="super_admin",
        email=u_super.email
    )
    r = client.post(f"/api/rbac/users/{u_brand_b.id}/role", json={"role": "super_admin"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    db.refresh(u_brand_b)
    assert u_brand_b.role == "super_admin"

    print("--- 3. Testing User Deactivation (DELETE /api/rbac/users/{id}) ---")
    
    # 3.a brand_admin deactivating user in own brand should succeed
    current_caller = UserContext(
        user_id=str(u_brand_a.id),
        brand_id=str(brand_a_id),
        store_id=None,
        role="brand_admin",
        email=u_brand_a.email
    )
    
    r = client.delete(f"/api/rbac/users/{u_staff_a.id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    db.refresh(u_staff_a)
    assert u_staff_a.is_active is False
    
    # Verify deactivation audit log
    audit_deact = db.scalar(select(AuditLog).where(AuditLog.action == "user.deactivate"))
    assert audit_deact is not None
    assert audit_deact.actor == u_brand_a.email
    assert audit_deact.details.get("email") == u_staff_a.email
    
    # 3.b brand_admin trying to deactivate super_admin should fail (403)
    r = client.delete(f"/api/rbac/users/{u_super.id}")
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    
    # Reset staff_a to active
    u_staff_a.is_active = True
    db.commit()
    
    # 3.c super_admin deactivating user should succeed
    current_caller = UserContext(
        user_id=str(u_super.id),
        brand_id=None,
        store_id=None,
        role="super_admin",
        email=u_super.email
    )
    r = client.delete(f"/api/rbac/users/{u_staff_a.id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    db.refresh(u_staff_a)
    assert u_staff_a.is_active is False

    print("ALL TESTS PASSED SUCCESSFULLY!")
    db.close()
    
    # Cleanup database file
    test_engine.dispose()
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    test_rbac_flow()
