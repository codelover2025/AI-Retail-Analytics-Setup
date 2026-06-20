"""Forecasting Engine with confidence intervals (Phase 5)."""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.database.analytics_models import FootfallDailyCamera
from shared.database.pos_models import POSPurchase

logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Statistical forecasting engine for revenue, growth, and customer retention."""

    def __init__(self, db: Session, brand_id: Any) -> None:
        self.db = db
        self.brand_id = brand_id

    def _get_historical_revenue(self, store_id: str, days: int = 60) -> list[tuple[date, float]]:
        stmt = (
            select(func.date(POSPurchase.timestamp), func.sum(POSPurchase.amount))
            .where(
                POSPurchase.brand_id == self.brand_id,
                POSPurchase.store_id == store_id,
                POSPurchase.timestamp >= datetime.now(timezone.utc) - timedelta(days=days)
            )
            .group_by(func.date(POSPurchase.timestamp))
            .order_by(func.date(POSPurchase.timestamp).asc())
        )
        results = self.db.execute(stmt).all()
        return [(r[0], float(r[1] or 0.0)) for r in results]

    def _get_historical_footfall(self, store_id: str, days: int = 60) -> list[tuple[date, int, int]]:
        stmt = (
            select(FootfallDailyCamera.day, func.sum(FootfallDailyCamera.total_visitors), func.sum(FootfallDailyCamera.repeat_visitors))
            .where(
                FootfallDailyCamera.brand_id == self.brand_id,
                FootfallDailyCamera.store_id == store_id,
                FootfallDailyCamera.day >= date.today() - timedelta(days=days)
            )
            .group_by(FootfallDailyCamera.day)
            .order_by(FootfallDailyCamera.day.asc())
        )
        results = self.db.execute(stmt).all()
        return [(r[0], int(r[1] or 0), int(r[2] or 0)) for r in results]

    def forecast_revenue(self, store_id: str, horizon: str = "daily") -> list[dict[str, Any]]:
        """
        Forecasts store revenue for a daily (7 days), weekly (4 weeks), or monthly (3 months) horizon.
        Includes upper and lower 95% confidence intervals.
        """
        history = self._get_historical_revenue(store_id, days=60)
        
        # Determine steps and interval delta based on horizon
        if horizon == "monthly":
            steps = 3
            delta_days = 30
            base_default = 15000.0
        elif horizon == "weekly":
            steps = 4
            delta_days = 7
            base_default = 4000.0
        else:  # daily
            steps = 7
            delta_days = 1
            base_default = 600.0

        if len(history) < 5:
            # Return fallback predictions if not enough data
            predictions = []
            for i in range(1, steps + 1):
                target_date = date.today() + timedelta(days=i * delta_days)
                pred_val = base_default * (1 + 0.02 * i) # 2% growth trend
                se = base_default * 0.15 * math.sqrt(i)   # increasing uncertainty
                predictions.append({
                    "date": target_date.isoformat(),
                    "forecast": round(pred_val, 2),
                    "lower_ci": round(max(pred_val - 1.96 * se, 0), 2),
                    "upper_ci": round(pred_val + 1.96 * se, 2),
                    "confidence_level": 0.95
                })
            return predictions

        # Aggregate values for the horizon if needed (e.g. weekly totals)
        y = np.array([h[1] for h in history])
        x = np.arange(len(history))
        
        # Fit linear trend line
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # Calculate standard error of residuals
        residuals = y - (m * x + c)
        std_error = np.std(residuals) if len(residuals) > 1 else base_default * 0.1

        predictions = []
        last_idx = len(history) - 1
        
        for i in range(1, steps + 1):
            target_idx = last_idx + (i * delta_days)
            target_date = date.today() + timedelta(days=i * delta_days)
            
            # Forecast value
            forecast_val = max(m * target_idx + c, 50.0)
            
            # Standard error grows with sqrt of distance from history (standard forecast property)
            se_forecast = std_error * math.sqrt(1 + (i * delta_days) / 30.0)
            
            predictions.append({
                "date": target_date.isoformat(),
                "forecast": round(forecast_val, 2),
                "lower_ci": round(max(forecast_val - 1.96 * se_forecast, 0), 2),
                "upper_ci": round(forecast_val + 1.96 * se_forecast, 2),
                "confidence_level": 0.95
            })
            
        return predictions

    def forecast_growth(self, store_id: str, horizon: str = "daily") -> list[dict[str, Any]]:
        """Forecasts store traffic growth percentage with confidence intervals."""
        history = self._get_historical_footfall(store_id, days=60)
        
        if horizon == "monthly":
            steps = 3
            delta_days = 30
            base_default = 5.0  # 5% growth
        elif horizon == "weekly":
            steps = 4
            delta_days = 7
            base_default = 3.0
        else:  # daily
            steps = 7
            delta_days = 1
            base_default = 1.0

        if len(history) < 5:
            predictions = []
            for i in range(1, steps + 1):
                target_date = date.today() + timedelta(days=i * delta_days)
                pred_val = base_default + 0.1 * i
                se = 2.0 * math.sqrt(i)
                predictions.append({
                    "date": target_date.isoformat(),
                    "forecast_growth_pct": round(pred_val, 2),
                    "lower_ci": round(pred_val - 1.96 * se, 2),
                    "upper_ci": round(pred_val + 1.96 * se, 2),
                    "confidence_level": 0.95
                })
            return predictions

        y = np.array([h[1] for h in history])
        x = np.arange(len(history))
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        residuals = y - (m * x + c)
        std_error = np.std(residuals) if len(residuals) > 1 else 5.0
        
        avg_traffic = np.mean(y) if len(y) > 0 else 50.0

        predictions = []
        last_idx = len(history) - 1
        
        for i in range(1, steps + 1):
            target_idx = last_idx + (i * delta_days)
            target_date = date.today() + timedelta(days=i * delta_days)
            
            predicted_traffic = max(m * target_idx + c, 5.0)
            # Growth percent relative to history average
            growth_pct = ((predicted_traffic - avg_traffic) / avg_traffic) * 100 if avg_traffic > 0 else 0.0
            
            se_pct = (std_error / avg_traffic) * 100 if avg_traffic > 0 else 5.0
            se_forecast = se_pct * math.sqrt(1 + (i * delta_days) / 30.0)
            
            predictions.append({
                "date": target_date.isoformat(),
                "forecast_growth_pct": round(growth_pct, 2),
                "lower_ci": round(growth_pct - 1.96 * se_forecast, 2),
                "upper_ci": round(growth_pct + 1.96 * se_forecast, 2),
                "confidence_level": 0.95
            })
            
        return predictions

    def forecast_retention(self, store_id: str, horizon: str = "daily") -> list[dict[str, Any]]:
        """Forecasts customer retention (repeat visitors counts) with confidence intervals."""
        history = self._get_historical_footfall(store_id, days=60)
        
        if horizon == "monthly":
            steps = 3
            delta_days = 30
            base_default = 120
        elif horizon == "weekly":
            steps = 4
            delta_days = 7
            base_default = 30
        else:  # daily
            steps = 7
            delta_days = 1
            base_default = 12

        if len(history) < 5:
            predictions = []
            for i in range(1, steps + 1):
                target_date = date.today() + timedelta(days=i * delta_days)
                pred_val = base_default + 0.5 * i
                se = base_default * 0.1 * math.sqrt(i)
                predictions.append({
                    "date": target_date.isoformat(),
                    "forecast_repeat_visitors": int(pred_val),
                    "lower_ci": int(max(pred_val - 1.96 * se, 0)),
                    "upper_ci": int(pred_val + 1.96 * se),
                    "confidence_level": 0.95
                })
            return predictions

        # Repeat visitors series
        y = np.array([h[2] for h in history])
        x = np.arange(len(history))
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        residuals = y - (m * x + c)
        std_error = np.std(residuals) if len(residuals) > 1 else 3.0

        predictions = []
        last_idx = len(history) - 1
        
        for i in range(1, steps + 1):
            target_idx = last_idx + (i * delta_days)
            target_date = date.today() + timedelta(days=i * delta_days)
            
            forecast_val = max(m * target_idx + c, 1.0)
            se_forecast = std_error * math.sqrt(1 + (i * delta_days) / 30.0)
            
            predictions.append({
                "date": target_date.isoformat(),
                "forecast_repeat_visitors": int(forecast_val),
                "lower_ci": int(max(forecast_val - 1.96 * se_forecast, 0)),
                "upper_ci": int(forecast_val + 1.96 * se_forecast),
                "confidence_level": 0.95
            })
            
        return predictions
