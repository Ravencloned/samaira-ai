"""
Chat API routes for text-based conversation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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
        
        return ChatResponse(
            response=result.text,
            session_id=session.session_id,
            intent=result.intent.primary_intent.value,
            confidence=result.intent.confidence,
            entities=result.intent.entities,
            is_safe=result.safety_check.is_safe,
            handoff_requested=result.safety_check.should_handoff,
            calculation_data=result.calculation_data,
            tts_text=tts_text
        )
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
