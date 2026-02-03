"""
Groq API client for SamairaAI.
Uses Llama 3 via Groq's free API for fast, high-quality responses.
Groq offers 30 requests/min free with excellent quality.
"""

import httpx
import time
from typing import Optional, AsyncGenerator
from pathlib import Path
from collections import deque

from config.settings import settings


class RateLimiter:
    """Simple rate limiter to stay within free tier limits."""
    
    def __init__(self, max_requests: int = 25, window_seconds: int = 60):
        """
        Args:
            max_requests: Max requests per window (25 to stay safe under 30 limit)
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding limit."""
        now = time.time()
        # Remove old requests outside the window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record a request timestamp."""
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        """Get seconds to wait before next request is allowed."""
        if self.can_make_request():
            return 0
        oldest = self.requests[0]
        return max(0, (oldest + self.window_seconds) - time.time())


class GroqClient:
    """
    Client for Groq API - fast inference with Llama 3.
    Free tier: 30 requests/min, 6000 tokens/min
    """
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    def __init__(self):
        self._system_prompt = None
        self._initialized = False
        self._api_key = None
        self._rate_limiter = RateLimiter(max_requests=25, window_seconds=60)  # Stay under 30/min
    
    def initialize(self):
        """Initialize the Groq client."""
        if self._initialized:
            return
        
        self._api_key = settings.GROQ_API_KEY
        self._system_prompt = self._load_system_prompt()
        self._initialized = True
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = settings.PROMPTS_DIR / "system_prompt.txt"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        
        return """You are SamairaAI, a friendly financial literacy companion for Indian families.
Speak in Hinglish (Hindi + English mix). Be warm, approachable, and helpful.
Focus on savings schemes like SIP, RD, PPF, FD, and goal-based planning.
Never recommend specific funds or stocks. Only provide educational information."""
    
    async def chat(
        self,
        user_message: str,
        session,  # SessionState
        context: Optional[str] = None
    ) -> str:
        """
        Send a message and get a response using Groq/Llama 3.
        
        Args:
            user_message: The user's input
            session: Current session state for context
            context: Additional context (calculation results, etc.)
        
        Returns:
            AI response text
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            return self._get_fallback_response("No API key")
        
        # Check rate limit to protect free tier
        if not self._rate_limiter.can_make_request():
            wait_time = self._rate_limiter.wait_time()
            print(f"⚠️ Rate limit: waiting {wait_time:.1f}s to protect free tier")
            return self._get_fallback_response(f"Rate limit - please wait {int(wait_time)} seconds")
        
        # Build messages array
        messages = [
            {"role": "system", "content": self._system_prompt}
        ]
        
        # Add conversation history (limit to save tokens)
        history = session.get_conversation_history(n=6)  # Reduced to save tokens
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        # Build current message with context
        current_message = user_message
        if context:
            current_message = f"{user_message}\n\n[Relevant context: {context}]"
        
        # Add user context
        user_context = self._build_user_context(session)
        if user_context and not history:  # Only add context at start
            current_message = f"[User info: {user_context}]\n\n{current_message}"
        
        messages.append({"role": "user", "content": current_message})
        
        try:
            # Record request for rate limiting
            self._rate_limiter.record_request()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",  # Best free model
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 800,  # Reduced to save tokens
                        "top_p": 0.9
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = response.text
                    print(f"Groq API error {response.status_code}: {error_text}")
                    return self._get_fallback_response(error_text)
                    
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._get_fallback_response(str(e))
    
    async def chat_stream(
        self,
        user_message: str,
        session,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response word-by-word using Groq.
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            yield self._get_fallback_response("No API key")
            return
        
        # Check rate limit
        if not self._rate_limiter.can_make_request():
            yield self._get_fallback_response("Rate limit reached - thoda wait karo!")
            return
        
        # Build messages
        messages = [{"role": "system", "content": self._system_prompt}]
        
        history = session.get_conversation_history(n=6)  # Reduced to save tokens
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        current_message = user_message
        if context:
            current_message = f"{user_message}\n\n[Relevant context: {context}]"
        
        messages.append({"role": "user", "content": current_message})
        
        try:
            # Record request
            self._rate_limiter.record_request()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 800,  # Reduced to save tokens
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                import json
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            except:
                                pass
        except Exception as e:
            print(f"Groq streaming error: {e}")
            yield self._get_fallback_response(str(e))
    
    def _build_user_context(self, session) -> str:
        """Build context string from session state."""
        parts = []
        
        if session.user_name:
            parts.append(f"User's name: {session.user_name}")
        
        if hasattr(session, 'current_goal') and session.current_goal:
            goal = session.current_goal
            parts.append(f"Current goal: {goal.goal_type.value}")
            if goal.target_amount:
                parts.append(f"Target: ₹{goal.target_amount:,.0f}")
        
        if hasattr(session, 'risk_preference') and session.risk_preference:
            parts.append(f"Risk: {session.risk_preference.value}")
        
        return "; ".join(parts) if parts else ""
    
    def _get_fallback_response(self, error: str) -> str:
        """Get a contextual fallback response."""
        if "rate" in error.lower() or "limit" in error.lower():
            return (
                "Ek second ruko, bahut saare sawaal aa rahe hain! "
                "Thoda wait karke dobara try karo. Main ready hoon aapki help ke liye."
            )
        return (
            "Arre, sorry yaar! Kuch technical issue aa gaya. "
            "Kya aap apna sawaal dobara puch sakte ho?"
        )


# Global client instance
groq_client = GroqClient()
