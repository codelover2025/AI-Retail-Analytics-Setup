from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from shared.config import Settings


def create_access_token(
    settings: Settings,
    *,
    subject: str,
    brand_id: str,
    brand_slug: str,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "brand_id": brand_id,
        "brand_slug": brand_slug,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
