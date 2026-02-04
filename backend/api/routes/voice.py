"""
Voice API routes for speech-to-text and text-to-speech.
Includes WebSocket endpoint for real-time voice conversation.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import json
import asyncio
import numpy as np
import base64
import io

from core.state import session_store
from core.conversation import orchestrator
from services.whisper_asr import whisper_asr
from services.tts_service import tts_service
from config.settings import settings


router = APIRouter()


class VoiceResponse(BaseModel):
    """Response for voice endpoints."""
    transcript: str  # What user said (as-spoken, in their language)
    response: str
    session_id: str
    tts_text: str
    tts_config: dict
    intent: str
    confidence: float
    is_safe: bool
    handoff_requested: bool
    detected_language: str = "hi"  # Language detected by Whisper


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
        
        # Transcribe using Whisper ASR
        result = whisper_asr.transcribe_bytes(audio_bytes, ext)
        
        return {
            "success": True,
            "transcript": result["text"],
            "language": result["language"],
            "segments": result.get("segments", [])
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
    
    # Standard unclear audio response
    UNCLEAR_RESPONSE = "Maaf kijiye, aapki awaaz clearly nahi sunayi di. Kya aap phir se bol sakte hain?"
    
    try:
        # Step 1: Transcribe audio (as-spoken, no translation)
        audio_bytes = await audio.read()
        print(f"[Voice] Received audio: {len(audio_bytes)} bytes, format: {ext}")
        
        transcription = whisper_asr.transcribe_bytes(audio_bytes, ext)
        transcript = transcription["text"]
        detected_language = transcription.get("language", "hi")
        print(f"[Voice] Transcription result: '{transcript}'")
        
        # Check for unclear audio (empty or hallucination sentinel)
        is_unclear = (
            not transcript.strip() or 
            "[Audio unclear" in transcript or 
            "[Unclear audio" in transcript
        )
        
        if is_unclear:
            return VoiceResponse(
                transcript="",
                response=UNCLEAR_RESPONSE,
                session_id=session_id or "",
                tts_text=UNCLEAR_RESPONSE,
                tts_config=tts_service.get_tts_config(),
                intent="unclear",
                confidence=0.0,
                is_safe=True,
                handoff_requested=False,
                detected_language=detected_language
            )
        
        # Step 2: Get or create session
        session = session_store.get_or_create(session_id)
        
        # Step 3: Process through orchestrator
        result = await orchestrator.process_message(transcript, session)
        
        # Step 4: Prepare TTS text
        tts_text = tts_service.prepare_text_for_speech(result.text)
        
        return VoiceResponse(
            transcript=transcript,  # Original as-spoken text (Hindi/English as user said)
            response=result.text,
            session_id=session.session_id,
            tts_text=tts_text,
            tts_config=tts_service.get_tts_config(),
            intent=result.intent.primary_intent.value,
            confidence=result.intent.confidence,
            is_safe=result.safety_check.is_safe,
            handoff_requested=result.safety_check.should_handoff,
            detected_language=detected_language
        )
    
    except Exception as e:
        import traceback
        print(f"Voice chat error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/tts-config")
async def get_tts_config():
    """Get TTS configuration for the frontend."""
    try:
        return tts_service.get_provider_info()
    except AttributeError:
        # Fallback for old TTS service
        return tts_service.get_tts_config()


class TTSRequest(BaseModel):
    """Request body for TTS synthesis."""
    text: str
    voice: Optional[str] = None
    provider: Optional[str] = None  # edge (FREE), azure, elevenlabs, browser


@router.post("/voice/tts")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text.
    
    Providers (in order of quality):
    1. Edge TTS - FREE! Same quality as Azure, no API key needed
    2. Azure Neural TTS - requires API key
    3. ElevenLabs - requires API key  
    4. Browser - fallback (client-side)
    
    Returns:
        audio: base64 encoded MP3 audio
        provider: which provider was used
        fallback: true if browser TTS should be used (no audio)
    """
    from services.tts_service import tts_service, TTSProvider
    
    # Initialize if needed
    if not tts_service._initialized:
        tts_service.initialize()
    
    # Clean text
    text = tts_service.prepare_text_for_speech(request.text)
    
    # Convert provider string to enum if provided
    provider = None
    if request.provider:
        try:
            provider = TTSProvider(request.provider)
        except ValueError:
            pass
    
    # Try to synthesize
    result = await tts_service.synthesize(text, provider, request.voice)
    
    if result:
        return {
            "success": True,
            "audio": result['audio'],
            "provider": result['provider'],
            "voice": result['voice'],
            "format": result['format'],
            "fallback": False
        }
    else:
        # Signal to use browser TTS
        return {
            "success": True,
            "audio": None,
            "provider": "browser",
            "fallback": True,
            "text": text  # Pre-cleaned text for browser TTS
        }


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


