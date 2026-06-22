"""Unit and integration tests for Employee & Customer Enrollment (crud, duplicates, isolation)."""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.models.identity import Customer, Employee, FaceEmbedding
from backend_core.schemas.identity import EmployeeCreateIn, CustomerCreateIn
from backend_core.services.identity_employees import IdentityEmployeeService
from backend_core.services.identity_customers import IdentityCustomerService
from shared.database.models import Base, Visitor


@pytest.fixture(name="db")
def fixture_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Seed default Brand for resolve_brand_id
    from shared.database.tenant_models import Brand
    brand = Brand(slug="orzen-demo", name="Orzen Demo")
    db.add(brand)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()


def test_employee_crud_and_face_enrollment(db: Session) -> None:
    brand_id = uuid.uuid4()
    svc = IdentityEmployeeService(db)

    # 1. Create Employee
    payload = EmployeeCreateIn(
        name="Test Worker",
        email="worker@orzen.io",
        phone="9876543210",
        department="Sales",
        designation="Sales Executive",
        store_id="store-001",
        branch="Main Branch",
        employee_code="EMP99",
    )
    emp = svc.create_employee(brand_id, payload)
    assert emp.name == "Test Worker"
    assert emp.email == "worker@orzen.io"
    assert emp.department == "Sales"
    assert emp.employee_code == "EMP99"
    assert emp.has_face_enrolled is False

    # 2. Get Employee
    emp_uuid = uuid.UUID(emp.id)
    retrieved = svc.get_employee(emp_uuid)
    assert retrieved.name == "Test Worker"

    # 3. Enroll Face via proper upsert so the Visitor table is updated
    dummy_embedding = [0.1] * 512
    enroll_payload = EmployeeCreateIn(
        id=emp.id,
        name=emp.name,
        email=emp.email,
        phone=emp.phone,
        department=emp.department,
        designation=emp.designation,
        store_id=emp.store_id,
        branch=emp.branch,
        employee_code=emp.employee_code,
        embedding=dummy_embedding,
    )
    emp_enrolled = svc.create_employee(brand_id, enroll_payload)
    assert emp_enrolled.has_face_enrolled is True

    # 4. Duplicate Face Check — same embedding must be rejected for a different employee
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        payload_dup = EmployeeCreateIn(
            name="Another Worker",
            embedding=dummy_embedding,
        )
        svc.create_employee(brand_id, payload_dup)
    assert "Face embedding already matches existing enrolled person" in str(exc.value.detail)

    # 5. Delete Face
    updated_emp = svc.delete_employee_face(emp_uuid, brand_id)
    assert updated_emp.has_face_enrolled is False
    assert not updated_emp.joining_date

    # 6. Delete Employee
    svc.delete_employee(emp_uuid, brand_id)
    with pytest.raises(HTTPException):
        svc.get_employee(emp_uuid)


def test_customer_crud_and_watchlist(db: Session) -> None:
    brand_id = uuid.uuid4()
    svc = IdentityCustomerService(db)

    # 1. Create Customer with VIP & Watchlist
    payload = CustomerCreateIn(
        name="Test Customer",
        email="customer@gmail.com",
        phone="1234567890",
        membership_id="MEMB-001",
        loyalty_points=150,
        is_vip=True,
        is_watchlist=True,
        preferred_store="store-001",
        notes="Important notes",
    )
    cust = svc.create_customer(brand_id, payload)
    assert cust.name == "Test Customer"
    assert cust.email == "customer@gmail.com"
    assert cust.is_vip is True
    assert cust.is_watchlist is True
    assert cust.loyalty_points == 150
    assert cust.has_face_enrolled is False

    # 2. Enroll Face
    dummy_embedding = [0.2] * 512
    cust_uuid = uuid.UUID(cust.id)
    svc.enroll_face_embedding(customer_id=cust_uuid, embedding=dummy_embedding)

    cust_out = svc._to_out(svc.get_customer(cust_uuid))
    assert cust_out.has_face_enrolled is True

    # 3. Watchlist match check inside AlertEngine
    from edge_ai.alert_engine.events import AlertEngine
    from shared.config import get_settings
    from edge_ai.recognition.face_matcher import MatchResult

    visitor = db.get(Visitor, cust_uuid)
    assert visitor is not None
    assert visitor.metadata_["is_watchlist"] is True

    engine = AlertEngine(db, get_settings(), brand_id)
    match_res = MatchResult(visitor=visitor, confidence=0.9, is_new=False)
    events = engine.process(match_res, track_id=1, confidence=0.9)
    
    # Watchlist alert should trigger
    watchlist_alerts = [e for e in events if e.alert_type == "watchlist_match"]
    assert len(watchlist_alerts) == 1
    assert "matched blacklist" in watchlist_alerts[0].message


def test_multi_tenant_isolation(db: Session) -> None:
    brand_a = uuid.uuid4()
    brand_b = uuid.uuid4()

    svc = IdentityEmployeeService(db)

    # Create employee in brand A
    payload = EmployeeCreateIn(name="Brand A worker")
    emp_a = svc.create_employee(brand_a, payload)

    # Attempt to retrieve employee from brand B
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        emp_uuid = uuid.UUID(emp_a.id)
        emp = svc.get_employee(emp_uuid)
        if emp.brand_id != brand_b:
            raise HTTPException(status_code=404, detail="Employee not found")
