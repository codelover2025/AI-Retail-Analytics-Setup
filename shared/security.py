import hashlib
import secrets


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, hashed: str) -> bool:
    return secrets.compare_digest(hash_secret(value), hashed)


def generate_api_key(prefix: str = "edge") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"
