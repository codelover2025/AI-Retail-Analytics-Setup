"""Voice AI API routes (Phase 5)."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import io

from backend_core.auth.dependencies import get_tenant_optional
from backend_core.auth.rbac import UserContext, require_role
from backend_core.services.ai.voice_service import VoiceService
from shared.database.session import get_db
from shared.tenant_context import TenantContext

router = APIRouter(prefix="/api/v1/ai/voice", tags=["voice-ai"])


class TtsRequest(BaseModel):
    text: str
    language: Optional[str] = "en"  # en | hi


@router.post("/stt", summary="Upload voice command and transcribe it")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Query(default="en", description="Source language: en (English) or hi (Hindi)"),
    tenant: TenantContext = Depends(get_tenant_optional),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Transcribes uploaded audio files (WAV, MP3, M4A) to text.
    Returns the transcription and language.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file uploaded")
        
    audio_bytes = await file.read()
    
    svc = VoiceService()
    text = svc.speech_to_text(audio_bytes, language=language)
    
    return {
        "transcription": text,
        "language": language,
        "filename": file.filename
    }


@router.post("/tts", summary="Convert text to voice speech audio")
async def text_to_speech(
    payload: TtsRequest,
    tenant: TenantContext = Depends(get_tenant_optional),
    _user: UserContext = Depends(require_role("staff_viewer")),
):
    """
    Synthesizes speech from a text input string.
    Returns a streaming MP3 audio file.
    """
    if not payload.text:
        raise HTTPException(status_code=400, detail="No text content provided")
        
    svc = VoiceService()
    audio_bytes = svc.text_to_speech(payload.text, language=payload.language or "en")
    
    # Return streaming audio response
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"}
    )
