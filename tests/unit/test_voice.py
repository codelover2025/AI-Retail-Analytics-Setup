"""Unit tests for Voice AI Service (Phase 5)."""

from __future__ import annotations

import pytest
from backend_core.services.ai.voice_service import VoiceService


def test_voice_stt_heuristics() -> None:
    """Verifies that speech-to-text fallbacks work without active Whisper key."""
    svc = VoiceService()
    audio_dummy = b"RIFF dummy audio data"
    
    # Test English heuristic fallback
    en_text = svc.speech_to_text(audio_dummy, language="en")
    assert "Mumbai" in en_text or "Compare" in en_text
    
    # Test Hindi heuristic fallback
    hi_text = svc.speech_to_text(audio_dummy, language="hi")
    assert len(hi_text) > 0


def test_voice_tts_synthesis() -> None:
    """Verifies text-to-speech audio byte generation."""
    svc = VoiceService()
    
    # Generate speech for English text
    audio_en = svc.text_to_speech("Welcome to Orzen Vision", language="en")
    assert len(audio_en) > 40  # Must be larger than simple wav header
    
    # Generate speech for Hindi text
    audio_hi = svc.text_to_speech("नमस्ते", language="hi")
    assert len(audio_hi) > 40
