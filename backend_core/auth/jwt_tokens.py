"""JWT helpers — create and decode access tokens."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt

from shared.config import Settings


def create_access_token(
    settings: Settings,
    *,
    brand_id: str,
    brand_slug: str,
    store_id: str,
    role: str = "staff_viewer",
    extra: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "brand_id": brand_id,
        "brand_slug": brand_slug,
        "store_id": store_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
