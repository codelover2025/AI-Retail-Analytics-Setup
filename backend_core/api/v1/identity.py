from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import uuid

from backend_core.auth.dependencies import verify_dashboard_api_key
from backend_core.models.identity import Customer, Employee, PersonRecognition
from backend_core.schemas.identity import (
    CustomerCreateIn,
    CustomerEnrollIn,
    CustomerOut,
    CustomerUpdateIn,
    EmployeeCreateIn,
    EmployeeOut,
    EmployeeUpdateIn,
    IdentityStatsOut,
    RecognitionOut,
)
from backend_core.services.identity_customers import IdentityCustomerService
from backend_core.services.identity_employees import IdentityEmployeeService
from backend_core.services.identity_recognitions import IdentityRecognitionService
from shared.database.session import get_db

router = APIRouter(prefix="/identity", tags=["identity-v1"])


@router.get("/customers", response_model=list[CustomerOut])
def v1_get_customers(
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityCustomerService(db).list_customers(limit=limit)


@router.post("/customers", response_model=CustomerOut)
def v1_create_customer(
    payload: CustomerCreateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityCustomerService(db)
    person_id = uuid.UUID(payload.id) if payload.id else uuid.uuid4()
    cust = svc.create_or_update_customer(
        person_id=person_id,
        first_seen=payload.first_seen,
        last_seen=payload.last_seen,
        visit_count=payload.visit_count,
    )
    if payload.embedding:
        svc.enroll_face_embedding(customer_id=cust.id, embedding=payload.embedding)
        db.commit()
    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def v1_get_customer(
    customer_id: str,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    cust = db.get(Customer, uuid.UUID(customer_id))
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def v1_update_customer(
    customer_id: str,
    payload: CustomerUpdateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityCustomerService(db)
    cust = db.get(Customer, uuid.UUID(customer_id))
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    updated = svc.create_or_update_customer(
        person_id=cust.id,
        first_seen=payload.first_seen,
        last_seen=payload.last_seen,
        visit_count=payload.visit_count,
    )
    db.commit()
    return CustomerOut(
        id=str(updated.id),
        first_seen=updated.first_seen,
        last_seen=updated.last_seen,
        visit_count=updated.visit_count,
    )


@router.post("/customers/{customer_id}/enroll", response_model=CustomerOut)
def v1_enroll_customer_embedding(
    customer_id: str,
    payload: CustomerEnrollIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityCustomerService(db)
    cust = db.get(Customer, uuid.UUID(customer_id))
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    svc.enroll_face_embedding(customer_id=cust.id, embedding=payload.embedding)
    db.commit()
    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.get(
    "/visitors/{person_id}/visits",
    response_model=list[RecognitionOut],
)
def v1_get_visits_for_person(
    person_id: str,
    repeat_only: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=2000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityRecognitionService(db)
    return svc.list_recognitions_for_person_id(
        uuid.UUID(person_id), limit=limit, repeat_only=repeat_only
    )


@router.get(
    "/repeat-visitors/{person_id}/visits",
    response_model=list[RecognitionOut],
)
def v1_get_repeat_visits_for_person(
    person_id: str,
    limit: int = Query(default=500, ge=1, le=2000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityRecognitionService(db)
    return svc.list_recognitions_for_person_id(
        uuid.UUID(person_id), limit=limit, repeat_only=True
    )


@router.get("/employees", response_model=list[EmployeeOut])
def v1_get_employees(
    limit: int = Query(default=200, ge=1, le=500),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityEmployeeService(db).list_employees(limit=limit)


@router.post("/employees", response_model=EmployeeOut)
def v1_create_employee(
    payload: EmployeeCreateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityEmployeeService(db).create_employee(payload)


@router.post("/employees/upload", response_model=EmployeeOut)
async def v1_create_employee_from_photos(
    name: str = Form(...),
    employee_id: str | None = Form(default=None),
    photos: list[UploadFile] = File(...),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    if not photos:
        raise HTTPException(status_code=400, detail="At least one photo required")
    files = [await p.read() for p in photos]
    eid = uuid.UUID(employee_id) if employee_id else None
    return IdentityEmployeeService(db).create_employee_from_images(
        name=name, files=files, employee_id=eid
    )


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def v1_get_employee(
    employee_id: str,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    emp = IdentityEmployeeService(db).get_employee(uuid.UUID(employee_id))
    return IdentityEmployeeService._to_out(emp)


@router.patch("/employees/{employee_id}", response_model=EmployeeOut)
def v1_update_employee(
    employee_id: str,
    payload: EmployeeUpdateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityEmployeeService(db).update_employee(uuid.UUID(employee_id), payload)


@router.post("/employees/{employee_id}/re-enroll", response_model=EmployeeOut)
async def v1_re_enroll_employee(
    employee_id: str,
    photos: list[UploadFile] = File(...),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    if not photos:
        raise HTTPException(status_code=400, detail="At least one photo required")
    files = [await p.read() for p in photos]
    return IdentityEmployeeService(db).re_enroll_from_images(
        uuid.UUID(employee_id), files
    )


@router.get("/stats", response_model=IdentityStatsOut)
def v1_get_identity_stats(
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    repeat_visitors = len(
        IdentityCustomerService(db).list_repeat_visitors(min_visits=2, limit=10_000)
    )
    employee_tags = db.scalar(select(func.count()).select_from(Employee)) or 0
    new_visitors_today = (
        db.scalar(
            select(func.count())
            .select_from(PersonRecognition)
            .where(PersonRecognition.type == "new_visitor")
        )
        or 0
    )

    return IdentityStatsOut(
        total_customers=int(total_customers),
        repeat_visitors=int(repeat_visitors),
        new_visitors_today=int(new_visitors_today),
        employee_tags=int(employee_tags),
    )