# ============================================================================
# REAL-TIME VOICE WebSocket Endpoint (Near-Duplex Conversation)
# ============================================================================

@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Real-time voice conversation over WebSocket.
    
    Client → Server: PCM audio chunks (30ms frames)
    Server → Client: VAD state, partial STT, final STT, LLM tokens, TTS audio chunks
    
    Flow:
    1. Client connects, sends `start` with session_id
    2. Client streams `audio_chunk` (base64 PCM16, 16kHz mono)
    3. Server accumulates, runs VAD, detects end-of-utterance
    4. On silence detected, server finalizes STT → `stt_final`
    5. Server streams LLM response → `llm_chunk`
    6. Server streams TTS chunks → `tts_chunk` (base64 MP3)
    7. After turn complete → `turn_done`, ready for next utterance
    """
    await websocket.accept()
    
    # State for this connection
    session = None
    audio_buffer = []  # List of numpy arrays
    vad_service = None
    faster_asr = None
    is_recording = False
    silence_frames = 0
    speech_detected = False
    SILENCE_THRESHOLD = 20  # ~600ms of silence to end utterance (20 frames * 30ms)
    
    try:
        # Initialize services
        if settings.USE_FASTER_WHISPER:
            try:
                from services.faster_whisper_asr import faster_whisper_asr
                faster_asr = faster_whisper_asr
                if not faster_asr._initialized:
                    faster_asr.initialize()
            except:
                pass
        
        if settings.VAD_ENABLED:
            try:
                from services.vad import vad_service as vad
                vad_service = vad
                if not vad_service._initialized:
                    vad_service.initialize()
            except:
                pass
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "start":
                # Initialize session
                session_id = message.get("session_id")
                session = session_store.get_or_create(session_id)
                is_recording = True
                audio_buffer = []
                silence_frames = 0
                speech_detected = False
                
                await websocket.send_text(json.dumps({
                    "type": "session",
                    "session_id": session.session_id
                }))
                
            elif msg_type == "audio_chunk":
                if not is_recording or session is None:
                    continue
                
                # Decode PCM16 audio chunk (base64 → bytes → numpy)
                audio_b64 = message.get("data")
                audio_bytes = base64.b64decode(audio_b64)
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                
                # Run VAD if available
                is_speech = True
                if vad_service:
                    try:
                        is_speech = vad_service.is_speech(audio_bytes, sample_rate=16000)
                    except:
                        is_speech = True
                
                # Track speech/silence
                if is_speech:
                    speech_detected = True
                    silence_frames = 0
                    audio_buffer.append(audio_array)
                    
                    # Send VAD state
                    await websocket.send_text(json.dumps({
                        "type": "vad_state",
                        "state": "speech"
                    }))
                else:
                    if speech_detected:
                        silence_frames += 1
                        audio_buffer.append(audio_array)  # Keep silence between speech
                        
                        await websocket.send_text(json.dumps({
                            "type": "vad_state",
                            "state": "silence",
                            "frames": silence_frames
                        }))
                        
                        # Check if utterance complete
                        if silence_frames >= SILENCE_THRESHOLD:
                            # End of utterance detected
                            is_recording = False
                            
                            # Transcribe accumulated audio
                            if len(audio_buffer) > 0:
                                combined_audio = np.concatenate(audio_buffer)
                                
                                # Convert int16 to float32 for Whisper
                                audio_float = combined_audio.astype(np.float32) / 32768.0
                                
                                # Transcribe
                                transcript_text = ""
                                if faster_asr:
                                    try:
                                        result = faster_asr.transcribe_numpy(audio_float, sample_rate=16000)
                                        transcript_text = result.get("text", "")
                                    except Exception as e:
                                        print(f"[ERROR] Faster-Whisper transcription failed: {e}")
                                else:
                                    # Fallback to regular Whisper
                                    try:
                                        result = whisper_asr.transcribe_numpy(audio_float, sample_rate=16000)
                                        transcript_text = result.get("text", "")
                                    except Exception as e:
                                        print(f"[ERROR] Whisper transcription failed: {e}")
                                
                                # Send final transcript
                                await websocket.send_text(json.dumps({
                                    "type": "stt_final",
                                    "text": transcript_text
                                }))
                                
                                # Check for unclear audio
                                is_unclear = (
                                    not transcript_text.strip() or 
                                    "[Audio unclear" in transcript_text
                                )
                                
                                if is_unclear:
                                    # Skip LLM, send polite retry message
                                    retry_msg = "Maaf kijiye, aapki awaaz clearly nahi sunayi. Phir se boliye?"
                                    await websocket.send_text(json.dumps({
                                        "type": "llm_chunk",
                                        "text": retry_msg
                                    }))
                                    
                                    # TTS for retry message
                                    try:
                                        tts_result = await tts_service.synthesize(retry_msg)
                                        if tts_result and tts_result.get('audio'):
                                            await websocket.send_text(json.dumps({
                                                "type": "tts_chunk",
                                                "audio": tts_result['audio'],
                                                "format": tts_result.get('format', 'mp3')
                                            }))
                                    except:
                                        pass
                                    
                                    await websocket.send_text(json.dumps({"type": "turn_done"}))
                                    
                                    # Reset for next turn
                                    audio_buffer = []
                                    silence_frames = 0
                                    speech_detected = False
                                    is_recording = True
                                    continue
                                
                                # Add to session history
                                session.add_message("user", transcript_text)
                                session_store.update_session(session)
                                
                                # Process through LLM (streaming)
                                from services.llm_service import llm_service
                                from core.postprocess import clean_response
                                full_response = ""
                                
                                async for chunk in llm_service.chat_stream(transcript_text, session):
                                    full_response += chunk
                                    await websocket.send_text(json.dumps({
                                        "type": "llm_chunk",
                                        "text": chunk
                                    }))
                                
                                # Clean response (strip any re-introductions) for TTS
                                turn_number = len(session.get_conversation_history()) // 2 + 1
                                cleaned_response = clean_response(full_response, turn_number=turn_number, for_voice=True)
                                
                                # Add assistant response to history (use cleaned version)
                                session.add_message("assistant", cleaned_response)
                                session_store.update_session(session)
                                
                                # Stream TTS audio (use cleaned response)
                                tts_text = tts_service.prepare_text_for_speech(cleaned_response)
                                
                                # Split into sentences for progressive playback
                                import re
                                sentences = re.split(r'([.!?]+\s+)', tts_text)
                                current_sentence = ""
                                
                                for part in sentences:
                                    current_sentence += part
                                    if re.match(r'[.!?]+\s*$', part) and len(current_sentence.strip()) > 10:
                                        # Synthesize this sentence
                                        try:
                                            tts_result = await tts_service.synthesize(current_sentence.strip())
                                            if tts_result and tts_result.get('audio'):
                                                await websocket.send_text(json.dumps({
                                                    "type": "tts_chunk",
                                                    "audio": tts_result['audio'],  # Already base64
                                                    "format": tts_result.get('format', 'mp3')
                                                }))
                                        except Exception as e:
                                            print(f"[WARNING] TTS chunk failed: {e}")
                                        
                                        current_sentence = ""
                                        await asyncio.sleep(0.1)  # Brief pause between chunks
                                
                                # Synthesize any remaining text
                                if current_sentence.strip():
                                    try:
                                        tts_result = await tts_service.synthesize(current_sentence.strip())
                                        if tts_result and tts_result.get('audio'):
                                            await websocket.send_text(json.dumps({
                                                "type": "tts_chunk",
                                                "audio": tts_result['audio'],
                                                "format": tts_result.get('format', 'mp3')
                                            }))
                                    except:
                                        pass
                                
                                # Turn complete
                                await websocket.send_text(json.dumps({
                                    "type": "turn_done"
                                }))
                            
                            # Reset for next utterance
                            audio_buffer = []
                            silence_frames = 0
                            speech_detected = False
                            is_recording = True  # Ready for next turn
            
            elif msg_type == "stop":
                # Client requested stop
                is_recording = False
                audio_buffer = []
                
            elif msg_type == "ping":
                # Keep-alive
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        print("[INFO] WebSocket disconnected")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass
    finally:
        # Cleanup
        try:
            await websocket.close()
        except:
            pass

