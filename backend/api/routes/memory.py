"""
Memory API routes for inspecting and managing MCP memory.
Useful for debugging and understanding what the model remembers.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


class MemoryFact(BaseModel):
    """A single fact stored in memory."""
    id: int
    fact_type: str
    content: str
    confidence: float
    extracted_at: str
    source_turn: int


class MemoryContext(BaseModel):
    """Full memory context for a session."""
    session_id: str
    turn_number: int
    conversation_summary: Optional[str]
    user_facts: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    user_goals: List[str]
    current_topic: Optional[str]
    language: str
    mood: str


class MemorySummary(BaseModel):
    """Summary of memory state."""
    session_id: str
    total_facts: int
    total_turns: int
    has_summary: bool
    last_updated: Optional[str]


@router.get("/memory/{session_id}", response_model=MemoryContext)
async def get_memory_context(session_id: str):
    """
    Get the full memory context for a session.
    Shows what the model "remembers" about the conversation.
    """
    try:
        from memory.mcp import mcp_memory
        
        context = mcp_memory.get_context(session_id)
        
        return MemoryContext(
            session_id=context.session_id,
            turn_number=context.turn_number,
            conversation_summary=context.conversation_summary,
            user_facts=context.user_facts,
            user_preferences=context.user_preferences,
            user_goals=context.user_goals,
            current_topic=context.current_topic,
            language=context.language,
            mood=context.mood
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP memory not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{session_id}/facts", response_model=List[MemoryFact])
async def get_memory_facts(session_id: str, fact_type: Optional[str] = None):
    """
    Get all facts stored for a session.
    Optionally filter by fact type (name, age, income, goal, etc.).
    """
    try:
        from memory.storage import memory_storage
        
        facts = memory_storage.get_facts(session_id, fact_type)
        
        return [
            MemoryFact(
                id=f['id'],
                fact_type=f['fact_type'],
                content=f['content'],
                confidence=f['confidence'],
                extracted_at=f['extracted_at'],
                source_turn=f['source_turn']
            )
            for f in facts
        ]
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP memory not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{session_id}/summary", response_model=MemorySummary)
async def get_memory_summary(session_id: str):
    """
    Get a quick summary of memory state for a session.
    """
    try:
        from memory.storage import memory_storage
        from memory.mcp import mcp_memory
        
        context = mcp_memory.get_context(session_id)
        facts = memory_storage.get_facts(session_id)
        
        return MemorySummary(
            session_id=session_id,
            total_facts=len(facts),
            total_turns=context.turn_number,
            has_summary=bool(context.conversation_summary),
            last_updated=facts[0]['extracted_at'] if facts else None
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP memory not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """
    Clear all memory for a session.
    Useful for starting fresh or privacy.
    """
    try:
        from memory.storage import memory_storage
        
        memory_storage.clear_session(session_id)
        
        return {"status": "success", "message": f"Memory cleared for session {session_id}"}
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP memory not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/debug/all")
async def debug_all_memory():
    """
    Debug endpoint to see all sessions and their memory.
    Only for development purposes.
    """
    try:
        from memory.storage import memory_storage
        
        conn = memory_storage._get_connection()
        cursor = conn.cursor()
        
        # Get all sessions
        cursor.execute("SELECT * FROM sessions ORDER BY last_activity DESC LIMIT 10")
        sessions = cursor.fetchall()
        
        result = []
        for session in sessions:
            session_id = session['session_id']
            facts = memory_storage.get_facts(session_id)
            summaries = memory_storage.get_summaries(session_id)
            
            result.append({
                'session_id': session_id,
                'turn_count': session['turn_count'],
                'last_activity': session['last_activity'],
                'facts_count': len(facts),
                'summaries_count': len(summaries),
                'recent_facts': facts[:5] if facts else []
            })
        
        return {
            'total_sessions': len(sessions),
            'sessions': result
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP memory not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
