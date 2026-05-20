from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend_core.auth.dependencies import get_edge_device
from backend_core.schemas.edge import (
    EdgeConfigResponse,
    EdgeHeartbeatRequest,
    EdgeHeartbeatResponse,
)
from backend_core.services.edge_cloud import EdgeCloudService
from shared.config import get_settings
from shared.database.session import get_db
from shared.database.tenant_models import EdgeDevice, Store

router = APIRouter(prefix="/edge", tags=["edge-cloud"])


def _load_device(db: Session, device_id) -> EdgeDevice:
    device = db.scalar(
        select(EdgeDevice)
        .options(joinedload(EdgeDevice.store).joinedload(Store.brand))
        .where(EdgeDevice.id == device_id)
    )
    if device is None:
        raise RuntimeError("Edge device not found")
    return device


@router.get("/config", response_model=EdgeConfigResponse)
def get_edge_config(
    device: EdgeDevice = Depends(get_edge_device),
    db: Session = Depends(get_db),
):
    loaded = _load_device(db, device.id)
    return EdgeCloudService(db, get_settings()).build_config(loaded)


@router.post("/heartbeat", response_model=EdgeHeartbeatResponse)
def post_heartbeat(
    body: EdgeHeartbeatRequest,
    config_version: int | None = Query(default=None),
    device: EdgeDevice = Depends(get_edge_device),
    db: Session = Depends(get_db),
):
    loaded = _load_device(db, device.id)
    svc = EdgeCloudService(db, get_settings())
    resp = svc.record_heartbeat(loaded, body, known_config_version=config_version)
    db.commit()
    return resp
