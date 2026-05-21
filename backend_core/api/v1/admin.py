from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import verify_dashboard_api_key
from backend_core.schemas.admin import (
    BrandCreate,
    BrandOut,
    CameraCreate,
    CameraOut,
    EdgeDeviceCreate,
    EdgeDeviceOut,
    StoreCreate,
    StoreOut,
)
from backend_core.services.admin import AdminService
from shared.audit import log_access
from shared.database.session import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin-provisioning"],
    dependencies=[Depends(verify_dashboard_api_key)],
)


@router.post("/brands", response_model=BrandOut)
def create_brand(body: BrandCreate, request: Request, db: Session = Depends(get_db)):
    out = AdminService(db).create_brand(body)
    log_access(db, action="admin.create_brand", actor="api_key", resource=body.slug)
    db.commit()
    return out


@router.post("/stores", response_model=StoreOut)
def create_store(body: StoreCreate, db: Session = Depends(get_db)):
    out = AdminService(db).create_store(body)
    log_access(
        db,
        action="admin.create_store",
        actor="api_key",
        resource=f"{body.brand_slug}/{body.external_id}",
    )
    db.commit()
    return out


@router.post("/cameras", response_model=CameraOut)
def create_camera(body: CameraCreate, db: Session = Depends(get_db)):
    out = AdminService(db).create_camera(body)
    log_access(
        db,
        action="admin.create_camera",
        actor="api_key",
        resource=out.external_id,
        details={"rtsp_url": out.rtsp_url[:80]},
    )
    db.commit()
    return out


@router.post("/edge-devices", response_model=EdgeDeviceOut)
def create_edge_device(body: EdgeDeviceCreate, db: Session = Depends(get_db)):
    out = AdminService(db).create_edge_device(body)
    log_access(db, action="admin.create_edge_device", actor="api_key", resource=out.name)
    db.commit()
    return out
