"""Predictive Analytics Service using historical DB data (Phase 5)."""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.database.analytics_models import AnalyticsSession, FootfallDailyCamera
from shared.database.models import Visitor
from shared.database.pos_models import POSPurchase
from shared.database.tenant_models import Camera, Store

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """Computes mathematical retail predictions using historical analytics."""

    def __init__(self, db: Session, brand_id: Any) -> None:
        self.db = db
        self.brand_id = brand_id

    def _get_historical_daily_footfall(self, store_id: str, limit_days: int = 30) -> list[tuple[date, int, int]]:
        """Fetches daily footfall and repeat visitors for a store."""
        # Find store database ID or use store_id as external_id directly
        stmt = (
            select(FootfallDailyCamera.day, func.sum(FootfallDailyCamera.total_visitors), func.sum(FootfallDailyCamera.repeat_visitors))
            .where(
                FootfallDailyCamera.brand_id == self.brand_id,
                FootfallDailyCamera.store_id == store_id,
                FootfallDailyCamera.day >= date.today() - timedelta(days=limit_days)
            )
            .group_by(FootfallDailyCamera.day)
            .order_by(FootfallDailyCamera.day.asc())
        )
        results = self.db.execute(stmt).all()
        return [(r[0], int(r[1] or 0), int(r[2] or 0)) for r in results]

    def predict_footfall(self, store_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
        """
        Predicts footfall for the next N days.
        Uses a linear trend model with day-of-week seasonality factors.
        """
        history = self._get_historical_daily_footfall(store_id, limit_days=45)
        
        # Fallback to defaults if history is empty
        if len(history) < 7:
            logger.warning("Insufficient history for footfall prediction, returning default values.")
            predictions = []
            for i in range(1, days_ahead + 1):
                target_day = date.today() + timedelta(days=i)
                # Mock average footfall: 50 + sin wave for weekly pattern
                avg_visitors = 40 + int(15 * math.sin(target_day.weekday()))
                predictions.append({
                    "date": target_day.isoformat(),
                    "predicted_visitors": avg_visitors,
                    "confidence_score": 0.65
                })
            return predictions

        # Build training arrays
        y = np.array([h[1] for h in history])
        x = np.arange(len(history))
        
        # Fit linear model manually (least squares)
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # Calculate day-of-week seasonal index
        dow_totals: dict[int, list[float]] = {i: [] for i in range(7)}
        for idx, (_, val, _) in enumerate(history):
            trend_val = m * idx + c
            # Seasonal factor is ratio of actual to trend
            factor = val / trend_val if trend_val > 0 else 1.0
            dow_totals[idx % 7].append(factor)
            
        dow_factors = {dow: (sum(factors) / len(factors) if factors else 1.0) for dow, factors in dow_totals.items()}
        
        # Generate predictions
        predictions = []
        last_idx = len(history) - 1
        for i in range(1, days_ahead + 1):
            target_day = date.today() + timedelta(days=i)
            target_idx = last_idx + i
            base_trend = m * target_idx + c
            
            # Apply seasonality
            factor = dow_factors.get(target_day.weekday(), 1.0)
            predicted = max(int(base_trend * factor), 5)
            
            predictions.append({
                "date": target_day.isoformat(),
                "predicted_visitors": predicted,
                "confidence_score": round(min(0.95, 0.85 + 0.1 / i), 2)
            })
            
        return predictions

    def predict_peak_hours(self, store_id: str) -> list[dict[str, Any]]:
        """
        Analyzes historical entry times to identify peak operating hours.
        Returns predicted busiest hours with traffic distribution weights.
        """
        stmt = (
            select(AnalyticsSession.entry_time)
            .where(
                AnalyticsSession.brand_id == self.brand_id,
                AnalyticsSession.store_id == store_id,
                AnalyticsSession.entry_time >= datetime.now(timezone.utc) - timedelta(days=30)
            )
        )
        sessions = self.db.scalars(stmt).all()
        
        # Hourly buckets (0 to 23)
        hours = [0] * 24
        for s in sessions:
            if s:
                # Convert to local timezone or read hour directly
                hours[s.hour] += 1
                
        total_sessions = len(sessions)
        
        # Provide default distribution if no data
        if total_sessions < 10:
            default_peaks = [
                {"hour": 11, "label": "11:00 AM", "weight": 0.12},
                {"hour": 12, "label": "12:00 PM", "weight": 0.15},
                {"hour": 17, "label": "05:00 PM", "weight": 0.14},
                {"hour": 18, "label": "06:00 PM", "weight": 0.18},
                {"hour": 19, "label": "07:00 PM", "weight": 0.11},
            ]
            return default_peaks

        hourly_breakdown = []
        for h in range(24):
            weight = hours[h] / total_sessions
            ampm = "AM" if h < 12 else "PM"
            display_h = h if h <= 12 else h - 12
            if display_h == 0:
                display_h = 12
            label = f"{display_h:02d}:00 {ampm}"
            
            hourly_breakdown.append({
                "hour": h,
                "label": label,
                "weight": round(weight, 4)
            })
            
        # Sort by weight desc and take top 5 peak hours
        hourly_breakdown.sort(key=lambda x: x["weight"], reverse=True)
        return hourly_breakdown[:5]

    def predict_repeat_visitors(self, store_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Predicts repeat visitor counts and ratios for upcoming days."""
        history = self._get_historical_daily_footfall(store_id, limit_days=30)
        
        if not history:
            predictions = []
            for i in range(1, days_ahead + 1):
                target_day = date.today() + timedelta(days=i)
                predictions.append({
                    "date": target_day.isoformat(),
                    "predicted_repeat_ratio": 0.35,  # 35% typical
                    "confidence_score": 0.70
                })
            return predictions

        # Compute average repeat ratio
        total_v = sum(h[1] for h in history)
        total_r = sum(h[2] for h in history)
        avg_ratio = total_r / total_v if total_v > 0 else 0.30

        predictions = []
        for i in range(1, days_ahead + 1):
            target_day = date.today() + timedelta(days=i)
            predictions.append({
                "date": target_day.isoformat(),
                "predicted_repeat_ratio": round(avg_ratio, 4),
                "confidence_score": round(min(0.90, 0.80 + 0.1 / i), 2)
            })
        return predictions

    def predict_conversion_probability(self, store_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Predicts the checkout conversion rate using POS and footfall data."""
        # Get historical transaction count by day
        pos_stmt = (
            select(func.date(POSPurchase.timestamp), func.count(POSPurchase.id))
            .where(
                POSPurchase.brand_id == self.brand_id,
                POSPurchase.store_id == store_id,
                POSPurchase.timestamp >= datetime.now(timezone.utc) - timedelta(days=30)
            )
            .group_by(func.date(POSPurchase.timestamp))
        )
        pos_history = {r[0]: r[1] for r in self.db.execute(pos_stmt).all()}

        footfall_history = self._get_historical_daily_footfall(store_id, limit_days=30)
        
        conversions = []
        for d, ff, _ in footfall_history:
            tx = pos_history.get(d, 0)
            ratio = tx / ff if ff > 0 else 0.0
            conversions.append(ratio)

        avg_conversion = sum(conversions) / len(conversions) if conversions else 0.15 # 15% default

        predictions = []
        for i in range(1, days_ahead + 1):
            target_day = date.today() + timedelta(days=i)
            predictions.append({
                "date": target_day.isoformat(),
                "conversion_probability": round(avg_conversion, 4),
                "confidence_score": 0.80
            })
        return predictions

    def predict_staff_requirement(self, store_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Recommends staff counts based on predicted footfall density (e.g., 1 staff per 15 customers)."""
        footfall_preds = self.predict_footfall(store_id, days_ahead=days_ahead)
        
        staff_recommendations = []
        for f in footfall_preds:
            visitors = f["predicted_visitors"]
            # Base requirement: 2 staff. Add 1 staff for every 15 customers above 20.
            recommended_staff = max(2, int(2 + math.ceil((visitors - 20) / 15)))
            
            staff_recommendations.append({
                "date": f["date"],
                "predicted_footfall": visitors,
                "recommended_staff_count": recommended_staff,
                "confidence_score": f["confidence_score"]
            })
        return staff_recommendations

    def predict_store_performance(self, store_id: str) -> dict[str, Any]:
        """Calculates a multi-factor score (0-100) on current store performance."""
        # 1. Footfall performance vs average
        history = self._get_historical_daily_footfall(store_id, limit_days=14)
        if not history:
            return {"score": 70, "rating": "Average", "metrics": {"footfall_score": 70, "conversion_score": 70}}

        avg_ff = sum(h[1] for h in history) / len(history)
        ff_score = min(100, int((avg_ff / 50.0) * 100)) # Benchmark 50 visitors/day

        # 2. Conversion score
        pos_stmt = (
            select(func.count(POSPurchase.id))
            .where(
                POSPurchase.brand_id == self.brand_id,
                POSPurchase.store_id == store_id,
                POSPurchase.timestamp >= datetime.now(timezone.utc) - timedelta(days=14)
            )
        )
        total_pos = self.db.scalar(pos_stmt) or 0
        total_ff = sum(h[1] for h in history)
        
        conversion_rate = total_pos / total_ff if total_ff > 0 else 0.0
        conversion_score = min(100, int((conversion_rate / 0.25) * 100)) # Benchmark 25% conversion

        # 3. Overall performance score
        overall_score = int(0.4 * ff_score + 0.6 * conversion_score)
        
        if overall_score >= 85:
            rating = "Excellent"
        elif overall_score >= 70:
            rating = "Good"
        elif overall_score >= 50:
            rating = "Average"
        else:
            rating = "Underperforming"

        return {
            "score": overall_score,
            "rating": rating,
            "metrics": {
                "footfall_index": ff_score,
                "conversion_index": conversion_score,
                "average_daily_footfall": round(avg_ff, 1),
                "conversion_rate": round(conversion_rate, 4)
            }
        }
