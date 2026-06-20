"""Recommendation Engine analyzing retail store performance (Phase 5)."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.services.dashboard_service import DashboardService
from backend_core.services.multi_camera_analytics import MultiCameraAnalyticsService
from shared.database.models import Visitor
from shared.database.pos_models import POSPurchase
from shared.database.tenant_models import Store

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Analyzes store performance metrics and generates structured business recommendations."""

    def __init__(self, db: Session, brand_id: Any) -> None:
        self.db = db
        self.brand_id = brand_id
        self.dash = DashboardService(db, None, brand_id) # Type settings as None, handled in constructor

    def generate_recommendations(self, store_id: str) -> list[dict[str, Any]]:
        """
        Queries analytics tables and evaluates rules to produce actionable structured recommendations.
        """
        # Fetch last 30 days of data for the store
        to_day = date.today()
        from_day = to_day - timedelta(days=29)

        # Get general store metrics
        try:
            svc = MultiCameraAnalyticsService(self.db, self.dash.settings, self.brand_id, store_id)
            ff = svc.footfall(from_day=from_day, days=30)
            dwell = svc.dwell_time(days=30)
            zones = svc.zones(days=30)
            repeats = svc.repeat_analytics(days=30)
        except Exception as exc:
            logger.warning("Could not gather store metrics for recommendations: %s", exc)
            return self._generate_default_recommendations()

        recommendations = []

        # 1. Staffing Recommendations
        # Check repeat vs new or peak hour patterns
        avg_dwell = dwell.avg_dwell_seconds
        total_visitors = ff.summary.total_visitors
        
        # If store has high footfall but average dwell time is low, suggest staffing assistance
        if total_visitors > 100 and avg_dwell < 60:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "category": "staffing",
                "title": "Increase Floor Coverage during Peak Hours",
                "description": "High footfall coupled with very low average dwell times indicates customers may be leaving without assistance.",
                "confidence_score": 0.88,
                "impact_level": "High",
                "actionable_steps": [
                    "Schedule extra staff during the peak hours identified in predictive analytics.",
                    "Position an greeter near the entrance to welcome visitors and guide them.",
                    "Ensure sales representatives actively engage customers spending over 3 minutes in jewelry zones."
                ]
            })

        # 2. Marketing Recommendations
        # Check repeat visitor ratio
        repeat_ratio = repeats.repeat_ratio
        if repeat_ratio < 0.20:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "category": "marketing",
                "title": "Launch New Customer Loyalty Campaign",
                "description": f"Repeat visitor ratio is low ({round(repeat_ratio * 100, 1)}%). Prioritize retention marketing.",
                "confidence_score": 0.82,
                "impact_level": "Medium",
                "actionable_steps": [
                    "Implement a loyalty signup incentive (e.g. 5% off next purchase).",
                    "Target first-time visitors with WhatsApp welcome codes.",
                    "Promote premium VIP member benefits at checkout."
                ]
            })
        elif repeat_ratio > 0.45:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "category": "marketing",
                "title": "Exclusive VIP Showcase Event",
                "description": f"Loyal customer base is strong ({round(repeat_ratio * 100, 1)}%). Leverage this to drive higher LTV.",
                "confidence_score": 0.90,
                "impact_level": "High",
                "actionable_steps": [
                    "Invite top 50 repeat visitors to a private collection viewing.",
                    "Offer personalized incentives to VIP customers who haven't visited in 14 days.",
                    "Introduce a referral rewards program for repeat buyers."
                ]
            })

        # 3. Store Layout & Product Placement Recommendations
        # Check zone dwell distributions
        if zones.zones:
            top_zone = zones.zones[0]
            # Identify low-performing zones (high dwell count but low overall time relative to others)
            least_zone = zones.zones[-1]
            if len(zones.zones) > 1 and least_zone.visit_count > 5:
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "category": "layout",
                    "title": f"Revitalize the '{least_zone.zone_name}' Zone Layout",
                    "description": f"The '{least_zone.zone_name}' zone has the lowest engagement. Only averaging {least_zone.avg_time_spent}s per visit.",
                    "confidence_score": 0.85,
                    "impact_level": "Medium",
                    "actionable_steps": [
                        f"Audit lighting and visibility of displays in the '{least_zone.zone_name}' zone.",
                        "Place high-demand promotional items or best-sellers near this area to draw traffic.",
                        "Reconfigure signage or pathways to naturally guide customer journeys toward this zone."
                    ]
                })

            # High-performing zone cross-merchandising
            recommendations.append({
                "id": str(uuid.uuid4()),
                "category": "placement",
                "title": f"Leverage High Traffic in '{top_zone.zone_name}'",
                "description": f"'{top_zone.zone_name}' is your most popular zone with {top_zone.visit_count} engagements.",
                "confidence_score": 0.95,
                "impact_level": "High",
                "actionable_steps": [
                    "Cross-promote items from low-traffic zones within this hot spot.",
                    "Ensure maximum employee coverage in this zone during peak hours.",
                    "Deploy digital kiosks or video catalog displays here to showcase items."
                ]
            })

        # 4. Conversion & Business Optimization
        # Check POS data to evaluate transaction conversion rates
        try:
            pos_stmt = select(func.count(POSPurchase.id)).where(
                POSPurchase.brand_id == self.brand_id,
                POSPurchase.store_id == store_id,
                POSPurchase.timestamp >= datetime.now(timezone.utc) - timedelta(days=30)
            )
            transactions = self.db.scalar(pos_stmt) or 0
            if total_visitors > 0:
                conversion_rate = transactions / total_visitors
                if conversion_rate < 0.15:
                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "category": "business",
                        "title": "Optimize Checkout Flow and Impulse Product Display",
                        "description": f"Visitor-to-purchase conversion is low ({round(conversion_rate*100, 1)}%). Improve conversion efficiency.",
                        "confidence_score": 0.89,
                        "impact_level": "High",
                        "actionable_steps": [
                            "Streamline checkout counter operations to reduce queuing friction.",
                            "Train staff in upselling complementary cleaning kits or warranties.",
                            "Audit price competitiveness of entry-level and mid-range products."
                        ]
                    })
        except Exception:
            pass

        # Return default recommendations if no specific rules matched
        if not recommendations:
            return self._generate_default_recommendations()

        return recommendations

    def _generate_default_recommendations(self) -> list[dict[str, Any]]:
        return [
            {
                "id": str(uuid.uuid4()),
                "category": "marketing",
                "title": "Promote Mid-Week Campaigns",
                "description": "Increase store footfall during historical mid-week low traffic intervals.",
                "confidence_score": 0.75,
                "impact_level": "Medium",
                "actionable_steps": [
                    "Host Wednesday promotional campaigns.",
                    "Send direct SMS/WhatsApp vouchers to local customers."
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "category": "layout",
                "title": "Optimize Counter Placement",
                "description": "Improve zone-to-zone customer transitions based on standard layouts.",
                "confidence_score": 0.80,
                "impact_level": "Medium",
                "actionable_steps": [
                    "Arrange jewelry collections chronologically by price point.",
                    "Create open walkways around premium glass displays."
                ]
            }
        ]
