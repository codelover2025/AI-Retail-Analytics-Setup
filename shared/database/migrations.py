"""Lightweight column migrations for existing dev databases."""

from sqlalchemy import inspect, text


def ensure_recognition_phase2_columns() -> None:
    """Add match_score + identity_type to recognitions if missing."""
    from shared.database.session import engine, is_sqlite

    insp = inspect(engine)
    tables = insp.get_table_names()
    if "recognitions" not in tables:
        return
    existing = {col["name"] for col in insp.get_columns("recognitions")}
    statements = []
    if "match_score" not in existing:
        col_type = "REAL" if is_sqlite() else "DOUBLE PRECISION"
        statements.append(
            "ALTER TABLE recognitions ADD COLUMN match_score " + col_type
        )
    if "identity_type" not in existing:
        statements.append(
            "ALTER TABLE recognitions ADD COLUMN identity_type VARCHAR(32)"
        )
    if not statements:
        return
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def ensure_employee_phase2_columns() -> None:
    """Add active + updated_at to employees if missing."""
    from shared.database.session import engine, is_sqlite

    sqlite = is_sqlite()
    insp = inspect(engine)
    if "employees" not in insp.get_table_names():
        return
    existing = {col["name"] for col in insp.get_columns("employees")}
    statements = []
    if "active" not in existing:
        statements.append(
            "ALTER TABLE employees ADD COLUMN active "
            + ("INTEGER DEFAULT 1 NOT NULL" if sqlite else "BOOLEAN DEFAULT TRUE NOT NULL")
        )
    if "updated_at" not in existing:
        if sqlite:
            # SQLite ALTER TABLE does not allow non-constant defaults (e.g. CURRENT_TIMESTAMP).
            statements.append("ALTER TABLE employees ADD COLUMN updated_at DATETIME")
            statements.append(
                "UPDATE employees SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
            )
        else:
            statements.append(
                "ALTER TABLE employees ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE "
                "DEFAULT CURRENT_TIMESTAMP"
            )
    if not statements:
        return
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
