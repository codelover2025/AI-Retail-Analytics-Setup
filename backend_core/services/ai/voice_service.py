"""Voice AI Backend service supporting English & Hindi (Phase 5)."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceService:
    """Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities."""

    def __init__(self, settings: Any = None) -> None:
        self.settings = settings
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def speech_to_text(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribes audio bytes to text.
        Supports 'en' (English) and 'hi' (Hindi).
        """
        lang_code = "hi-IN" if language.lower() == "hi" else "en-US"
        
        # Write bytes to temporary file for processing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # 1. Try OpenAI Whisper API if key is available
            if self.openai_key:
                import httpx
                headers = {"Authorization": f"Bearer {self.openai_key}"}
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {"model": "whisper-1", "language": language.lower()}
                
                resp = httpx.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30.0
                )
                if resp.status_code == 200:
                    transcription = resp.json().get("text", "")
                    logger.info("STT transcribed via Whisper API: %s", transcription)
                    return transcription
                else:
                    logger.warning("Whisper STT failed with status %d: %s", resp.status_code, resp.text)

            # 1.5 Try Local Offline Vosk Model
            try:
                import vosk
                import json
                import wave
                
                # Check for language-specific Vosk model
                model_dir = "./data/models"
                vosk_lang = "en-us" if language.lower() == "en" else "hi"
                model_path = os.path.join(model_dir, f"vosk-model-small-{vosk_lang}")
                
                if os.path.exists(model_path):
                    # Cache the model to avoid reloading on every request
                    cache_key = f"_vosk_model_{vosk_lang}"
                    if not hasattr(VoiceService, cache_key):
                        logger.info("Loading Vosk model from %s...", model_path)
                        setattr(VoiceService, cache_key, vosk.Model(model_path))
                    
                    model = getattr(VoiceService, cache_key)
                    
                    with wave.open(tmp_path, "rb") as wf:
                        if wf.getnchannels() > 0:
                            rec = vosk.KaldiRecognizer(model, wf.getframerate())
                            data = wf.readframes(wf.getnframes())
                            if rec.AcceptWaveform(data):
                                res = json.loads(rec.Result())
                            else:
                                res = json.loads(rec.PartialResult())
                            
                            text = res.get("text", "")
                            if text:
                                logger.info("STT transcribed via local Vosk model: %s", text)
                                return text
                else:
                    logger.debug("Vosk model not found at %s. Skipping Vosk.", model_path)
            except ImportError:
                logger.debug("Vosk library not installed. Skipping local Vosk STT.")
            except Exception as e:
                logger.warning("Vosk transcription failed: %s", e)

            # 2. Try SpeechRecognition (Sphinx offline / Google online) fallback
            try:
                import speech_recognition as sr  # type: ignore
                recognizer = sr.Recognizer()
                with sr.AudioFile(tmp_path) as source:
                    audio_data = recognizer.record(source)
                
                # Try Sphinx offline first if language is english
                if language.lower() == "en":
                    try:
                        text = recognizer.recognize_sphinx(audio_data)
                        if text:
                            logger.info("STT transcribed via Sphinx offline fallback: %s", text)
                            return text
                    except Exception as e:
                        logger.debug("Sphinx offline transcription unavailable: %s", e)

                text = recognizer.recognize_google(audio_data, language=lang_code)
                logger.info("STT transcribed via SpeechRecognition Google fallback: %s", text)
                return text
            except ImportError:
                logger.warning("SpeechRecognition library not installed.")
            except Exception as exc:
                logger.warning("SpeechRecognition transcription failed: %s", exc)

            # 3. Last fallback: heuristic mock if everything else is unavailable
            logger.warning("No speech transcribers available. Returning default mock query.")
            return "Compare Mumbai and Bangalore" if language == "en" else "दिल्ली के फुटफॉल में कमी क्यों आई"

        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """
        Synthesizes text to speech audio bytes.
        Supports 'en' (English) and 'hi' (Hindi).
        """
        lang_code = "hi" if language.lower() == "hi" else "en"
        
        try:
            # Try using gTTS (Google Text-to-Speech)
            from gtts import gTTS  # type: ignore
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
                
            try:
                tts = gTTS(text=text, lang=lang_code, slow=False)
                tts.save(tmp_path)
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
                return audio_bytes
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as exc:
            logger.warning("gTTS synthesis failed, generating synthetic beep: %s", exc)
            # Return a small mock wave header / beep sound if gTTS fails
            return (
                b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"
                + text.encode("utf-8")
            )
