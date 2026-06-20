"""Unit tests for Predictive Analytics Service (Phase 5)."""

from __future__ import annotations

import datetime
import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.services.ai.predictive_analytics import PredictiveAnalyticsService
from shared.config import Settings
from shared.database.models import Base
from shared.database.tenant_models import Store


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


def test_predictive_service_fallbacks(db: Session) -> None:
    """Verifies that mathematical predictions work with sparse/seeded data."""
    brand_id = uuid.uuid4()
    svc = PredictiveAnalyticsService(db, brand_id)
    
    store_id = "store-001"
    
    # Test Footfall Predictions
    footfall = svc.predict_footfall(store_id, days_ahead=5)
    assert len(footfall) == 5
    assert "date" in footfall[0]
    assert footfall[0]["predicted_visitors"] > 0
    
    # Test Peak Hours
    peaks = svc.predict_peak_hours(store_id)
    assert len(peaks) > 0
    assert "hour" in peaks[0]
    
    # Test Staff Requirements
    staffing = svc.predict_staff_requirement(store_id, days_ahead=3)
    assert len(staffing) == 3
    assert staffing[0]["recommended_staff_count"] >= 2
    
    # Test Store Performance Score
    performance = svc.predict_store_performance(store_id)
    assert "score" in performance
    assert 0 <= performance["score"] <= 100
    assert "rating" in performance

