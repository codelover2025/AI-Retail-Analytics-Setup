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


def ensure_identity_multi_tenant_columns() -> None:
    """Add brand_id + store_id to customers, employees, and person_recognitions if missing, and backfill."""
    from shared.database.session import engine, is_sqlite
    from shared.config import get_settings
    from shared.tenant_resolve import resolve_brand_id
    from sqlalchemy.orm import Session

    insp = inspect(engine)
    tables = insp.get_table_names()

    # 1. Migrate columns if missing
    statements = []
    
    # Customers
    if "customers" in tables:
        cust_cols = {col["name"] for col in insp.get_columns("customers")}
        if "brand_id" not in cust_cols:
            statements.append("ALTER TABLE customers ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE customers ADD COLUMN brand_id UUID")

    # Employees
    if "employees" in tables:
        emp_cols = {col["name"] for col in insp.get_columns("employees")}
        if "brand_id" not in emp_cols:
            statements.append("ALTER TABLE employees ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE employees ADD COLUMN brand_id UUID")

    # Person Recognitions
    if "person_recognitions" in tables:
        rec_cols = {col["name"] for col in insp.get_columns("person_recognitions")}
        if "brand_id" not in rec_cols:
            statements.append("ALTER TABLE person_recognitions ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE person_recognitions ADD COLUMN brand_id UUID")
        if "store_id" not in rec_cols:
            statements.append("ALTER TABLE person_recognitions ADD COLUMN store_id VARCHAR(64)")

    # Footfall Daily
    if "footfall_daily" in tables:
        fd_cols = {col["name"] for col in insp.get_columns("footfall_daily")}
        if "brand_id" not in fd_cols:
            statements.append("ALTER TABLE footfall_daily ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE footfall_daily ADD COLUMN brand_id UUID")

    # Visitors
    if "visitors" in tables:
        vis_cols = {col["name"] for col in insp.get_columns("visitors")}
        if "brand_id" not in vis_cols:
            statements.append("ALTER TABLE visitors ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE visitors ADD COLUMN brand_id UUID")

    # Recognitions (core pipeline logs)
    if "recognitions" in tables:
        rec_cols = {col["name"] for col in insp.get_columns("recognitions")}
        if "brand_id" not in rec_cols:
            statements.append("ALTER TABLE recognitions ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE recognitions ADD COLUMN brand_id UUID")

    # Live Visitors (active tracks)
    if "live_visitors" in tables:
        lv_cols = {col["name"] for col in insp.get_columns("live_visitors")}
        if "brand_id" not in lv_cols:
            statements.append("ALTER TABLE live_visitors ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE live_visitors ADD COLUMN brand_id UUID")

    # Alerts (notifications log)
    if "alerts" in tables:
        al_cols = {col["name"] for col in insp.get_columns("alerts")}
        if "brand_id" not in al_cols:
            statements.append("ALTER TABLE alerts ADD COLUMN brand_id VARCHAR(36)" if is_sqlite() else "ALTER TABLE alerts ADD COLUMN brand_id UUID")

    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))

    # 2. Backfill brand_id and store_id if they are NULL
    settings = get_settings()
    with Session(engine) as db:
        try:
            brand_id = resolve_brand_id(db, settings)
            brand_id_str = str(brand_id)
            store_id = settings.store_id

            if "customers" in tables:
                db.execute(
                    text("UPDATE customers SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "employees" in tables:
                db.execute(
                    text("UPDATE employees SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "person_recognitions" in tables:
                db.execute(
                    text("UPDATE person_recognitions SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
                db.execute(
                    text("UPDATE person_recognitions SET store_id = :store_id WHERE store_id IS NULL"),
                    {"store_id": store_id}
                )
            if "footfall_daily" in tables:
                db.execute(
                    text("UPDATE footfall_daily SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "visitors" in tables:
                db.execute(
                    text("UPDATE visitors SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "recognitions" in tables:
                db.execute(
                    text("UPDATE recognitions SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "live_visitors" in tables:
                db.execute(
                    text("UPDATE live_visitors SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            if "alerts" in tables:
                db.execute(
                    text("UPDATE alerts SET brand_id = :brand_id WHERE brand_id IS NULL"),
                    {"brand_id": brand_id_str if is_sqlite() else brand_id}
                )
            db.commit()
        except Exception:
            db.rollback()
            pass

