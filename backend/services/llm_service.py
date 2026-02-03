"""
Unified LLM service for SamairaAI.
Supports multiple providers: Groq (free, recommended) and Gemini.
"""

from typing import Optional, AsyncGenerator
from config.settings import settings


class LLMService:
    """
    Unified interface for LLM providers.
    Automatically falls back between providers.
    """
    
    def __init__(self):
        self._provider = None
        self._groq_client = None
        self._gemini_client = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the configured LLM provider."""
        if self._initialized:
            return
        
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "groq" and settings.GROQ_API_KEY:
            from services.groq_client import groq_client
            groq_client.initialize()
            self._groq_client = groq_client
            self._provider = "groq"
            print("✅ LLM Provider: Groq (Llama 3.3 70B)")
        elif settings.GEMINI_API_KEY:
            from services.gemini_client import gemini_client
            gemini_client.initialize()
            self._gemini_client = gemini_client
            self._provider = "gemini"
            print("✅ LLM Provider: Google Gemini")
        else:
            print("⚠️ No LLM API key configured! Using fallback responses.")
            self._provider = "fallback"
        
        self._initialized = True
    
    @property
    def provider(self) -> str:
        """Get current provider name."""
        if not self._initialized:
            self.initialize()
        return self._provider
    
    async def chat(
        self,
        user_message: str,
        session,
        context: Optional[str] = None
    ) -> str:
        """
        Send a message and get a response.
        
        Args:
            user_message: The user's input
            session: Current session state
            context: Additional context (calculations, etc.)
        
        Returns:
            AI response text
        """
        if not self._initialized:
            self.initialize()
        
        if self._provider == "groq":
            return await self._groq_client.chat(user_message, session, context)
        elif self._provider == "gemini":
            return await self._gemini_client.chat(user_message, session, context)
        else:
            return self._get_smart_fallback(user_message, session)
    
    async def chat_stream(
        self,
        user_message: str,
        session,
        context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response for real-time display.
        """
        if not self._initialized:
            self.initialize()
        
        if self._provider == "groq":
            async for chunk in self._groq_client.chat_stream(user_message, session, context):
                yield chunk
        elif self._provider == "gemini":
            # Gemini doesn't have native streaming in our client, simulate it
            response = await self._gemini_client.chat(user_message, session, context)
            for word in response.split():
                yield word + " "
        else:
            # Fallback - yield the whole response
            response = self._get_smart_fallback(user_message, session)
            for word in response.split():
                yield word + " "
    
    def _get_smart_fallback(self, message: str, session) -> str:
        """
        Provide contextual fallback responses when no LLM is available.
        At least tries to understand the intent.
        """
        message_lower = message.lower()
        
        # Greeting detection
        greetings = ["hi", "hello", "namaste", "hey", "hola", "kaise", "how are", "can you hear"]
        if any(g in message_lower for g in greetings):
            name = session.user_name or "dost"
            return (
                f"Namaste {name}! Haan main sun sakti hoon. Main SamairaAI hoon, "
                f"aapki financial friend! Batao, kya help chahiye? SIP, RD, PPF, "
                f"ya koi aur sawaal ho toh poocho!"
            )
        
        # SIP queries
        if "sip" in message_lower:
            return (
                "SIP (Systematic Investment Plan) ek smart tarika hai invest karne ka! "
                "Har mahine fixed amount mutual funds mein jaata hai. Benefits:\n"
                "1. **Rupee cost averaging** - market ups-downs ka fayda\n"
                "2. **Discipline** - automatic savings habit\n"
                "3. **Flexibility** - ₹500 se bhi start kar sakte ho\n"
                "4. **Power of compounding** - long term mein amazing returns\n\n"
                "Kya aap jaanna chahoge kitna SIP karna chahiye?"
            )
        
        # RD queries
        if "rd" in message_lower or "recurring deposit" in message_lower:
            return (
                "RD (Recurring Deposit) bank mein safe investment hai!\n"
                "- Fixed monthly deposit karni hoti hai\n"
                "- Interest guaranteed hota hai (6-7% usually)\n"
                "- 6 months se 10 years tak tenure\n"
                "- Short term goals ke liye perfect!\n\n"
                "RD vs SIP mein confusion hai? Main compare kar sakti hoon."
            )
        
        # PPF queries
        if "ppf" in message_lower:
            return (
                "PPF (Public Provident Fund) ek government backed scheme hai:\n"
                "- **Interest:** ~7.1% (tax-free!)\n"
                "- **Lock-in:** 15 years\n"
                "- **Tax benefit:** Section 80C under ₹1.5 lakh\n"
                "- **Safety:** Government guarantee\n\n"
                "Bachon ki education ya retirement ke liye perfect hai!"
            )
        
        # Emergency fund
        if "emergency" in message_lower or "fund" in message_lower:
            return (
                "Emergency Fund bahut zaroori hai! Rule of thumb:\n"
                "- **Kitna:** 3-6 months ki expenses\n"
                "- **Kahaan:** Savings account ya Liquid Mutual Fund\n"
                "- **Kab use karein:** Job loss, medical emergency, urgent repairs\n\n"
                "Pehle emergency fund, phir investments!"
            )
        
        # Comparison queries
        if "vs" in message_lower or "compare" in message_lower or "better" in message_lower:
            return (
                "Comparison ke liye bataao kaunsi schemes compare karni hain:\n"
                "- SIP vs RD\n"
                "- FD vs PPF\n"
                "- PPF vs NPS\n"
                "- Mutual Funds vs Direct Stocks\n\n"
                "Specific comparison chahiye toh batao!"
            )
        
        # Default helpful response
        return (
            "Hmm, main samajh nahi paayi. Kya aap thoda detail mein bata sakte ho? "
            "Main help kar sakti hoon:\n"
            "- SIP, RD, FD, PPF ke baare mein\n"
            "- Investment planning\n"
            "- Emergency fund guidance\n"
            "- Goal-based savings (education, wedding, retirement)\n\n"
            "Kya specific jaanna chahte ho?"
        )


# Global instance
llm_service = LLMService()
