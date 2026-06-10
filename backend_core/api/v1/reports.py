"""
Reports API — Module 3 (Phase 4).

Endpoints:
  POST /api/reports/generate      — trigger async report generation
  GET  /api/reports/export/{id}   — get job status + download file
  POST /api/reports/schedule      — create recurring report schedule
  GET  /api/reports/schedule      — list schedules
  DELETE /api/reports/schedule/{id} — remove schedule
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.services.report_service import ReportService
from backend_core.services.report_scheduler import add_schedule_job, remove_schedule_job
from shared.config import get_settings
from shared.database.report_models import ReportJob, ReportSchedule
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class GenerateReportRequest(BaseModel):
    report_type: str = Field(..., description="daily | weekly | monthly | custom")
    output_format: str = Field(..., description="pdf | excel | csv")
    store_ids: list[str] = Field(default_factory=list)
    from_day: Optional[date] = None
    to_day: Optional[date] = None


class ScheduleReportRequest(BaseModel):
    report_type: str
    output_format: str
    store_ids: list[str] = Field(default_factory=list)
    cron_expr: str = Field(..., description="Standard 5-field cron, e.g. '0 8 * * 1'")
    delivery_channels: list[str] = Field(default_factory=list, description="email | whatsapp")
    recipients: list[str] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    report_type: str
    output_format: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Background task runner
# ---------------------------------------------------------------------------

def _run_job_bg(job_id: uuid.UUID, brand_id: uuid.UUID, settings) -> None:
    from shared.database.session import SessionLocal
    db = SessionLocal()
    try:
        svc = ReportService(db, settings, brand_id)
        svc.execute_job(job_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/generate", status_code=202, summary="Trigger async report generation")
def generate_report(
    body: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """
    Queues an async report generation job.

    Returns `job_id` immediately; poll `/api/reports/export/{job_id}` for status.
    """
    valid_types = {"daily", "weekly", "monthly", "custom"}
    valid_formats = {"pdf", "excel", "csv"}
    if body.report_type not in valid_types:
        raise HTTPException(400, f"report_type must be one of {valid_types}")
    if body.output_format not in valid_formats:
        raise HTTPException(400, f"output_format must be one of {valid_formats}")

    settings = get_settings()
    svc = ReportService(db, settings, tenant.brand_id)
    params = {}
    if body.from_day:
        params["from_day"] = str(body.from_day)
    if body.to_day:
        params["to_day"] = str(body.to_day)

    job = svc.create_job(
        report_type=body.report_type,
        output_format=body.output_format,
        store_ids=body.store_ids,
        params=params,
        requested_by=tenant.brand_slug,
    )

    background_tasks.add_task(
        _run_job_bg, job.id, tenant.brand_id, settings
    )

    return {"job_id": str(job.id), "status": "pending"}


@router.get("/export/{job_id}", summary="Get report job status / download")
def export_report(
    job_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Poll job status. When status=completed, returns the file for download."""
    job = db.get(ReportJob, job_id)
    if job is None or job.brand_id != tenant.brand_id:
        raise HTTPException(404, "Report job not found")

    if job.status == "completed" and job.file_path:
        try:
            ext_map = {"pdf": "application/pdf",
                       "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       "csv": "text/csv"}
            ext = job.file_path.split(".")[-1]
            media_type = ext_map.get(ext, "application/octet-stream")
            return FileResponse(
                path=job.file_path,
                media_type=media_type,
                filename=job.file_path.split("/")[-1].split("\\")[-1],
            )
        except Exception:
            pass

    return {
        "job_id": str(job.id),
        "status": job.status,
        "report_type": job.report_type,
        "output_format": job.output_format,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
    }


@router.post("/schedule", status_code=201, summary="Create recurring report schedule")
def create_schedule(
    body: ScheduleReportRequest,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    """Create a recurring report schedule using cron syntax."""
    schedule = ReportSchedule(
        brand_id=tenant.brand_id,
        store_ids=body.store_ids,
        report_type=body.report_type,
        output_format=body.output_format,
        cron_expr=body.cron_expr,
        delivery_channels=body.delivery_channels,
        recipients=body.recipients,
        enabled=True,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    add_schedule_job(str(schedule.id), body.cron_expr)

    return {
        "schedule_id": str(schedule.id),
        "cron_expr": schedule.cron_expr,
        "status": "active",
    }


@router.get("/schedule", summary="List report schedules")
def list_schedules(
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    schedules = (
        db.query(ReportSchedule)
        .filter(ReportSchedule.brand_id == tenant.brand_id)
        .order_by(ReportSchedule.created_at.desc())
        .all()
    )
    return [
        {
            "schedule_id": str(s.id),
            "report_type": s.report_type,
            "output_format": s.output_format,
            "cron_expr": s.cron_expr,
            "delivery_channels": s.delivery_channels,
            "enabled": s.enabled,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
        }
        for s in schedules
    ]


@router.delete("/schedule/{schedule_id}", status_code=204, summary="Delete report schedule")
def delete_schedule(
    schedule_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
):
    schedule = db.get(ReportSchedule, schedule_id)
    if schedule is None or schedule.brand_id != tenant.brand_id:
        raise HTTPException(404, "Schedule not found")
    remove_schedule_job(str(schedule_id))
    db.delete(schedule)
    db.commit()
    return Response(status_code=204)
