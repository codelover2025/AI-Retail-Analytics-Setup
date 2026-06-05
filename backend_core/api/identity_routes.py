"""Identity insights legacy API — delegates directly to v1 handlers to eliminate duplicate code."""

from typing import Optional
import uuid as _uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import verify_dashboard_api_key, get_tenant_optional
from shared.tenant_context import TenantContext
from backend_core.models.identity import Customer, FaceEmbedding, PersonRecognition
from backend_core.schemas.identity import (
    CustomerCreateIn,
    CustomerEnrollIn,
    CustomerOut,
    CustomerUpdateIn,
    EmployeeCreateIn,
    EmployeeOut,
    EmployeeUpdateIn,
    IdentityStatsOut,
    RecognitionIngest,
    RecognitionOut,
    RepeatVisitorOut,
)
from backend_core.services.identity_customers import IdentityCustomerService
from backend_core.services.identity_recognitions import IdentityRecognitionService
from shared.database.session import get_db

# Import implementation handlers from v1 to avoid duplicate code
from backend_core.api.v1.identity import (
    v1_get_customers,
    v1_create_customer,
    v1_get_customer,
    v1_update_customer,
    v1_enroll_customer_embedding,
    v1_get_visits_for_person,
    v1_get_repeat_visits_for_person,
    v1_get_employees,
    v1_create_employee,
    v1_create_employee_from_photos,
    v1_get_employee,
    v1_update_employee,
    v1_re_enroll_employee,
    v1_get_identity_stats,
)

router = APIRouter(prefix="/api", tags=["identity-legacy"])


@router.get("/customers", response_model=list[CustomerOut])
def get_customers(
    limit: int = Query(default=500, ge=1, le=1000),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_customers(limit=limit, tenant=tenant, db=db)


@router.post("/customers", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreateIn,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_create_customer(payload=payload, tenant=tenant, db=db)


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_customer(customer_id=customer_id, tenant=tenant, db=db)


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdateIn,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_update_customer(customer_id=customer_id, payload=payload, tenant=tenant, db=db)


@router.post("/customers/{customer_id}/enroll", response_model=CustomerOut)
def enroll_customer_embedding(
    customer_id: str,
    payload: CustomerEnrollIn,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_enroll_customer_embedding(customer_id=customer_id, payload=payload, tenant=tenant, db=db)


@router.get("/recognitions", response_model=list[RecognitionOut])
def get_recognitions(
    limit: int = Query(default=500, ge=1, le=1000),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    # Unique to legacy router
    return IdentityRecognitionService(db).list_recognitions(brand_id=tenant.brand_id, limit=limit)


@router.get("/visitors/{person_id}/visits", response_model=list[RecognitionOut])
def get_visits_for_person(
    person_id: str,
    repeat_only: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=2000),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_visits_for_person(
        person_id=person_id,
        repeat_only=repeat_only,
        limit=limit,
        tenant=tenant,
        db=db,
    )


@router.get("/repeat-visitors", response_model=list[RepeatVisitorOut])
def get_repeat_visitors(
    min_visits: int = Query(default=2, ge=2, le=100),
    limit: int = Query(default=500, ge=1, le=1000),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    # Unique to legacy router
    return IdentityCustomerService(db).list_repeat_visitors_filtered(
        brand_id=tenant.brand_id, min_visits=min_visits, limit=limit
    )


@router.get("/repeat-visitors/{person_id}/visits", response_model=list[RecognitionOut])
def get_repeat_visits_for_person(
    person_id: str,
    limit: int = Query(default=500, ge=1, le=2000),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_repeat_visits_for_person(person_id=person_id, limit=limit, tenant=tenant, db=db)


@router.get("/employees", response_model=list[EmployeeOut])
def get_employees(
    limit: int = Query(default=200, ge=1, le=500),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_employees(limit=limit, tenant=tenant, db=db)


@router.post("/employees", response_model=EmployeeOut)
def create_employee(
    payload: EmployeeCreateIn,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_create_employee(payload=payload, tenant=tenant, db=db)


@router.post("/employees/upload", response_model=EmployeeOut)
async def create_employee_from_photos(
    name: str = Form(...),
    employee_id: str | None = Form(default=None),
    photos: list[UploadFile] = File(...),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return await v1_create_employee_from_photos(
        name=name,
        employee_id=employee_id,
        photos=photos,
        tenant=tenant,
        db=db,
    )


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: str,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_employee(employee_id=employee_id, tenant=tenant, db=db)


@router.patch("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdateIn,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_update_employee(employee_id=employee_id, payload=payload, tenant=tenant, db=db)


@router.post("/employees/{employee_id}/re-enroll", response_model=EmployeeOut)
async def re_enroll_employee(
    employee_id: str,
    photos: list[UploadFile] = File(...),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return await v1_re_enroll_employee(employee_id=employee_id, photos=photos, tenant=tenant, db=db)


@router.post("/customers/{customer_id}/enroll-photo", response_model=CustomerOut)
async def enroll_customer_from_photos(
    customer_id: str,
    photos: list[UploadFile] = File(...),
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    # Unique to legacy router
    if not photos:
        raise HTTPException(status_code=400, detail="At least one photo required")
    from shared.face_enrollment import embedding_from_upload

    svc = IdentityCustomerService(db)
    cust = db.get(Customer, _uuid.UUID(customer_id))
    if cust is None or (cust.brand_id is not None and cust.brand_id != tenant.brand_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    embedding = embedding_from_upload([await p.read() for p in photos])
    svc.enroll_face_embedding(customer_id=cust.id, embedding=embedding)
    db.commit()
    return CustomerOut(
        id=str(cust.id),
        first_seen=cust.first_seen,
        last_seen=cust.last_seen,
        visit_count=cust.visit_count,
    )


@router.get("/identity-stats", response_model=IdentityStatsOut)
def get_identity_stats(
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    return v1_get_identity_stats(tenant=tenant, db=db)


@router.post("/ingest/recognition", response_model=RecognitionOut)
def ingest_recognition(
    payload: RecognitionIngest,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """AI pipeline posts raw events here — no matching logic in this layer."""
    # Unique to legacy router
    return IdentityRecognitionService(db).ingest(tenant.brand_id, payload)
