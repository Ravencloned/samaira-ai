"""
Model Context Protocol (MCP) - Core Memory Management
Provides context persistence, summarization, and retrieval for LLM conversations.

Architecture:
- Short-term memory: Rolling window of recent turns + compressed summaries
- Episodic memory: Extracted facts (user preferences, goals, constraints)  
- Semantic memory: (Future) Vector embeddings for similarity search

This module ensures the LLM has relevant context even across long conversations
and multiple sessions.
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .storage import memory_storage


@dataclass
class MemoryContext:
    """
    Assembled context to inject into LLM prompts.
    Contains all relevant memory for the current conversation.
    """
    # Session info
    session_id: str
    turn_number: int = 0
    
    # Short-term: recent conversation summary
    conversation_summary: str = ""
    recent_topics: List[str] = field(default_factory=list)
    
    # Episodic: extracted user facts
    user_facts: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    user_goals: List[str] = field(default_factory=list)
    
    # Conversation state
    current_topic: str = ""
    pending_questions: List[str] = field(default_factory=list)
    clarifications_needed: List[str] = field(default_factory=list)
    
    # Metadata
    language: str = "hinglish"
    mood: str = "neutral"
    
    def to_prompt_context(self) -> str:
        """
        Format memory context for injection into LLM system prompt.
        Returns a concise, structured context string.
        """
        parts = []
        
        # User profile facts
        if self.user_facts:
            facts_str = ", ".join(f"{k}: {v}" for k, v in self.user_facts.items() if v)
            if facts_str:
                parts.append(f"**User Profile:** {facts_str}")
        
        # User goals
        if self.user_goals:
            parts.append(f"**User Goals:** {', '.join(self.user_goals)}")
        
        # Preferences
        if self.user_preferences:
            prefs = ", ".join(f"{k}={v}" for k, v in self.user_preferences.items() if v)
            if prefs:
                parts.append(f"**Preferences:** {prefs}")
        
        # Conversation summary (most important for context)
        if self.conversation_summary:
            parts.append(f"**Previous Discussion:** {self.conversation_summary}")
        
        # Recent topics for continuity
        if self.recent_topics:
            parts.append(f"**Recent Topics:** {', '.join(self.recent_topics[-5:])}")
        
        # Current focus
        if self.current_topic:
            parts.append(f"**Current Topic:** {self.current_topic}")
        
        # Pending items
        if self.pending_questions:
            parts.append(f"**Unanswered Questions:** {'; '.join(self.pending_questions)}")
        
        if not parts:
            return ""
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class MCPMemory:
    """
    Model Context Protocol memory manager.
    Handles context assembly, summarization, and persistence.
    """
    
    # Summarization triggers
    SUMMARIZE_EVERY_N_TURNS = 6  # Summarize after every N turns
    MAX_RECENT_TURNS = 8        # Keep this many recent turns in full
    MAX_SUMMARY_LENGTH = 500    # Max chars for conversation summary
    
    # Fact extraction patterns
    FACT_PATTERNS = {
        'age': [
            r'(?:i am|main|meri age|mera age)\s*(\d{1,2})\s*(?:saal|years?|yrs?)',
            r'(\d{1,2})\s*(?:saal|years?)\s*(?:ka|ki|ke|old)',
        ],
        'name': [
            r'(?:my name is|mera naam|i am|main)\s+([A-Z][a-z]+)',
            r'(?:call me|mujhe bolo)\s+([A-Z][a-z]+)',
        ],
        'income': [
            r'(?:salary|income|kamaai|kamata|kamati)\s*(?:hai|is)?\s*(?:₹|rs\.?|rupees?)?\s*(\d[\d,]*)',
            r'(\d[\d,]*)\s*(?:₹|rs\.?|rupees?)\s*(?:per month|monthly|mahine)',
        ],
        'savings': [
            r'(?:save|bachat|bachata|bachati)\s*(?:karta|karti|kar sakta)?\s*(?:₹|rs\.?|rupees?)?\s*(\d[\d,]*)',
            r'(\d[\d,]*)\s*(?:₹|rs\.?|rupees?)\s*(?:save|bachat)',
        ],
        'family': [
            r'(?:married|shaadi|shadi|wife|husband|biwi|pati)',
            r'(\d)\s*(?:bachche|bachcha|kids?|children|beta|beti)',
        ],
        'goal': [
            r'(?:goal|target|lakshya)\s*(?:hai|is)?\s*(.+?)(?:\.|,|$)',
            r'(?:want to|chahta|chahti)\s*(.+?)(?:\.|,|$)',
        ],
        'risk': [
            r'(?:risk|jokhim)\s*(?:nahi|kam|low|high|zyada|lena)',
            r'(?:safe|secure|guaranteed|surakshit)',
        ],
    }
    
    # Goal keywords for extraction
    GOAL_KEYWORDS = {
        'retirement': ['retire', 'pension', 'old age', 'budhapa', 'retirement'],
        'education': ['education', 'padhai', 'college', 'school', 'bachche ki padhai'],
        'home': ['ghar', 'house', 'home', 'flat', 'apartment', 'property', 'makan'],
        'emergency': ['emergency', 'rainy day', 'backup', 'mushkil', 'emergency fund'],
        'wealth': ['wealth', 'ameer', 'rich', 'paisa grow', 'investment'],
        'wedding': ['shaadi', 'wedding', 'marriage'],
        'car': ['car', 'gaadi', 'vehicle'],
        'travel': ['travel', 'vacation', 'trip', 'ghoomna'],
    }
    
    def __init__(self):
        self.storage = memory_storage
        self._cache: Dict[str, MemoryContext] = {}
    
    def get_context(self, session_id: str) -> MemoryContext:
        """
        Get or create memory context for a session.
        Loads from persistent storage if available.
        """
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Initialize from storage
        context = MemoryContext(session_id=session_id)
        
        # Load session metadata
        session = self.storage.get_session(session_id)
        if session:
            context.turn_number = session.get('turn_count', 0)
            context.language = session.get('language', 'hinglish')
            if session.get('topics'):
                context.recent_topics = json.loads(session['topics']) if isinstance(session['topics'], str) else session['topics']
        
        # Load episodic facts
        facts = self.storage.get_facts(session_id)
        for fact in facts:
            fact_type = fact['fact_type']
            fact_key = fact['fact_key']
            fact_value = fact['fact_value']
            
            # Try to parse JSON values
            try:
                fact_value = json.loads(fact_value)
            except (json.JSONDecodeError, TypeError):
                pass
            
            if fact_type == 'user_info':
                context.user_facts[fact_key] = fact_value
            elif fact_type == 'preference':
                context.user_preferences[fact_key] = fact_value
            elif fact_type == 'goal':
                if fact_value not in context.user_goals:
                    context.user_goals.append(fact_value)
        
        # Load conversation summaries
        summaries = self.storage.get_summaries(session_id)
        if summaries:
            # Combine recent summaries
            recent_summaries = summaries[-3:]  # Last 3 summary chunks
            context.conversation_summary = " ".join(s['summary'] for s in recent_summaries)
            
            # Extract topics from summaries
            for s in summaries:
                if s.get('key_topics'):
                    context.recent_topics.extend(s['key_topics'])
        
        self._cache[session_id] = context
        return context
    
    def process_turn(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        detected_intent: str = None
    ) -> MemoryContext:
        """
        Process a conversation turn: extract facts, update context, trigger summarization.
        Call this after each successful exchange.
        """
        context = self.get_context(session_id)
        context.turn_number += 1
        
        # Update session in storage
        self.storage.create_or_update_session(session_id, language=context.language)
        
        # Extract facts from user message
        extracted_facts = self._extract_facts(user_message)
        for fact_type, fact_key, fact_value in extracted_facts:
            # Store in DB
            self.storage.store_fact(
                session_id=session_id,
                fact_type=fact_type,
                fact_key=fact_key,
                fact_value=fact_value,
                source_turn=context.turn_number
            )
            
            # Update context
            if fact_type == 'user_info':
                context.user_facts[fact_key] = fact_value
            elif fact_type == 'preference':
                context.user_preferences[fact_key] = fact_value
            elif fact_type == 'goal':
                if fact_value not in context.user_goals:
                    context.user_goals.append(fact_value)
        
        # Extract goals from keywords
        detected_goals = self._extract_goals(user_message)
        for goal in detected_goals:
            if goal not in context.user_goals:
                context.user_goals.append(goal)
                self.storage.store_fact(
                    session_id=session_id,
                    fact_type='goal',
                    fact_key=goal,
                    fact_value=goal,
                    source_turn=context.turn_number
                )
        
        # Update current topic from intent
        if detected_intent:
            context.current_topic = detected_intent
            if detected_intent not in context.recent_topics:
                context.recent_topics.append(detected_intent)
        
        # Check if summarization is needed
        if context.turn_number % self.SUMMARIZE_EVERY_N_TURNS == 0:
            self._summarize_recent_turns(session_id, context, user_message, ai_response)
        
        return context
    
    def _extract_facts(self, message: str) -> List[Tuple[str, str, Any]]:
        """Extract structured facts from a message."""
        facts = []
        message_lower = message.lower()
        
        # Age extraction
        for pattern in self.FACT_PATTERNS['age']:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                if 10 < age < 100:
                    facts.append(('user_info', 'age', age))
                    # Derive age group
                    if age < 25:
                        facts.append(('user_info', 'age_group', '18-25'))
                    elif age < 35:
                        facts.append(('user_info', 'age_group', '25-35'))
                    elif age < 45:
                        facts.append(('user_info', 'age_group', '35-45'))
                    elif age < 55:
                        facts.append(('user_info', 'age_group', '45-55'))
                    else:
                        facts.append(('user_info', 'age_group', '55+'))
                break
        
        # Income extraction
        for pattern in self.FACT_PATTERNS['income']:
            match = re.search(pattern, message_lower)
            if match:
                income_str = match.group(1).replace(',', '')
                try:
                    income = int(income_str)
                    if income > 1000:  # Sanity check
                        facts.append(('user_info', 'monthly_income', income))
                except ValueError:
                    pass
                break
        
        # Savings extraction
        for pattern in self.FACT_PATTERNS['savings']:
            match = re.search(pattern, message_lower)
            if match:
                savings_str = match.group(1).replace(',', '')
                try:
                    savings = int(savings_str)
                    if savings > 0:
                        facts.append(('user_info', 'monthly_savings', savings))
                except ValueError:
                    pass
                break
        
        # Family status
        if any(word in message_lower for word in ['married', 'shaadi', 'shadi', 'wife', 'husband', 'biwi', 'pati']):
            facts.append(('user_info', 'marital_status', 'married'))
        
        # Kids
        kids_match = re.search(r'(\d)\s*(?:bachche|bachcha|kids?|children|beta|beti)', message_lower)
        if kids_match:
            facts.append(('user_info', 'children', int(kids_match.group(1))))
        elif any(word in message_lower for word in ['beta', 'beti', 'bachcha', 'bachchi', 'child', 'kid']):
            facts.append(('user_info', 'has_children', True))
        
        # Risk preference
        if any(word in message_lower for word in ['risk nahi', 'no risk', 'safe', 'secure', 'guaranteed', 'kam risk', 'low risk']):
            facts.append(('preference', 'risk_appetite', 'conservative'))
        elif any(word in message_lower for word in ['high risk', 'zyada risk', 'aggressive', 'risk le sakta']):
            facts.append(('preference', 'risk_appetite', 'aggressive'))
        elif any(word in message_lower for word in ['moderate', 'balanced', 'thoda risk']):
            facts.append(('preference', 'risk_appetite', 'moderate'))
        
        return facts
    
    def _extract_goals(self, message: str) -> List[str]:
        """Extract financial goals from message."""
        goals = []
        message_lower = message.lower()
        
        for goal_name, keywords in self.GOAL_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                goals.append(goal_name)
        
        return goals
    
    def _summarize_recent_turns(
        self,
        session_id: str,
        context: MemoryContext,
        last_user_msg: str,
        last_ai_msg: str
    ):
        """
        Create a summary of recent conversation turns.
        Uses simple extractive summarization (no LLM call to avoid recursion).
        """
        # Build a simple summary from the current turn and context
        summary_parts = []
        
        # Extract key information from user message
        user_topics = []
        for goal_name, keywords in self.GOAL_KEYWORDS.items():
            if any(kw in last_user_msg.lower() for kw in keywords):
                user_topics.append(goal_name)
        
        if user_topics:
            summary_parts.append(f"User asked about {', '.join(user_topics)}")
        
        # Extract what was discussed from AI response (first sentence or key point)
        ai_first_line = last_ai_msg.split('\n')[0][:200] if last_ai_msg else ""
        if ai_first_line:
            # Clean markdown
            ai_first_line = re.sub(r'\*+', '', ai_first_line)
            ai_first_line = re.sub(r'^#+\s*', '', ai_first_line)
            summary_parts.append(f"Discussed: {ai_first_line}")
        
        # Include any extracted facts
        if context.user_facts:
            facts_summary = ", ".join(f"{k}={v}" for k, v in list(context.user_facts.items())[-3:])
            summary_parts.append(f"User info: {facts_summary}")
        
        if context.user_goals:
            summary_parts.append(f"Goals: {', '.join(context.user_goals[-3:])}")
        
        summary = ". ".join(summary_parts)
        
        # Trim if too long
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[:self.MAX_SUMMARY_LENGTH] + "..."
        
        # Store summary
        turn_start = max(1, context.turn_number - self.SUMMARIZE_EVERY_N_TURNS)
        self.storage.store_summary(
            session_id=session_id,
            turn_start=turn_start,
            turn_end=context.turn_number,
            summary=summary,
            key_topics=user_topics
        )
        
        # Update context summary
        context.conversation_summary = summary
    
    def get_prompt_context(self, session_id: str) -> str:
        """
        Get formatted context string for LLM prompt injection.
        Convenience method for easy integration.
        """
        context = self.get_context(session_id)
        return context.to_prompt_context()
    
    def clear_session_cache(self, session_id: str):
        """Clear cached context for a session."""
        if session_id in self._cache:
            del self._cache[session_id]
    
    def get_full_context(self, session_id: str) -> Dict[str, Any]:
        """Get full context as dictionary for API responses."""
        context = self.get_context(session_id)
        return context.to_dict()


# Global instance
mcp_memory = MCPMemory()
