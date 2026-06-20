"""Unit tests for Forecasting Engine (Phase 5)."""

from __future__ import annotations

import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.services.ai.forecasting_engine import ForecastingEngine
from shared.config import Settings
from shared.database.models import Base


@pytest.fixture(name="db")
def fixture_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_forecasting_bounds(db: Session) -> None:
    """Checks daily/weekly/monthly horizons and confidence intervals."""
    brand_id = uuid.uuid4()
    engine = ForecastingEngine(db, brand_id)
    
    store_id = "store-001"
    
    # 1. Test Revenue Forecast
    rev_forecast = engine.forecast_revenue(store_id, horizon="daily")
    assert len(rev_forecast) == 7
    for f in rev_forecast:
        assert f["lower_ci"] <= f["forecast"] <= f["upper_ci"]
        assert f["confidence_level"] == 0.95

    # 2. Test Store Growth Forecast
    growth_forecast = engine.forecast_growth(store_id, horizon="weekly")
    assert len(growth_forecast) == 4
    for f in growth_forecast:
        assert f["lower_ci"] <= f["forecast_growth_pct"] <= f["upper_ci"]

    # 3. Test Customer Retention Forecast
    ret_forecast = engine.forecast_retention(store_id, horizon="monthly")
    assert len(ret_forecast) == 3
    for f in ret_forecast:
        assert f["lower_ci"] <= f["forecast_repeat_visitors"] <= f["upper_ci"]
