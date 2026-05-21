import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from shared.database.audit_models import AuditLog


def log_access(
    db: Session,
    *,
    action: str,
    actor: str,
    brand_id: Optional[uuid.UUID] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    db.add(
        AuditLog(
            brand_id=brand_id,
            actor=actor,
            action=action,
            resource=resource,
            ip_address=ip_address,
            details=details or {},
        )
    )
