"""Unit tests for LLM client and RAG synthesis (Phase 5)."""

from __future__ import annotations

import json
import os
import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.services.ai.llm_client import get_llm_client, StubLlmClient
from backend_core.services.ai.rag_service import RagService
from shared.config import Settings
from shared.database.models import Base
from shared.database.tenant_models import Store


@pytest.fixture(name="db")
def fixture_db() -> Generator[Session, None, None]:
    """In-memory SQLite database for test runs."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_llm_factory() -> None:
    """Verifies settings factory returns correct LLM instances."""
    os.environ["LLM_PROVIDER"] = "stub"
    settings = Settings()
    client = get_llm_client(settings)
    assert isinstance(client, StubLlmClient)
    
    # Test chat return format
    response = client.chat(messages=[{"role": "user", "content": "hello"}], response_format_json=True)
    data = json.loads(response)
    assert "answer" in data
    assert "summary" in data


def test_rag_service_intent_fallback(db: Session) -> None:
    """Verifies RAG intent extraction fallbacks function correctly."""
    settings = Settings()
    brand_id = uuid.uuid4()
    
    # Seed a store
    store = Store(
        id=uuid.uuid4(),
        brand_id=brand_id,
        name="Mumbai Jewelers",
        external_id="mumbai-01",
        is_active=True
    )
    db.add(store)
    db.commit()

    rag = RagService(db, settings, brand_id)
    intent = rag.extract_query_intent("Why did Mumbai footfall decrease yesterday?")
    
    # Verify Mumbai was extracted and mapped
    assert "mumbai-01" in intent["store_ids"]
    assert intent["topic"] == "footfall"

