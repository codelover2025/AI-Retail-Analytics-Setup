"""Identity insights API — strict contract for dashboard + AI ingestion."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import verify_dashboard_api_key
from backend_core.models.identity import Customer, Employee, PersonRecognition
from backend_core.schemas.identity import (
    CustomerCreateIn,
    CustomerEnrollIn,
    CustomerOut,
    CustomerUpdateIn,
    EmployeeCreateIn,
    EmployeeOut,
    IdentityStatsOut,
    RecognitionIngest,
    RecognitionOut,
    RepeatVisitorOut,
)
from backend_core.services.identity_customers import IdentityCustomerService
from backend_core.services.identity_employees import IdentityEmployeeService
from backend_core.services.identity_recognitions import IdentityRecognitionService
from shared.database.session import get_db

router = APIRouter(prefix="/api", tags=["identity"])


@router.get("/customers", response_model=list[CustomerOut])
def get_customers(
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityCustomerService(db).list_customers(limit=limit)


@router.post("/customers", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    svc = IdentityCustomerService(db)
    import uuid as _uuid

    person_id = _uuid.UUID(payload.id) if payload.id else _uuid.uuid4()
    first_seen = payload.first_seen
    last_seen = payload.last_seen
    cust = svc.create_or_update_customer(
        person_id=person_id,
        first_seen=first_seen,
        last_seen=last_seen,
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
def get_customer(
    customer_id: str,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    cust = db.get(Customer, _uuid.UUID(customer_id))
    if cust is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    svc = IdentityCustomerService(db)
    cust = db.get(Customer, _uuid.UUID(customer_id))
    if cust is None:
        from fastapi import HTTPException

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
def enroll_customer_embedding(
    customer_id: str,
    payload: CustomerEnrollIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    svc = IdentityCustomerService(db)
    cust = db.get(Customer, _uuid.UUID(customer_id))
    if cust is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Customer not found")

    svc.enroll_face_embedding(customer_id=cust.id, embedding=payload.embedding)
    db.commit()
    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.get("/recognitions", response_model=list[RecognitionOut])
def get_recognitions(
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityRecognitionService(db).list_recognitions(limit=limit)


@router.get("/visitors/{person_id}/visits", response_model=list[RecognitionOut])
def get_visits_for_person(
    person_id: str,
    repeat_only: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=2000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    svc = IdentityRecognitionService(db)
    return svc.list_recognitions_for_person_id(
        _uuid.UUID(person_id), limit=limit, repeat_only=repeat_only
    )


@router.get("/repeat-visitors", response_model=list[RepeatVisitorOut])
def get_repeat_visitors(
    min_visits: int = Query(default=2, ge=2, le=100),
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityCustomerService(db).list_repeat_visitors(
        min_visits=min_visits, limit=limit
    )


@router.get("/repeat-visitors/{person_id}/visits", response_model=list[RecognitionOut])
def get_repeat_visits_for_person(
    person_id: str,
    limit: int = Query(default=500, ge=1, le=2000),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    svc = IdentityRecognitionService(db)
    return svc.list_recognitions_for_person_id(
        _uuid.UUID(person_id), limit=limit, repeat_only=True
    )


@router.get("/employees", response_model=list[EmployeeOut])
def get_employees(
    limit: int = Query(default=200, ge=1, le=500),
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityEmployeeService(db).list_employees(limit=limit)


@router.post("/employees", response_model=EmployeeOut)
def create_employee(
    payload: EmployeeCreateIn,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    return IdentityEmployeeService(db).create_employee(payload)


@router.get("/identity-stats", response_model=IdentityStatsOut)
def get_identity_stats(
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    repeat = len(IdentityCustomerService(db).list_repeat_visitors(min_visits=2, limit=10_000))
    employees = db.scalar(select(func.count()).select_from(Employee)) or 0
    new_today = (
        db.scalar(
            select(func.count())
            .select_from(PersonRecognition)
            .where(PersonRecognition.type == "new_visitor")
        )
        or 0
    )
    return IdentityStatsOut(
        total_customers=int(total_customers),
        repeat_visitors=repeat,
        new_visitors_today=int(new_today),
        employee_tags=int(employees),
    )


@router.post("/ingest/recognition", response_model=RecognitionOut)
def ingest_recognition(
    payload: RecognitionIngest,
    _: None = Depends(verify_dashboard_api_key),
    db: Session = Depends(get_db),
):
    """AI pipeline posts raw events here — no matching logic in this layer."""
    return IdentityRecognitionService(db).ingest(payload)
