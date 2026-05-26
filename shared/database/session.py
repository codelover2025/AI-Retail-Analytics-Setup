from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from shared.config import get_settings
from shared.database.models import Base
from shared.database import audit_models  # noqa: F401
from shared.database import tenant_models  # noqa: F401 — register tenant tables

settings = get_settings()


def _build_engine():
    url = settings.database_url
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        # Relative path ./data/orzen_dev.db → ensure directory exists
        if ":///" in url and not url.startswith("sqlite:////"):
            raw = url.split("///", 1)[-1]
            if raw.startswith("./") or (not raw.startswith(":") and "/" not in raw[:3]):
                db_path = Path(raw.split("?", 1)[0])
                if not db_path.is_absolute():
                    db_path = Path.cwd() / db_path
                db_path.parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
    return create_engine(url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        from shared.database.migrations import ensure_recognition_phase2_columns

        ensure_recognition_phase2_columns()
        if is_sqlite():
            # quick connectivity check
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError(
            "Database connection failed.\n"
            "  • PostgreSQL: start Docker Desktop, then run: docker compose up -d postgres\n"
            "  • Or use SQLite (no Docker): set in .env\n"
            "      DATABASE_URL=sqlite:///./data/orzen_dev.db\n"
            f"Original error: {exc}"
        ) from exc


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
