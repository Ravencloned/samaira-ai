"""
Voice API routes for speech-to-text and text-to-speech.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from core.state import session_store
from core.conversation import orchestrator
from services.whisper_asr import whisper_asr
from services.tts_service import tts_service


router = APIRouter()


class VoiceResponse(BaseModel):
    """Response for voice endpoints."""
    transcript: str
    response: str
    session_id: str
    tts_text: str
    tts_config: dict
    intent: str
    confidence: float
    is_safe: bool
    handoff_requested: bool


@router.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Transcribe audio to text using Whisper.
    Returns only the transcript without processing through LLM.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    # Get file extension
    ext = audio.filename.split(".")[-1] if "." in audio.filename else "wav"
    
    try:
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Transcribe
        result = whisper_asr.transcribe_bytes(audio_bytes, ext)
        
        return {
            "success": True,
            "transcript": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }
    
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/chat", response_model=VoiceResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Full voice-to-voice conversation flow:
    1. Transcribe audio to text (Whisper)
    2. Process through conversation orchestrator (Gemini)
    3. Return response with TTS-ready text
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    ext = audio.filename.split(".")[-1] if "." in audio.filename else "wav"
    
    try:
        # Step 1: Transcribe audio
        audio_bytes = await audio.read()
        transcription = whisper_asr.transcribe_bytes(audio_bytes, ext)
        transcript = transcription["text"]
        
        if not transcript.strip():
            return VoiceResponse(
                transcript="",
                response="Maaf kijiye, aapki awaaz clearly nahi sunayi di. Kya aap phir se bol sakte hain?",
                session_id=session_id or "",
                tts_text="Maaf kijiye, aapki awaaz clearly nahi sunayi di. Kya aap phir se bol sakte hain?",
                tts_config=tts_service.get_tts_config(),
                intent="unclear",
                confidence=0.0,
                is_safe=True,
                handoff_requested=False
            )
        
        # Step 2: Get or create session
        session = session_store.get_or_create(session_id)
        
        # Step 3: Process through orchestrator
        result = await orchestrator.process_message(transcript, session)
        
        # Step 4: Prepare TTS text
        tts_text = tts_service.prepare_text_for_speech(result.text)
        
        return VoiceResponse(
            transcript=transcript,
            response=result.text,
            session_id=session.session_id,
            tts_text=tts_text,
            tts_config=tts_service.get_tts_config(),
            intent=result.intent.primary_intent.value,
            confidence=result.intent.confidence,
            is_safe=result.safety_check.is_safe,
            handoff_requested=result.safety_check.should_handoff
        )
    
    except Exception as e:
        print(f"Voice chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/tts-config")
async def get_tts_config():
    """Get TTS configuration for the frontend."""
    return tts_service.get_tts_config()


@router.post("/voice/prepare-tts")
async def prepare_tts(text: str):
    """
    Prepare text for TTS by cleaning formatting.
    Also returns chunked text for smoother playback.
    """
    cleaned = tts_service.prepare_text_for_speech(text)
    chunks = tts_service.split_for_chunked_speech(cleaned)
    
    return {
        "original": text,
        "cleaned": cleaned,
        "chunks": chunks,
        "config": tts_service.get_tts_config()
    }
