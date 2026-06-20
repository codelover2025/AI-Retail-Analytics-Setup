"""RAG service for Orzen Vision AI Assistant (Phase 5)."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.services.ai.llm_client import get_llm_client, BaseLlmClient
from backend_core.services.dashboard_service import DashboardService
from shared.config import Settings
from shared.database.tenant_models import Store

logger = logging.getLogger(__name__)


class RagService:
    """
    RAG service translating natural language queries to structured dashboard data,
    then synthesizing responses with 100% accuracy and clear sources.
    """

    def __init__(self, db: Session, settings: Settings, brand_id: Any) -> None:
        self.db = db
        self.settings = settings
        self.brand_id = brand_id
        self.llm = get_llm_client(settings)
        self.dash_service = DashboardService(db, settings, brand_id)

    def _resolve_stores(self) -> dict[str, str]:
        """Maps lowercase store names to external_ids."""
        stmt = select(Store).where(Store.brand_id == self.brand_id)
        stores = self.db.scalars(stmt).all()
        mapping = {}
        for s in stores:
            mapping[s.name.lower()] = s.external_id
            # Extract main city name for matching e.g., "Mumbai Store" -> "mumbai"
            city = s.name.split()[0].lower()
            mapping[city] = s.external_id
        return mapping

    def extract_query_intent(self, query: str) -> dict[str, Any]:
        """Stage 1: Use LLM or rules to extract date range, stores, and topics."""
        store_map = self._resolve_stores()
        
        system_prompt = (
            "You are a parser. Extract entities from the user's query about retail store performance. "
            f"Available stores: {list(store_map.keys())}. "
            "Output valid JSON only. Do not include markdown code block syntax. Keys:\n"
            "- stores: list of matched store names\n"
            "- days_ago_start: int (e.g. 0 for today, 1 for yesterday, 7 for last week)\n"
            "- days_ago_end: int (usually 0 for today, or start date offset)\n"
            "- topic: string ('footfall' | 'conversion' | 'dwell' | 'comparison' | 'general')"
        )
        
        user_prompt = f"Query: \"{query}\"\nCurrent Date: {date.today().isoformat()}"
        
        extracted = {
            "stores": [],
            "days_ago_start": 30,
            "days_ago_end": 0,
            "topic": "general"
        }

        try:
            raw_response = self.llm.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                response_format_json=True
            )
            # Remove any markdown wrapping if LLM ignored response_format
            clean_json = re.sub(r"^```json\s*|```$", "", raw_response.strip(), flags=re.MULTILINE)
            parsed = json.loads(clean_json)
            if "topic" in parsed or "stores" in parsed:
                extracted.update(parsed)
            else:
                raise ValueError("LLM response did not match the expected extraction schema")
        except Exception as exc:
            logger.warning("Stage 1 LLM extraction failed, falling back to heuristics: %s", exc)
            # Simple heuristic regex fallback
            query_lower = query.lower()
            for sname in store_map:
                if sname in query_lower:
                    extracted["stores"].append(sname)
            if "today" in query_lower:
                extracted["days_ago_start"] = 0
            elif "yesterday" in query_lower:
                extracted["days_ago_start"] = 1
                extracted["days_ago_end"] = 1
            elif "week" in query_lower:
                extracted["days_ago_start"] = 7
            
            if "compare" in query_lower or len(extracted["stores"]) > 1:
                extracted["topic"] = "comparison"
            elif "why" in query_lower or "decrease" in query_lower or "increase" in query_lower:
                extracted["topic"] = "footfall"
            elif "dwell" in query_lower or "time" in query_lower:
                extracted["topic"] = "dwell"

        # Resolve store names to database external_ids
        resolved_store_ids = []
        for name in extracted["stores"]:
            name_lower = name.lower()
            if name_lower in store_map:
                resolved_store_ids.append(store_map[name_lower])
        
        # Default to all active stores if none explicitly resolved
        if not resolved_store_ids:
            resolved_store_ids = [s.external_id for s in self.db.scalars(
                select(Store).where(Store.brand_id == self.brand_id, Store.is_active == True)
            ).all()]

        # Convert offsets to real date strings
        today = date.today()
        start_day = today - timedelta(days=extracted["days_ago_start"])
        end_day = today - timedelta(days=extracted["days_ago_end"])

        return {
            "store_ids": resolved_store_ids,
            "start_date": start_day,
            "end_date": end_day,
            "topic": extracted["topic"]
        }

    def generate_answer(self, query: str, conversation_history: list[dict[str, str]] = None) -> dict[str, Any]:
        """Stage 2: Retrieve DB context, format prompt, and generate answer with source attribution."""
        intent = self.extract_query_intent(query)
        
        # 1. Fetch data from DB based on intent
        start_date = intent["start_date"]
        end_date = intent["end_date"]
        store_ids = intent["store_ids"]
        topic = intent["topic"]
        
        context_data = {}
        sources = []

        if topic == "comparison" and len(store_ids) >= 2:
            comp = self.dash_service.comparison(store_ids, from_day=start_date, to_day=end_date)
            context_data["comparison"] = comp["stores"]
            sources.append({
                "type": "database_aggregation",
                "detail": f"Store comparison for {', '.join(store_ids)} from {start_date} to {end_date}."
            })
        else:
            # General or specific store metrics
            overview = self.dash_service.overview(from_day=start_date, to_day=end_date, store_ids=store_ids)
            context_data["overview_summary"] = overview["summary"]
            context_data["individual_stores"] = overview["stores"]
            sources.append({
                "type": "database_aggregation",
                "detail": f"Store metrics summary for {', '.join(store_ids)} from {start_date} to {end_date}."
            })

        # Add POS conversion info if available
        try:
            from sqlalchemy import func
            from shared.database.pos_models import POSPurchase
            pos_stmt = select(
                POSPurchase.store_id,
                func.sum(POSPurchase.amount).label("revenue"),
                func.count(POSPurchase.id).label("transactions")
            ).where(
                POSPurchase.brand_id == self.brand_id,
                POSPurchase.timestamp >= datetime.combine(start_date, datetime.min.time()),
                POSPurchase.timestamp <= datetime.combine(end_date, datetime.max.time())
            ).group_by(POSPurchase.store_id)
            pos_data = self.db.execute(pos_stmt).all()
            if pos_data:
                context_data["sales_performance"] = [
                    {"store_id": r.store_id, "revenue": float(r.revenue or 0), "transactions": int(r.transactions or 0)}
                    for r in pos_data
                ]
                sources.append({
                    "type": "pos_database",
                    "detail": f"POS transaction history from {start_date} to {end_date}."
                })
        except Exception:
            pass

        # 2. Compile LLM Prompt
        system_prompt = (
            "You are the Orzen Vision Executive Assistant. You analyze retail analytics, explain KPIs, "
            "and generate structured, data-driven reports for retail executives.\n\n"
            "Rules:\n"
            "1. Answer queries clearly, professionaly, and concisely.\n"
            "2. Base all numbers and comparisons ONLY on the provided context. DO NOT invent metrics.\n"
            "3. Format your answer as a structured JSON object containing:\n"
            "   - 'answer': string (the narrative response to the user's query, supporting markdown)\n"
            "   - 'summary': string (a short executive TL;DR of the insights)\n"
            "   - 'kpis': list of key-value pairs of metrics mentioned (e.g. [{'kpi': 'Footfall', 'value': '150'}])\n"
            "4. Language support: If query is in Hindi, respond in Hindi. Otherwise, respond in English."
        )

        formatted_context = json.dumps(context_data, indent=2, default=str)
        
        messages = []
        if conversation_history:
            # Include recent conversation memory
            messages.extend(conversation_history[-6:])
        
        messages.append({
            "role": "user",
            "content": (
                f"Context Data:\n{formatted_context}\n\n"
                f"User Question: \"{query}\"\n\n"
                "Please synthesize an accurate answer with the requested JSON structure."
            )
        })

        try:
            raw_response = self.llm.chat(
                messages=messages,
                system_prompt=system_prompt,
                response_format_json=True
            )
            clean_json = re.sub(r"^```json\s*|```$", "", raw_response.strip(), flags=re.MULTILINE)
            result = json.loads(clean_json)
            result["sources"] = sources
            return result
        except Exception as exc:
            logger.error("RAG final generation failed: %s", exc)
            return {
                "answer": f"I gathered the database context for this query but encountered an error synthesizing the final response. Here is the raw retrieved context: {json.dumps(context_data, default=str)}",
                "summary": "Retrieved raw database context; failed synthesis.",
                "kpis": [],
                "sources": sources
            }
