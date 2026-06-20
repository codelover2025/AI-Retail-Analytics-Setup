"""Integration tests for Phase 5 AI Assistant, Voice, and ML endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend_core.main import app
from shared.config import get_settings


@pytest.fixture(name="client")
def fixture_client() -> TestClient:
    return TestClient(app)


def test_unauthorized_endpoints(client: TestClient) -> None:
    """Verifies that endpoints fail without appropriate JWT auth tokens."""
    settings = get_settings()
    
    # 1. AI chat endpoint
    resp1 = client.post("/api/v1/ai/assistant/chat", json={"query": "hello"})
    assert resp1.status_code == 401  # Unauthorized
    
    # 2. Voice endpoints
    resp2 = client.post("/api/v1/ai/voice/tts", json={"text": "hello"})
    assert resp2.status_code == 401
    
    # 3. Predictions
    resp3 = client.get("/api/v1/ai/predictions")
    assert resp3.status_code == 401
    
    # 4. Forecasts
    resp4 = client.get("/api/v1/ai/forecasts")
    assert resp4.status_code == 401

    # 5. RBAC profile / permissions endpoint
    resp5 = client.get("/api/rbac/me")
    assert resp5.status_code == 401


def test_rate_limiting(client: TestClient) -> None:
    """Verifies RateLimitingMiddleware intercepts too many rapid requests."""
    # Send 70 requests rapidly to hit the limit (configured at max 60/minute)
    limited = False
    
    # We send dummy headers to endpoints under rate limiter
    for _ in range(70):
        # Even unauthorized requests are rate-limited on IP checks first
        resp = client.get("/api/v1/ai/predictions")
        if resp.status_code == 429:
            limited = True
            break
            
    assert limited, "Rate limiter should trigger 429 Too Many Requests"


def test_health_detailed_metrics(client: TestClient) -> None:
    """Verifies detailed health endpoint returns database pool metrics."""
    resp = client.get("/api/v1/health/detailed")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "subsystems" in data
    assert "database" in data["subsystems"]
    db_info = data["subsystems"]["database"]
    assert db_info["status"] == "ok"
    assert "pool" in db_info
    assert "class" in db_info["pool"]
