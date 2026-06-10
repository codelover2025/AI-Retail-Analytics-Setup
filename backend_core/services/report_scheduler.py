"""
Background report scheduler — Module 3 (Phase 4).

Uses APScheduler to run recurring report jobs based on
ReportSchedule DB records.  Initialized once at app startup.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_scheduler_started = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _run_scheduled_report(schedule_id: str) -> None:
    """Called by APScheduler; runs in a thread pool worker."""
    from shared.database.session import SessionLocal
    from shared.database.report_models import ReportSchedule, ReportJob
    from shared.config import get_settings
    from backend_core.services.report_service import ReportService

    settings = get_settings()
    db = SessionLocal()
    try:
        sid = uuid.UUID(schedule_id)
        schedule = db.get(ReportSchedule, sid)
        if schedule is None or not schedule.enabled:
            return

        svc = ReportService(db, settings, schedule.brand_id)
        job = svc.create_job(
            report_type=schedule.report_type,
            output_format=schedule.output_format,
            store_ids=list(schedule.store_ids or []),
            params={},
            requested_by=f"schedule:{schedule_id}",
        )

        file_path = svc.execute_job(job.id)
        logger.info("Scheduled report %s completed: %s", schedule_id, file_path)

        # Deliver via configured channels
        _deliver_report(
            file_path=file_path,
            report_type=schedule.report_type,
            channels=list(schedule.delivery_channels or []),
            recipients=list(schedule.recipients or []),
            settings=settings,
        )

        # Update next/last run
        schedule.last_run_at = _utcnow()
        db.commit()

    except Exception as exc:
        logger.error("Scheduled report %s failed: %s", schedule_id, exc)
        db.rollback()
    finally:
        db.close()


def _deliver_report(
    *,
    file_path: str,
    report_type: str,
    channels: list[str],
    recipients: list[str],
    settings: Any,
) -> None:
    """Deliver a generated report via email and/or WhatsApp."""
    from backend_core.services.whatsapp.factory import get_whatsapp_provider

    if "email" in channels:
        _send_email_report(file_path, report_type, recipients, settings)

    if "whatsapp" in channels:
        try:
            provider = get_whatsapp_provider(settings)
            for recipient in recipients:
                if recipient.startswith("+") or recipient.lstrip("+").isdigit():
                    provider.send_text(
                        to=recipient,
                        message=f"📊 Your {report_type.title()} Retail Analytics Report is ready.\n"
                                f"File: {file_path.split('/')[-1]}",
                    )
        except Exception as exc:
            logger.warning("WhatsApp delivery failed: %s", exc)


def _send_email_report(
    file_path: str,
    report_type: str,
    recipients: list[str],
    settings: Any,
) -> None:
    import smtplib
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if not settings.smtp_host or not recipients:
        logger.debug("Email not configured or no recipients — skipping email delivery")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from_address
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"Orzen Vision — {report_type.title()} Analytics Report"
        msg.attach(MIMEText(
            f"Please find attached your {report_type.title()} Retail Analytics Report.", "plain"
        ))

        with open(file_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=file_path.split("/")[-1])
        part["Content-Disposition"] = f'attachment; filename="{file_path.split("/")[-1]}"'
        msg.attach(part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_address, recipients, msg.as_string())

        logger.info("Email report delivered to %d recipients", len(recipients))
    except Exception as exc:
        logger.error("Email delivery failed: %s", exc)


def start_scheduler() -> None:
    """Initialize APScheduler and load all active ReportSchedule records."""
    global _scheduler_started
    if _scheduler_started:
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
        from apscheduler.triggers.cron import CronTrigger  # type: ignore
        from shared.database.session import SessionLocal
        from shared.database.report_models import ReportSchedule

        scheduler = BackgroundScheduler()

        db = SessionLocal()
        try:
            schedules = db.query(ReportSchedule).filter(
                ReportSchedule.enabled == True
            ).all()
            for s in schedules:
                scheduler.add_job(
                    _run_scheduled_report,
                    trigger=CronTrigger.from_crontab(s.cron_expr),
                    id=str(s.id),
                    args=[str(s.id)],
                    replace_existing=True,
                    misfire_grace_time=300,
                )
                logger.info("Loaded report schedule %s (cron: %s)", s.id, s.cron_expr)
        finally:
            db.close()

        scheduler.start()
        _scheduler_started = True
        logger.info("Report scheduler started with %d jobs", len(scheduler.get_jobs()))

        # Store scheduler reference for dynamic job management
        import backend_core.services.report_scheduler as _self
        _self._scheduler_instance = scheduler

    except ImportError:
        logger.warning("APScheduler not installed — scheduled reports disabled")
    except Exception as exc:
        logger.error("Scheduler startup failed: %s", exc)


_scheduler_instance = None


def add_schedule_job(schedule_id: str, cron_expr: str) -> None:
    """Dynamically register a new schedule after creation via API."""
    if _scheduler_instance is None:
        return
    try:
        from apscheduler.triggers.cron import CronTrigger  # type: ignore

        _scheduler_instance.add_job(
            _run_scheduled_report,
            trigger=CronTrigger.from_crontab(cron_expr),
            id=schedule_id,
            args=[schedule_id],
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info("Added schedule job %s", schedule_id)
    except Exception as exc:
        logger.error("Failed to add schedule job %s: %s", schedule_id, exc)


def remove_schedule_job(schedule_id: str) -> None:
    if _scheduler_instance is None:
        return
    try:
        _scheduler_instance.remove_job(schedule_id)
    except Exception:
        pass
