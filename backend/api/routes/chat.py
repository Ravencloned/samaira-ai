"""
Chat API routes for text-based conversation.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from core.state import session_store
from core.conversation import orchestrator


router = APIRouter()


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str
    session_id: str
    intent: str
    confidence: float
    entities: dict
    is_safe: bool
    handoff_requested: bool
    calculation_data: Optional[dict] = None
    tts_text: Optional[str] = None
    suggested_questions: Optional[list] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a text message and return AI response.
    
    This is the main conversation endpoint for text-based interaction.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get or create session
    session = session_store.get_or_create(request.session_id)
    
    try:
        # Process message through orchestrator
        result = await orchestrator.process_message(
            request.message,
            session
        )
        
        # Prepare TTS-friendly text (stripped of markdown)
        from services.tts_service import tts_service
        tts_text = tts_service.prepare_text_for_speech(result.text)
        
        # Generate suggested follow-up questions
        suggested = generate_follow_up_questions(result.intent.primary_intent.value, request.message)
        
        return ChatResponse(
            response=result.text,
            session_id=session.session_id,
            intent=result.intent.primary_intent.value,
            confidence=result.intent.confidence,
            entities=result.intent.entities,
            is_safe=result.safety_check.is_safe,
            handoff_requested=result.safety_check.should_handoff,
            calculation_data=result.calculation_data,
            tts_text=tts_text,
            suggested_questions=suggested
        )
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_follow_up_questions(intent: str, user_message: str) -> list:
    """Generate contextual follow-up question suggestions."""
    
    suggestions_map = {
        "sip_query": [
            "SIP mein minimum kitna invest kar sakte hain?",
            "SIP vs Lumpsum - kya better hai?",
            "Best time to start SIP kab hai?"
        ],
        "rd_query": [
            "RD ka interest rate kitna hai abhi?",
            "RD vs FD - kaunsa better hai?",
            "Bank RD vs Post Office RD mein farak?"
        ],
        "compare_investments": [
            "Long term ke liye kya better hai?",
            "Tax savings ke liye kya options hain?",
            "Risk kam kaise karein investments mein?"
        ],
        "ppf_query": [
            "PPF account kaise kholen?",
            "PPF mein yearly limit kitni hai?",
            "PPF vs NPS - retirement ke liye kya better?"
        ],
        "goal_education": [
            "Education loan ke baare mein batao",
            "Sukanya Samriddhi Yojana kya hai?",
            "10 saal mein kitna corpus ban sakta hai?"
        ],
        "goal_wedding": [
            "Wedding fund kitna hona chahiye?",
            "Gold investment kaise karein?",
            "5 saal mein 10 lakh kaise save karein?"
        ],
        "emergency_fund": [
            "Emergency fund kahaan rakhein?",
            "Kitne months ka fund rakhna chahiye?",
            "Liquid funds vs Savings account?"
        ],
        "greeting": [
            "SIP ke baare mein batao",
            "Bachon ki education planning kaise karein?",
            "Emergency fund kaise banayein?"
        ],
        "general_query": [
            "Mutual funds safe hain kya?",
            "Tax bachane ke tarike batao",
            "Monthly budget kaise banayein?"
        ]
    }
    
    # Get suggestions based on intent, fallback to general
    suggestions = suggestions_map.get(intent, suggestions_map["general_query"])
    
    # Return 3 suggestions
    return suggestions[:3]


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response word-by-word for a ChatGPT-like experience.
    Uses Server-Sent Events (SSE) with real LLM streaming.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session = session_store.get_or_create(request.session_id)
    
    # Import LLM service for streaming
    from services.llm_service import llm_service
    from core.intent import detect_intent
    
    async def generate():
        try:
            # Send session info first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session.session_id})}\n\n"
            
            # Detect intent for suggestions
            intent_result = detect_intent(request.message)
            
            # Stream directly from LLM
            full_response = ""
            async for chunk in llm_service.chat_stream(request.message, session):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth display
            
            # Update session with the conversation
            session.add_message("user", request.message)
            session.add_message("assistant", full_response)
            
            # Send metadata at the end
            from services.tts_service import tts_service
            tts_text = tts_service.prepare_text_for_speech(full_response)
            suggested = generate_follow_up_questions(intent_result.primary_intent.value, request.message)
            
            yield f"data: {json.dumps({'type': 'done', 'intent': intent_result.primary_intent.value, 'tts_text': tts_text, 'suggested_questions': suggested})}\n\n"
            
        except Exception as e:
            print(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


class QuickCalcRequest(BaseModel):
    """Request for quick calculation."""
    calc_type: str  # "sip", "rd", "fd", "compare_sip_rd", "goal_corpus"
    amount: float
    years: int
    rate: Optional[float] = None
    target_amount: Optional[float] = None  # For goal corpus


@router.post("/calculate")
async def quick_calculate(request: QuickCalcRequest):
    """
    Perform quick financial calculations without LLM.
    Deterministic calculations only.
    """
    from financial.calculators import (
        calculate_sip, 
        calculate_rd, 
        calculate_fd,
        compare_sip_vs_rd,
        calculate_goal_corpus
    )
    
    try:
        if request.calc_type == "sip":
            result = calculate_sip(
                request.amount, 
                request.years,
                request.rate or 12.0
            )
            return {
                "success": True,
                "type": "sip",
                "data": result.to_dict(),
                "summary": result.format_summary_hinglish()
            }
        
        elif request.calc_type == "rd":
            result = calculate_rd(
                request.amount,
                request.years,
                request.rate or 6.5
            )
            return {
                "success": True,
                "type": "rd",
                "data": result.to_dict(),
                "summary": result.format_summary_hinglish()
            }
        
        elif request.calc_type == "fd":
            result = calculate_fd(
                request.amount,
                request.years,
                request.rate or 7.0
            )
            return {
                "success": True,
                "type": "fd",
                "data": result.to_dict(),
                "summary": result.format_summary_hinglish()
            }
        
        elif request.calc_type == "compare_sip_rd":
            result = compare_sip_vs_rd(request.amount, request.years)
            return {
                "success": True,
                "type": "comparison",
                "data": result,
                "summary": result["summary_hinglish"]
            }
        
        elif request.calc_type == "goal_corpus":
            if not request.target_amount:
                raise HTTPException(
                    status_code=400, 
                    detail="target_amount required for goal_corpus calculation"
                )
            result = calculate_goal_corpus(
                request.target_amount,
                request.years,
                request.rate or 12.0
            )
            return {
                "success": True,
                "type": "goal_corpus",
                "data": result,
                "summary": result["summary_hinglish"]
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown calculation type: {request.calc_type}"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemes/{scheme_code}")
async def get_scheme_info(scheme_code: str):
    """Get information about a government scheme."""
    from financial.schemes import get_scheme_info, get_scheme_explanation_hinglish
    
    scheme = get_scheme_info(scheme_code)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme not found: {scheme_code}")
    
    return {
        "code": scheme.code,
        "name": scheme.name,
        "name_hindi": scheme.name_hindi,
        "current_rate": scheme.current_rate,
        "min_investment": scheme.min_investment,
        "max_investment": scheme.max_investment,
        "lock_in_years": scheme.lock_in_years,
        "tax_benefit": scheme.tax_benefit,
        "risk_level": scheme.risk_level,
        "suitable_for": scheme.suitable_for,
        "key_features": scheme.key_features,
        "explanation_hinglish": get_scheme_explanation_hinglish(scheme_code)
    }


class TTSRequest(BaseModel):
    """Request for text-to-speech."""
    text: str
    voice: Optional[str] = None


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs.
    Returns base64 encoded audio.
    """
    from services.elevenlabs_tts import elevenlabs_tts
    from config.settings import settings
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Check if ElevenLabs is available
    if settings.TTS_PROVIDER == "elevenlabs" and elevenlabs_tts.is_available():
        audio_base64 = await elevenlabs_tts.synthesize_base64(request.text, request.voice)
        if audio_base64:
            return {
                "success": True,
                "audio": audio_base64,
                "format": "mp3",
                "provider": "elevenlabs"
            }
    
    # Fallback to browser TTS
    return {
        "success": False,
        "audio": None,
        "format": None,
        "provider": "browser",
        "message": "Use browser TTS as fallback"
    }


@router.get("/tts/status")
async def tts_status():
    """Check TTS provider status."""
    from services.elevenlabs_tts import elevenlabs_tts
    from config.settings import settings
    
    return {
        "provider": settings.TTS_PROVIDER,
        "elevenlabs_available": elevenlabs_tts.is_available(),
        "fallback": "browser"
    }


@router.get("/schemes")
async def list_schemes():
    """List all available government schemes."""
    from financial.schemes import get_all_schemes
    
    schemes = get_all_schemes()
    return {
        "schemes": [
            {
                "code": s.code,
                "name": s.name,
                "name_hindi": s.name_hindi,
                "current_rate": s.current_rate,
                "risk_level": s.risk_level
            }
            for s in schemes
        ]
    }
