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
            return self._get_smart_fallback(user_message, str(e))
    
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
            return self._get_smart_fallback(user_message, str(e))
    
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
    
    def _get_smart_fallback(self, user_message: str, error: str) -> str:
        """Get a contextual fallback response based on user's message."""
        message_lower = user_message.lower()
        
        # Greeting detection
        greetings = ["hi", "hello", "namaste", "hey", "hola", "kaise", "how are", "can you hear", "sun", "suno"]
        if any(g in message_lower for g in greetings):
            return (
                "Namaste! Haan main sun sakti hoon! 🙏 Main SamairaAI hoon - aapki financial friend.\n\n"
                "Main aapki madad kar sakti hoon:\n"
                "- **SIP vs RD** comparison\n"
                "- **PPF, NPS** government schemes\n"
                "- **Emergency Fund** planning\n"
                "- **Goal-based savings** - education, wedding, retirement\n\n"
                "Batao, kya jaanna chahte ho?"
            )
        
        # SIP queries
        if "sip" in message_lower:
            return (
                "**SIP (Systematic Investment Plan)** ek smart investment tarika hai!\n\n"
                "📊 **Kaise kaam karta hai:**\n"
                "- Har mahine fixed amount mutual funds mein invest hoti hai\n"
                "- ₹500/month se bhi start kar sakte ho\n"
                "- Market ups-downs ka average nikalta hai (Rupee Cost Averaging)\n\n"
                "📈 **Example:**\n"
                "- ₹5,000/month × 10 years × 12% returns\n"
                "- Total invested: ₹6 lakhs\n"
                "- Expected value: ~₹11.6 lakhs!\n\n"
                "Kya aap SIP vs RD compare karna chahenge?"
            )
        
        # RD queries
        if "rd" in message_lower or "recurring" in message_lower:
            return (
                "**RD (Recurring Deposit)** bank mein safe savings option hai!\n\n"
                "🏦 **Features:**\n"
                "- Fixed monthly deposit\n"
                "- Guaranteed interest (6-7% currently)\n"
                "- 6 months to 10 years tenure\n"
                "- No market risk\n\n"
                "📊 **Example:**\n"
                "- ₹5,000/month × 5 years × 6.5% interest\n"
                "- Total deposited: ₹3 lakhs\n"
                "- Maturity value: ~₹3.5 lakhs\n\n"
                "Short-term goals ke liye RD perfect hai!"
            )
        
        # PPF queries
        if "ppf" in message_lower:
            return (
                "**PPF (Public Provident Fund)** government-backed safe investment hai!\n\n"
                "✅ **Benefits:**\n"
                "- Interest rate: ~7.1% (tax-free!)\n"
                "- Lock-in: 15 years\n"
                "- Tax deduction: Section 80C (₹1.5 lakh/year)\n"
                "- Government guarantee - 100% safe\n\n"
                "📊 **Limits:**\n"
                "- Minimum: ₹500/year\n"
                "- Maximum: ₹1.5 lakh/year\n\n"
                "Bachon ki education ya retirement ke liye perfect!"
            )
        
        # Emergency fund
        if "emergency" in message_lower or "fund" in message_lower:
            return (
                "**Emergency Fund** sabse pehle banana chahiye! 🚨\n\n"
                "📋 **Kitna rakhein:**\n"
                "- Single income: 6 months expenses\n"
                "- Dual income: 3-4 months expenses\n\n"
                "🏦 **Kahaan rakhein:**\n"
                "- Savings account (easy access)\n"
                "- Liquid mutual funds (better returns)\n"
                "- FD with premature withdrawal option\n\n"
                "⚠️ **Kab use karein:**\n"
                "- Job loss\n"
                "- Medical emergency\n"
                "- Urgent home repairs\n\n"
                "Pehle emergency fund, phir investments!"
            )
        
        # Comparison queries
        if "vs" in message_lower or "compare" in message_lower or "better" in message_lower:
            return (
                "Main aapko compare kar ke bata sakti hoon! 📊\n\n"
                "**Popular comparisons:**\n"
                "- SIP vs RD - Market-linked vs Fixed returns\n"
                "- PPF vs FD - Long-term tax-free vs Short-term\n"
                "- NPS vs PPF - Retirement planning options\n"
                "- Mutual Funds vs Stocks - Professional vs Direct\n\n"
                "Kaunsi schemes compare karni hain?"
            )
        
        # Default helpful response
        return (
            "Hmm, main samajh gayi! 🤔\n\n"
            "Main in topics mein expert hoon:\n"
            "- **SIP/Mutual Funds** - Long-term wealth building\n"
            "- **RD/FD** - Safe, guaranteed returns\n"
            "- **PPF/NPS** - Tax-saving + retirement\n"
            "- **Emergency Fund** - Financial safety net\n"
            "- **Goal Planning** - Education, wedding, home\n\n"
            "Kya specific jaanna chahte ho? Main Hinglish mein simple tarike se samjhaungi!"
        )
    
    def _get_demo_response(self) -> str:
        """Get a demo response when API is unavailable - but make it contextual."""
        # This will be used when we have last_message context
        return (
            "Namaste! Main SamairaAI hoon - aapki financial literacy companion. "
            "Abhi mera AI brain thoda busy hai, lekin main phir bhi basic help kar sakti hoon!\n\n"
            "Aap mujhse puch sakte ho:\n"
            "- **SIP** (Systematic Investment Plan) ke baare mein\n"
            "- **RD** (Recurring Deposit) kaise kaam karta hai\n"
            "- **PPF** (Public Provident Fund) ke benefits\n"
            "- **Emergency Fund** kaise banayein\n"
            "- **Goal Planning** - education, wedding, retirement\n\n"
            "Batao, kismein help chahiye?"
        )


# Global client instance
gemini_client = GeminiClient()
