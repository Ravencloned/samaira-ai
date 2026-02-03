"""
Google Gemini API client for SamairaAI.
Handles conversation with the LLM including system prompt and history management.
"""

import google.generativeai as genai
from typing import Optional
from pathlib import Path

from config.settings import settings
from core.state import SessionState


class GeminiClient:
    """
    Wrapper for Google Gemini API with SamairaAI system prompt.
    """
    
    def __init__(self):
        self._model = None
        self._system_prompt = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the Gemini client with API key and system prompt."""
        if self._initialized:
            return
        
        # Configure API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Load system prompt
        self._system_prompt = self._load_system_prompt()
        
        # Initialize model (using gemini-2.0-flash for best balance)
        self._model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",  # Fast and capable
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )
        
        self._initialized = True
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = settings.PROMPTS_DIR / "system_prompt.txt"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        
        # Fallback minimal prompt
        return """You are SamairaAI, a friendly financial literacy companion for Indian families.
Speak in Hinglish (Hindi + English mix). Be calm, respectful, and helpful.
Never recommend specific funds or stocks. Only provide educational information."""
    
    async def chat(
        self,
        user_message: str,
        session: SessionState,
        context: Optional[str] = None
    ) -> str:
        """
        Send a message and get a response.
        
        Args:
            user_message: The user's input
            session: Current session state for context
            context: Additional context to inject (e.g., calculation results)
        
        Returns:
            AI response text
        """
        if not self._initialized:
            self.initialize()
        
        # Build conversation history for context
        history = session.get_gemini_history(n=8)  # Last 8 messages
        
        # Prepend system prompt to history if this is first message
        if not history:
            history = [
                {"role": "user", "parts": [f"[SYSTEM INSTRUCTIONS - Follow these strictly]\n{self._system_prompt}\n\n[END SYSTEM INSTRUCTIONS]"]},
                {"role": "model", "parts": ["Namaste! Main SamairaAI hoon - aapki financial literacy companion. Main aapki madad karne ke liye ready hoon. Bataaiye, aaj main aapki kya help kar sakti hoon?"]}
            ]
        
        # Create chat with history
        chat = self._model.start_chat(history=history)
        
        # Build the message with any additional context
        message = user_message
        if context:
            message = f"{user_message}\n\n[Context for response: {context}]"
        
        # Add user context if available
        user_context = self._build_user_context(session)
        if user_context:
            message = f"[User Context: {user_context}]\n\n{message}"
        
        try:
            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            # Handle errors gracefully
            print(f"Gemini API error: {e}")
            return self._get_fallback_response(str(e))
    
    def chat_sync(
        self,
        user_message: str,
        session: SessionState,
        context: Optional[str] = None
    ) -> str:
        """Synchronous version of chat for simpler use cases."""
        if not self._initialized:
            self.initialize()
        
        history = session.get_gemini_history(n=8)
        chat = self._model.start_chat(history=history)
        
        message = user_message
        if context:
            message = f"{user_message}\n\n[Context for response: {context}]"
        
        user_context = self._build_user_context(session)
        if user_context:
            message = f"[User Context: {user_context}]\n\n{message}"
        
        try:
            response = chat.send_message(message)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_fallback_response(str(e))
    
    def _build_user_context(self, session: SessionState) -> str:
        """Build context string from session state."""
        parts = []
        
        if session.user_name:
            parts.append(f"User's name: {session.user_name}")
        
        if session.current_goal:
            goal = session.current_goal
            parts.append(f"Current goal: {goal.goal_type.value}")
            if goal.target_amount:
                parts.append(f"Target amount: ₹{goal.target_amount:,.0f}")
            if goal.timeline_years:
                parts.append(f"Timeline: {goal.timeline_years} years")
        
        if session.risk_preference:
            parts.append(f"Risk preference: {session.risk_preference.value}")
        
        if session.topics_discussed:
            parts.append(f"Topics discussed: {', '.join(session.topics_discussed[-3:])}")
        
        return "; ".join(parts) if parts else ""
    
    def _get_fallback_response(self, error: str) -> str:
        """Get a graceful fallback response on error."""
        if "quota" in error.lower() or "rate" in error.lower() or "429" in str(error):
            # Return a helpful demo response instead of error
            return self._get_demo_response()
        elif "safety" in error.lower() or "blocked" in error.lower():
            return (
                "Is sawaal ka jawab dena mere liye possible nahi hai. "
                "Kya main aapki kisi aur cheez mein madad kar sakti hoon?"
            )
        else:
            return (
                "Maaf kijiye, kuch technical issue aa gaya. "
                "Kya aap apna sawaal dobara puch sakte hain?"
            )
    
    def _get_demo_response(self) -> str:
        """Get a demo response when API is unavailable."""
        import random
        demo_responses = [
            "Bahut accha sawaal hai! Dekho, financial planning mein sabse pehle emergency fund banana zaroori hai - lagbhag 3-6 months ki expenses rakho. Uske baad hi SIP ya investments start karo. Kya aap emergency fund ke baare mein aur jaanna chahte hain?",
            
            "SIP aur RD mein main farak yeh hai: SIP mein aapka paisa mutual funds mein jaata hai jo market ke saath grow karta hai, jabki RD mein fixed interest milta hai. Long term ke liye (5+ years), SIP usually better returns deta hai, lekin short term ke liye RD safe hai.",
            
            "PPF ek bahut hi safe government scheme hai. 15 saal ka lock-in hota hai, lekin tax benefits bhi milte hain - Section 80C ke under 1.5 lakh tak deduction. Interest rate quarterly change hota hai, abhi lagbhag 7.1% hai. Bacchon ki education ke liye perfect hai!",
            
            "Emergency fund banaane ka sabse simple tarika: Har mahine apni salary ka 10-20% alag rakho ek savings account mein. Target rakho 3-6 months ki expenses cover ho jaaye. Yeh paisa sirf emergency ke liye use karo - job loss, medical emergency, ya urgent repairs ke liye.",
            
            "Namaste! Main SamairaAI hoon. Aap mujhse kuch bhi puch sakte ho - SIP vs RD comparison, PPF ke benefits, bachon ki education planning, ya koi bhi financial sawaal. Main simple Hinglish mein samjhaaungi!"
        ]
        return random.choice(demo_responses)


# Global client instance
gemini_client = GeminiClient()
