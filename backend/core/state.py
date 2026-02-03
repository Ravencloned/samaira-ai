"""
Session state model for SamairaAI conversations.
Tracks user context, goals, preferences, and conversation history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum
import uuid


class GoalType(str, Enum):
    """Supported financial goal types."""
    CHILD_EDUCATION = "child_education"
    WEDDING = "wedding"
    HOME_DOWNPAYMENT = "home_downpayment"
    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    GENERAL_WEALTH = "general_wealth"
    OTHER = "other"


class RiskPreference(str, Enum):
    """User risk tolerance levels."""
    SAFE = "safe"           # FD, PPF, RD only
    MODERATE = "moderate"   # Mix of debt and equity
    GROWTH = "growth"       # Equity-heavy


class ConversationPhase(str, Enum):
    """Current phase in the conversation flow."""
    GREETING = "greeting"
    GOAL_DISCOVERY = "goal_discovery"
    CLARIFYING = "clarifying"
    EDUCATING = "educating"
    CALCULATING = "calculating"
    HANDOFF = "handoff"
    COMPLETED = "completed"


@dataclass
class Message:
    """Single message in conversation history."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UserGoal:
    """Structured representation of a user's financial goal."""
    goal_type: GoalType
    target_amount: Optional[float] = None       # Target corpus in INR
    timeline_years: Optional[int] = None        # Years to achieve goal
    monthly_capacity: Optional[float] = None    # How much user can invest monthly
    beneficiary: Optional[str] = None           # e.g., "son", "daughter"
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "goal_type": self.goal_type.value,
            "target_amount": self.target_amount,
            "timeline_years": self.timeline_years,
            "monthly_capacity": self.monthly_capacity,
            "beneficiary": self.beneficiary,
            "notes": self.notes
        }


@dataclass 
class SessionState:
    """
    Complete session state for a user conversation.
    Maintains context across multiple turns.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    # User identification
    user_name: Optional[str] = None
    
    # Current conversation context
    current_phase: ConversationPhase = ConversationPhase.GREETING
    current_goal: Optional[UserGoal] = None
    
    # User preferences (learned during conversation)
    risk_preference: Optional[RiskPreference] = None
    preferred_language: str = "hinglish"  # hinglish, hindi, english
    
    # Conversation tracking
    conversation_history: list[Message] = field(default_factory=list)
    detected_intents: list[str] = field(default_factory=list)
    topics_discussed: list[str] = field(default_factory=list)
    
    # Safety flags
    handoff_requested: bool = False
    handoff_reason: Optional[str] = None
    advisory_boundary_hit: bool = False
    disclaimers_shown: int = 0
    
    def add_message(self, role: Literal["user", "assistant", "system"], content: str):
        """Add a message to conversation history."""
        self.conversation_history.append(Message(role=role, content=content))
        self.last_active = datetime.now()
    
    def get_recent_history(self, n: int = 10) -> list[dict]:
        """Get last n messages for context."""
        recent = self.conversation_history[-n:] if len(self.conversation_history) > n else self.conversation_history
        return [msg.to_dict() for msg in recent]
    
    def get_gemini_history(self, n: int = 10) -> list[dict]:
        """
        Format history for Gemini API (role: user/model format).
        Returns the last n message pairs for context continuity.
        """
        history = []
        messages = self.conversation_history[-n*2:] if len(self.conversation_history) > n*2 else self.conversation_history
        
        for msg in messages:
            role = "model" if msg.role == "assistant" else msg.role
            if role in ["user", "model"]:  # Skip system messages
                history.append({
                    "role": role,
                    "parts": [msg.content]
                })
        
        return history
    
    def get_conversation_summary(self) -> str:
        """
        Generate a brief summary of the conversation for context.
        Useful for maintaining coherence in long conversations.
        """
        summary_parts = []
        
        if self.user_name:
            summary_parts.append(f"User's name: {self.user_name}")
        
        if self.current_goal:
            summary_parts.append(f"Goal: {self.current_goal.goal_type.value}")
            if self.current_goal.target_amount:
                summary_parts.append(f"Target: ₹{self.current_goal.target_amount:,.0f}")
            if self.current_goal.timeline_years:
                summary_parts.append(f"Timeline: {self.current_goal.timeline_years} years")
        
        if self.risk_preference:
            summary_parts.append(f"Risk preference: {self.risk_preference.value}")
        
        if self.topics_discussed:
            summary_parts.append(f"Topics discussed: {', '.join(self.topics_discussed[-5:])}")
        
        return " | ".join(summary_parts) if summary_parts else ""
    
    def set_goal(self, goal_type: GoalType, **kwargs):
        """Set or update the current financial goal."""
        self.current_goal = UserGoal(goal_type=goal_type, **kwargs)
        self.current_phase = ConversationPhase.GOAL_DISCOVERY
    
    def trigger_handoff(self, reason: str):
        """Mark session for human handoff."""
        self.handoff_requested = True
        self.handoff_reason = reason
        self.current_phase = ConversationPhase.HANDOFF
    
    def mark_advisory_boundary(self):
        """Flag that user hit an advisory boundary."""
        self.advisory_boundary_hit = True
    
    def to_dict(self) -> dict:
        """Serialize state to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "user_name": self.user_name,
            "current_phase": self.current_phase.value,
            "current_goal": self.current_goal.to_dict() if self.current_goal else None,
            "risk_preference": self.risk_preference.value if self.risk_preference else None,
            "preferred_language": self.preferred_language,
            "message_count": len(self.conversation_history),
            "detected_intents": self.detected_intents,
            "topics_discussed": self.topics_discussed,
            "handoff_requested": self.handoff_requested,
            "handoff_reason": self.handoff_reason,
            "advisory_boundary_hit": self.advisory_boundary_hit,
        }


class SessionStore:
    """
    In-memory session store for the prototype.
    Production would use Redis or similar.
    """
    
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
    
    def create_session(self) -> SessionState:
        """Create a new session."""
        session = SessionState()
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)
    
    def get_or_create(self, session_id: Optional[str] = None) -> SessionState:
        """Get existing session or create new one."""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_active = datetime.now()
            return session
        return self.create_session()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired(self, timeout_minutes: int = 30):
        """Remove sessions older than timeout."""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if (now - session.last_active).total_seconds() > timeout_minutes * 60
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# Global session store instance
session_store = SessionStore()
