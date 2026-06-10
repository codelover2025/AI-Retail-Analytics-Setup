"""
POS conversion analytics service — Module 8 (Phase 4).

Joins POSPurchase × AnalyticsSession × FootfallDailyCamera
to compute retail conversion metrics.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config import Settings
from shared.database.analytics_models import FootfallDailyCamera
from shared.database.pos_models import POSPurchase


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConversionService:
    """Computes visitor→purchase conversion metrics from POS and footfall data."""

    def __init__(self, db: Session, settings: Settings, brand_id: uuid.UUID) -> None:
        self.db = db
        self.settings = settings
        self.brand_id = brand_id

    def conversion_analytics(
        self,
        store_id: Optional[str] = None,
        *,
        from_day: Optional[date] = None,
        to_day: Optional[date] = None,
        days: int = 30,
    ) -> dict:
        to_day = to_day or date.today()
        from_day = from_day or (to_day - timedelta(days=days - 1))

        # Total footfall
        ff_stmt = select(func.sum(FootfallDailyCamera.total_visitors)).where(
            FootfallDailyCamera.brand_id == self.brand_id,
            FootfallDailyCamera.day >= from_day,
            FootfallDailyCamera.day <= to_day,
        )
        if store_id:
            ff_stmt = ff_stmt.where(FootfallDailyCamera.store_id == store_id)
        total_visitors = self.db.scalar(ff_stmt) or 0

        # Total purchases
        from_dt = datetime.combine(from_day, datetime.min.time()).replace(tzinfo=timezone.utc)
        to_dt = datetime.combine(to_day, datetime.max.time()).replace(tzinfo=timezone.utc)
        pos_stmt = select(
            func.count().label("tx_count"),
            func.sum(POSPurchase.amount).label("total_revenue"),
        ).where(
            POSPurchase.brand_id == self.brand_id,
            POSPurchase.timestamp >= from_dt,
            POSPurchase.timestamp <= to_dt,
        )
        if store_id:
            pos_stmt = pos_stmt.where(POSPurchase.store_id == store_id)
        pos_row = self.db.execute(pos_stmt).one()
        tx_count = int(pos_row.tx_count or 0)
        total_revenue = float(pos_row.total_revenue or 0.0)

        conversion_pct = round((tx_count / total_visitors * 100) if total_visitors else 0.0, 2)
        revenue_per_visitor = round(total_revenue / total_visitors if total_visitors else 0.0, 2)

        # Per-store breakdown if no specific store requested
        store_breakdown = []
        if not store_id:
            store_ids_result = self.db.execute(
                select(FootfallDailyCamera.store_id)
                .where(
                    FootfallDailyCamera.brand_id == self.brand_id,
                    FootfallDailyCamera.day >= from_day,
                    FootfallDailyCamera.day <= to_day,
                )
                .distinct()
            ).all()
            for (sid,) in store_ids_result:
                s_metrics = self.conversion_analytics(
                    store_id=sid, from_day=from_day, to_day=to_day
                )
                store_breakdown.append({
                    "store_id": sid,
                    "total_visitors": s_metrics["total_visitors"],
                    "purchases": s_metrics["purchases"],
                    "conversion_pct": s_metrics["conversion_pct"],
                    "revenue_per_visitor": s_metrics["revenue_per_visitor"],
                })

        return {
            "store_id": store_id,
            "from_day": str(from_day),
            "to_day": str(to_day),
            "total_visitors": total_visitors,
            "purchases": tx_count,
            "total_revenue": round(total_revenue, 2),
            "conversion_pct": conversion_pct,
            "revenue_per_visitor": revenue_per_visitor,
            "store_breakdown": store_breakdown,
        }

    def transaction_list(
        self,
        store_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        from shared.schemas.pagination import paginate

        stmt = select(POSPurchase).where(POSPurchase.brand_id == self.brand_id)
        if store_id:
            stmt = stmt.where(POSPurchase.store_id == store_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        rows = list(
            self.db.scalars(
                stmt.order_by(POSPurchase.timestamp.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        items = [
            {
                "id": str(r.id),
                "store_id": r.store_id,
                "visitor_id": str(r.visitor_id),
                "transaction_external_id": r.transaction_external_id,
                "amount": r.amount,
                "items_count": r.items_count,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ]
        return paginate(items, total=total, page=page, page_size=page_size)
