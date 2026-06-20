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


def ensure_phase4_columns() -> None:
    """
    Additive Phase 4 migrations — idempotent, safe to re-run.

    Creates Phase 4 tables if missing and patches any new columns
    onto tables that may have been created before Phase 4.
    """
    from shared.database.session import engine, is_sqlite

    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())

    # Ensure all Phase 4 models are registered before create_all
    import shared.database.report_models  # noqa: F401
    import shared.database.alert_rule_models  # noqa: F401
    import shared.database.rbac_models  # noqa: F401
    from shared.database.models import Base

    Base.metadata.create_all(bind=engine)

    # Patch analytics_sessions with Phase 4 demographic columns
    if "analytics_sessions" in existing_tables:
        cols = {c["name"] for c in insp.get_columns("analytics_sessions")}
        stmts = []
        if "identity_type" not in cols:
            stmts.append("ALTER TABLE analytics_sessions ADD COLUMN identity_type VARCHAR(32)")
        if "age_bucket" not in cols:
            stmts.append("ALTER TABLE analytics_sessions ADD COLUMN age_bucket VARCHAR(32)")
        if "gender" not in cols:
            stmts.append("ALTER TABLE analytics_sessions ADD COLUMN gender VARCHAR(16)")
        if stmts:
            with engine.begin() as conn:
                for s in stmts:
                    conn.execute(text(s))

    # Patch alerts table with camera_id and rule_id
    if "alerts" in existing_tables:
        cols = {c["name"] for c in insp.get_columns("alerts")}
        stmts = []
        if "camera_id" not in cols:
            stmts.append("ALTER TABLE alerts ADD COLUMN camera_id VARCHAR(64)")
        if "rule_id" not in cols:
            col_type = "VARCHAR(36)" if is_sqlite() else "UUID"
            stmts.append(f"ALTER TABLE alerts ADD COLUMN rule_id {col_type}")
        if stmts:
            with engine.begin() as conn:
                for s in stmts:
                    conn.execute(text(s))


def ensure_phase5_columns() -> None:
    """
    Additive Phase 5 migrations — registers chat tables and optimization indexes.
    """
    from shared.database.session import engine, is_sqlite
    
    # 1. Create chat history tables
    import shared.database.ai_models  # noqa: F401
    from shared.database.models import Base
    Base.metadata.create_all(bind=engine)

    # 2. Add performance indexes for POS, HRMS, and Recognitions if they exist
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())

    with engine.begin() as conn:
        # Index on pos_purchases
        if "pos_purchases" in existing_tables:
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pos_purchases_brand_store_ts ON pos_purchases (brand_id, store_id, timestamp)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pos_purchases_visitor_id ON pos_purchases (visitor_id)"))
            except Exception:
                pass

        # Index on hrms_attendance_syncs
        if "hrms_attendance_syncs" in existing_tables:
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_hrms_attendance_syncs_brand_emp_verified ON hrms_attendance_syncs (brand_id, employee_id, verified_at)"))
            except Exception:
                pass

        # Index on person_recognitions
        if "person_recognitions" in existing_tables:
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_person_recognitions_brand_store_type_ts ON person_recognitions (brand_id, store_id, type, timestamp)"))
            except Exception:
                pass

    # 3. Patch demographics_daily table with updated_at column if missing
    if "demographics_daily" in existing_tables:
        cols = {c["name"] for c in insp.get_columns("demographics_daily")}
        if "updated_at" not in cols:
            try:
                with engine.begin() as conn:
                    col_type = "DATETIME" if is_sqlite() else "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"
                    conn.execute(text(f"ALTER TABLE demographics_daily ADD COLUMN updated_at {col_type}"))
            except Exception:
                pass

