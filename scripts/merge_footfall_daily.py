"""
Merge duplicate footfall_daily rows and add unique index (brand_id, store_id, day).

Run once after upgrading Phase 1 footfall fix:
  python scripts/merge_footfall_daily.py
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select, text

from shared.database.models import FootfallDaily
from shared.database.session import SessionLocal, engine, init_db


def merge() -> None:
    init_db()
    db = SessionLocal()
    try:
        rows = list(db.scalars(select(FootfallDaily)).all())
        groups: dict[tuple, list[FootfallDaily]] = defaultdict(list)
        for row in rows:
            key = (row.brand_id, row.store_id, row.day)
            groups[key].append(row)

        merged = 0
        for key, dupes in groups.items():
            if len(dupes) <= 1:
                continue
            keeper = dupes[0]
            for extra in dupes[1:]:
                keeper.unique_visitors += extra.unique_visitors
                keeper.total_detections += extra.total_detections
                db.delete(extra)
                merged += 1

        db.commit()
        print(f"Merged {merged} duplicate footfall row(s) across {len(groups)} day keys.")

        with engine.connect() as conn:
            if engine.dialect.name == "sqlite":
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_footfall_brand_store_day "
                        "ON footfall_daily (brand_id, store_id, day)"
                    )
                )
            conn.commit()
        print("Unique index ensured on (brand_id, store_id, day).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    merge()
