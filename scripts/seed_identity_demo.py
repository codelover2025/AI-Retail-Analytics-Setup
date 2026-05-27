"""Seed demo customers, employees, and recognition logs for identity dashboard."""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend_core.models.identity import Customer, Employee, PersonRecognition
from shared.database.session import SessionLocal, init_db

NOW = datetime.now(timezone.utc)


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(PersonRecognition).count() > 0:
            print("Identity data already present; skip")
            return

        c1 = uuid.uuid4()
        c2 = uuid.uuid4()
        emp1 = uuid.uuid4()

        db.add_all(
            [
                Customer(
                    id=c1,
                    first_seen=NOW - timedelta(days=5),
                    last_seen=NOW - timedelta(hours=1),
                    visit_count=4,
                ),
                Customer(
                    id=c2,
                    first_seen=NOW - timedelta(days=1),
                    last_seen=NOW - timedelta(minutes=30),
                    visit_count=1,
                ),
            ]
        )
        db.add(
            Employee(
                id=emp1,
                name="Priya Sharma",
                embedding=[0.0] * 512,
            )
        )

        logs = [
            (c1, "repeat_visitor", NOW - timedelta(hours=2), "cam-001"),
            (c1, "repeat_visitor", NOW - timedelta(hours=1), "cam-001"),
            (c2, "new_visitor", NOW - timedelta(minutes=30), "cam-002"),
            (emp1, "employee", NOW - timedelta(minutes=10), "cam-001"),
        ]
        for person_id, rtype, ts, cam in logs:
            db.add(
                PersonRecognition(
                    person_id=person_id,
                    type=rtype,
                    timestamp=ts,
                    camera_id=cam,
                )
            )
        db.commit()
        print("Seeded identity demo: 2 customers, 1 employee, 4 recognition logs")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
