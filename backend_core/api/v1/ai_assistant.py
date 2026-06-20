"""AI Assistant API routes (Phase 5)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.ai.rag_service import RagService
from shared.config import get_settings
from shared.database.ai_models import ChatMessage, ChatSession
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/v1/ai/assistant", tags=["ai-assistant"])


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[uuid.UUID] = None


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: Optional[list[dict[str, Any]]] = None
    created_at: datetime


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    summary: str
    kpis: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    messages: list[ChatMessageOut]


@router.post("/chat", response_model=ChatResponse, summary="Send query to AI assistant")
def chat(
    payload: ChatRequest,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Continues or starts a chat session with the Orzen Vision AI Assistant.

    Translates user query to SQL/aggregations, retrieves live metrics,
    and returns a structured response with sources.
    """
    brand_id = tenant.brand_id

    # Resolve or create ChatSession
    session = None
    if payload.session_id:
        session = db.scalar(
            select(ChatSession).where(
                ChatSession.id == payload.session_id, ChatSession.brand_id == brand_id
            )
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    
    if not session:
        # Create new chat session with a truncated query as the title
        title = payload.query[:50] + "..." if len(payload.query) > 50 else payload.query
        session = ChatSession(brand_id=brand_id, title=title)
        db.add(session)
        db.flush()

    # Load conversation history for memory context
    history_stmt = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc())
    history_msgs = db.scalars(history_stmt).all()
    
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_msgs
    ]

    # Save User message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.query,
        sources=[]
    )
    db.add(user_msg)
    db.flush()

    # Execute RAG Service
    rag = RagService(db, get_settings(), brand_id)
    ai_result = rag.generate_answer(payload.query, conversation_history)

    # Save Assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_result["answer"],
        sources=ai_result.get("sources", [])
    )
    db.add(assistant_msg)
    db.commit()

    # Prepare response messages
    all_msgs_stmt = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc())
    all_msgs = db.scalars(all_msgs_stmt).all()
    
    msg_out_list = [
        ChatMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            created_at=m.created_at
        )
        for m in all_msgs
    ]

    return ChatResponse(
        session_id=session.id,
        answer=ai_result["answer"],
        summary=ai_result.get("summary", ""),
        kpis=ai_result.get("kpis", []),
        sources=ai_result.get("sources", []),
        messages=msg_out_list
    )


@router.get("/sessions", response_model=list[ChatSessionOut], summary="List AI chat sessions")
def list_sessions(
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """Returns a list of all active chat sessions/threads for the brand."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.brand_id == tenant.brand_id)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = db.scalars(stmt).all()
    return [
        ChatSessionOut(id=s.id, title=s.title, created_at=s.created_at)
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=list[ChatMessageOut], summary="Get chat session details")
def get_session_details(
    session_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_optional),
    db: Session = Depends(get_db),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """Returns the full message list for a specific chat session."""
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.brand_id == tenant.brand_id
        )
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
    stmt = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc())
    messages = db.scalars(stmt).all()
    return [
        ChatMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            created_at=m.created_at
        )
        for m in messages
    ]
