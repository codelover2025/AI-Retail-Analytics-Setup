"""
HRMS API — Module 7 (Phase 4).

Endpoints:
  POST /api/hrms/sync/employees     — trigger employee sync
  POST /api/hrms/sync/attendance    — trigger attendance sync
  GET  /api/hrms/employees          — list synced employees
  GET  /api/hrms/employees/{id}     — single employee profile
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.integrations.hrms.factory import get_hrms_adapter
from backend_core.models.identity import Employee
from shared.config import get_settings
from shared.database.hrms_models import HRMSAttendanceSync
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/hrms", tags=["hrms"])


@router.post("/sync/employees", summary="Trigger HRMS employee sync")
def sync_employees(
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Pulls employees from configured HRMS and upserts into local Employee table."""
    settings = get_settings()
    adapter = get_hrms_adapter(settings)
    employees = adapter.sync_employees(str(tenant.brand_id))

    synced = 0
    for emp in employees:
        # Upsert by name (simplistic — extend with external_id column for production)
        existing = db.scalar(
            select(Employee).where(
                Employee.brand_id == tenant.brand_id,
                Employee.name == emp.name,
            )
        )
        if existing is None:
            new_emp = Employee(
                brand_id=tenant.brand_id,
                name=emp.name,
                embedding=[],
                active=emp.is_active,
            )
            db.add(new_emp)
            synced += 1
        else:
            existing.active = emp.is_active
    db.commit()
    return {"synced": synced, "total_from_hrms": len(employees)}


@router.post("/sync/attendance", summary="Trigger HRMS attendance sync")
def sync_attendance(
    sync_date: Optional[date] = Query(default=None),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Pulls attendance records from HRMS for a date and persists them."""
    settings = get_settings()
    adapter = get_hrms_adapter(settings)
    target_date = str(sync_date or date.today())
    records = adapter.sync_attendance(str(tenant.brand_id), target_date)

    saved = 0
    for rec in records:
        emp = db.scalar(
            select(Employee).where(
                Employee.brand_id == tenant.brand_id,
                Employee.name == rec.employee_external_id,
            )
        )
        if emp:
            attendance = HRMSAttendanceSync(
                brand_id=tenant.brand_id,
                employee_id=emp.id,
                status=rec.status,
            )
            db.add(attendance)
            saved += 1
    db.commit()
    return {"date": target_date, "records_from_hrms": len(records), "saved": saved}


@router.get("/employees", summary="List synced employees")
def list_employees(
    active_only: bool = Query(default=True),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    stmt = select(Employee).where(Employee.brand_id == tenant.brand_id)
    if active_only:
        stmt = stmt.where(Employee.active == True)
    stmt = stmt.order_by(Employee.name)
    rows = list(db.scalars(stmt).all())
    return [
        {"id": str(e.id), "name": e.name, "active": e.active, "created_at": e.created_at.isoformat()}
        for e in rows
    ]


@router.get("/employees/{employee_id}", summary="Employee profile")
def get_employee(
    employee_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    emp = db.get(Employee, employee_id)
    if emp is None or emp.brand_id != tenant.brand_id:
        raise HTTPException(404, "Employee not found")

    settings = get_settings()
    adapter = get_hrms_adapter(settings)
    hrms_profile = adapter.get_employee_profile(str(employee_id))

    return {
        "id": str(emp.id),
        "name": emp.name,
        "active": emp.active,
        "created_at": emp.created_at.isoformat(),
        "hrms_profile": {
            "department": hrms_profile.department if hrms_profile else None,
            "designation": hrms_profile.designation if hrms_profile else None,
            "email": hrms_profile.email if hrms_profile else None,
        } if hrms_profile else None,
    }
