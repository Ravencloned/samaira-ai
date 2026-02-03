"""
Session management API routes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.state import session_store, RiskPreference, GoalType


router = APIRouter()


class UpdateSessionRequest(BaseModel):
    """Request to update session data."""
    user_name: Optional[str] = None
    risk_preference: Optional[str] = None
    preferred_language: Optional[str] = None


@router.post("/session/create")
async def create_session():
    """Create a new conversation session."""
    session = session_store.create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "message": "Session created successfully"
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    session = session_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20):
    """Get conversation history for a session."""
    session = session_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "message_count": len(session.conversation_history),
        "messages": session.get_recent_history(limit)
    }


@router.patch("/session/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update session data (name, preferences, etc.)."""
    session = session_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if request.user_name:
        session.user_name = request.user_name
    
    if request.risk_preference:
        try:
            session.risk_preference = RiskPreference(request.risk_preference)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid risk_preference. Must be one of: {[r.value for r in RiskPreference]}"
            )
    
    if request.preferred_language:
        session.preferred_language = request.preferred_language
    
    return {
        "message": "Session updated",
        "session": session.to_dict()
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    deleted = session_store.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted", "session_id": session_id}


@router.post("/session/cleanup")
async def cleanup_sessions(timeout_minutes: int = 30):
    """Clean up expired sessions."""
    count = session_store.cleanup_expired(timeout_minutes)
    return {
        "message": f"Cleaned up {count} expired sessions",
        "timeout_minutes": timeout_minutes
    }


@router.post("/session/{session_id}/goal")
async def set_session_goal(
    session_id: str,
    goal_type: str,
    target_amount: Optional[float] = None,
    timeline_years: Optional[int] = None
):
    """Set a financial goal for the session."""
    session = session_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        goal_type_enum = GoalType(goal_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid goal_type. Must be one of: {[g.value for g in GoalType]}"
        )
    
    session.set_goal(
        goal_type=goal_type_enum,
        target_amount=target_amount,
        timeline_years=timeline_years
    )
    
    return {
        "message": "Goal set successfully",
        "goal": session.current_goal.to_dict() if session.current_goal else None
    }
