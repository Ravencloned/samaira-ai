"""
Groq API client for SamairaAI.
Uses Llama 4 via Groq's free API for fast, high-quality responses.
"""

import httpx
import time
import re
from typing import Optional, AsyncGenerator
from collections import deque

from config.settings import settings


class RateLimiter:
    """Simple rate limiter to stay within free tier limits."""
    
    def __init__(self, max_requests: int = 25, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def can_make_request(self) -> bool:
        now = time.time()
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        if self.can_make_request():
            return 0
        oldest = self.requests[0]
        return max(0, (oldest + self.window_seconds) - time.time())


class GroqClient:
    """Client for Groq API with Llama 4."""
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
    
    def __init__(self):
        self._system_prompt = None
        self._initialized = False
        self._api_key = None
        self._rate_limiter = RateLimiter(max_requests=25, window_seconds=60)
    
    def initialize(self):
        if self._initialized:
            return
        self._api_key = settings.GROQ_API_KEY
        self._system_prompt = self._load_system_prompt()
        self._initialized = True
    
    def _load_system_prompt(self) -> str:
        prompt_path = settings.PROMPTS_DIR / "system_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "You are SamairaAI, a helpful financial advisor for Indian families."
    
    # Common Indian names for direct detection (English + Hindi)
    COMMON_NAMES = {
        'yash', 'rahul', 'amit', 'priya', 'neha', 'rohit', 'vikram', 'ankit', 'pooja', 'ravi',
        'sanjay', 'deepak', 'arun', 'vijay', 'suresh', 'kumar', 'raj', 'aman', 'arjun', 'karan',
        'nikhil', 'sachin', 'aditya', 'manish', 'sunil', 'rakesh', 'ajay', 'vishal', 'gaurav',
        'abhishek', 'harsh', 'varun', 'mohit', 'ashish', 'vivek', 'akash', 'shubham', 'tushar',
        'divya', 'anjali', 'shruti', 'swati', 'megha', 'nisha', 'kavita', 'sunita', 'rekha',
        'meera', 'suman', 'geeta', 'seema', 'anita', 'sarita', 'mamta', 'ritu', 'komal',
        # Hindi script versions
        'यश', 'याश', 'राहुल', 'अमित', 'प्रिया', 'नेहा', 'रोहित', 'विक्रम', 'अंकित', 'पूजा',
        'रवि', 'संजय', 'दीपक', 'अरुण', 'विजय', 'सुरेश', 'कुमार', 'राज', 'अमन', 'अर्जुन',
    }
    
    # Skip words that aren't names (English + Hindi)
    SKIP_WORDS = {
        'mera', 'naam', 'hai', 'main', 'hoon', 'hi', 'hello', 'the', 'is', 'am', 'my', 'name',
        'मेरा', 'मीरा', 'मिरा', 'नाम', 'है', 'मैं', 'हूं', 'हूँ', 'जी', 'हां', 'हाँ',
        'aapka', 'tumhara', 'kya', 'ji', 'bhai', 'sir', 'madam', 'aap', 'tum',
        'आपका', 'तुम्हारा', 'क्या', 'भाई', 'सर', 'मैडम', 'आप', 'तुम',
    }
    
    def _extract_user_info(self, message: str, session) -> None:
        """Extract user info from message and store in session. Supports Hindi, Urdu, and English."""
        msg_lower = message.lower()
        
        # Extract name - supports English, Hindi Devanagari, and Urdu
        if not session.user_name:
            name = self._extract_name_multilingual(message)
            if name:
                session.user_name = name
                print(f"[INFO] Extracted name: {name}")
        
        # Also scan conversation history for name if not found yet
        if not session.user_name:
            name = self._scan_history_for_name(session)
            if name:
                session.user_name = name
                print(f"[INFO] Extracted name from history: {name}")
        
        # Extract age
        if not hasattr(session, 'user_age') or not session.user_age:
            age_patterns = [
                r"(?:i am|i'm|meri age|meri umar|age hai|saal ka|saal ki|years old)\s*(\d{1,2})",
                r"(\d{1,2})\s*(?:saal|years|yr|age)",
            ]
            for pattern in age_patterns:
                match = re.search(pattern, msg_lower)
                if match:
                    age = int(match.group(1))
                    if 15 <= age <= 80:
                        session.user_age = age
                        print(f"[INFO] Extracted age: {age}")
                        break
        
        # Extract income
        if not hasattr(session, 'user_income') or not session.user_income:
            income_patterns = [
                r"(?:earn|salary|income|kamaata|kamata)\s*(?:around|approx|about)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)",
                r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\s*(?:per month|monthly|mahine)",
            ]
            for pattern in income_patterns:
                match = re.search(pattern, msg_lower)
                if match:
                    income = float(match.group(1))
                    session.user_income = income
                    print(f"[INFO] Extracted income: {income} lakh")
                    break
        
        # Extract savings capacity
        if not hasattr(session, 'user_savings') or not session.user_savings:
            savings_patterns = [
                r"(?:save|saving|bacha|bachata)\s*(?:around|approx|about)?\s*(\d+(?:,\d+)?)",
            ]
            for pattern in savings_patterns:
                match = re.search(pattern, msg_lower)
                if match:
                    savings = int(match.group(1).replace(',', ''))
                    session.user_savings = savings
                    print(f"[INFO] Extracted savings: {savings}")
                    break
        
        # Extract location
        if not hasattr(session, 'user_location') or not session.user_location:
            cities = ['mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad', 'jaipur']
            for city in cities:
                if city in msg_lower:
                    session.user_location = city.title()
                    print(f"[INFO] Extracted location: {city.title()}")
                    break
    
    def _extract_name_multilingual(self, message: str) -> Optional[str]:
        """Extract name from message supporting English, Hindi, and Urdu scripts."""
        
        # Pattern set 1: English patterns
        english_patterns = [
            r"(?:my name is|i am|i'm|call me)\s+([A-Za-z]+)",
            r"^([A-Za-z]+)\s+(?:here|hoon|hu|hai|speaking)$",
        ]
        
        # Pattern set 2: Hindi/Hinglish patterns (romanized)
        hindi_roman_patterns = [
            r"(?:mera naam|naam hai|main|mera nam)\s+([A-Za-z]+)",
            r"(?:mai|mein)\s+([A-Za-z]+)\s+(?:hoon|hu|hai)",
        ]
        
        # Pattern set 3: Hindi Devanagari patterns
        # Using raw Unicode code points to avoid encoding issues
        # मेरा = \u092e\u0947\u0930\u093e, नाम = \u0928\u093e\u092e, है = \u0939\u0948
        # मीरा = \u092e\u0940\u0930\u093e (STT error), मैं = \u092e\u0948\u0902
        devanagari_patterns = [
            # "मेरा नाम X" / "मीरा नाम X" / "नाम X है"
            r'(?:\u092e\u0947\u0930\u093e\s*\u0928\u093e\u092e|\u092e\u0940\u0930\u093e\s*\u0928\u093e\u092e|\u092e\u093f\u0930\u093e\s*\u0928\u093e\u092e|\u0928\u093e\u092e)\s+([A-Za-z\u0900-\u097F]+)',
            # "मैं X हूं" / "मैं X" (मैं = \u092e\u0948\u0902, हूं = \u0939\u0942\u0902)
            r'\u092e\u0948\u0902\s+([A-Za-z\u0900-\u097F]+)(?:\s+\u0939\u0942\u0902|\s+\u0939\u0942\u0901|\s+\u0939\u0941|$)',
            # Reverse order: "X नाम है मेरा"
            r'([A-Za-z\u0900-\u097F]+)\s+\u0928\u093e\u092e\s+\u0939\u0948',
        ]
        
        # Pattern set 4: Urdu patterns  
        urdu_patterns = [
            r'(?:\u0645\u06cc\u0631\u0627\s*\u0646\u0627\u0645|\u0646\u0627\u0645\s*\u06c1\u06d2)\s+([A-Za-z\u0600-\u06FF]+)',
        ]
        
        # Try all pattern sets
        all_patterns = english_patterns + hindi_roman_patterns + devanagari_patterns + urdu_patterns
        
        for pattern in all_patterns:
            match = re.search(pattern, message, re.IGNORECASE | re.UNICODE)
            if match:
                name = match.group(1).strip()
                # Clean and validate
                if self._is_valid_name(name):
                    return self._normalize_name(name)
        
        # Direct name detection - check if message contains a known name
        words = re.findall(r'[A-Za-z\u0900-\u097F\u0600-\u06FF]+', message)
        for word in words:
            word_lower = word.lower() if word.isascii() else word
            if word_lower in self.COMMON_NAMES or word in self.COMMON_NAMES:
                return self._normalize_name(word)
        
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if extracted text is a valid name."""
        if not name or len(name) < 2:
            return False
        name_lower = name.lower() if name.isascii() else name
        if name_lower in self.SKIP_WORDS or name in self.SKIP_WORDS:
            return False
        # Must have at least one letter (any script)
        if not re.search(r'[A-Za-z\u0900-\u097F\u0600-\u06FF]', name):
            return False
        return True
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name to proper format."""
        # Hindi name mappings (common variations to standard form)
        hindi_to_english = {
            'यश': 'Yash', 'याश': 'Yash',
            'राहुल': 'Rahul', 'अमित': 'Amit', 'प्रिया': 'Priya',
            'नेहा': 'Neha', 'रोहित': 'Rohit', 'विक्रम': 'Vikram',
            'अंकित': 'Ankit', 'पूजा': 'Pooja', 'रवि': 'Ravi',
        }
        if name in hindi_to_english:
            return hindi_to_english[name]
        # Title case for ASCII names
        if name.isascii():
            return name.title()
        return name
    
    def _scan_history_for_name(self, session) -> Optional[str]:
        """Scan conversation history for name mentions we might have missed."""
        history = session.get_conversation_history(n=20)
        for msg in history:
            if msg['role'] == 'user':
                name = self._extract_name_multilingual(msg['content'])
                if name:
                    return name
        return None
    
    def _build_user_profile(self, session) -> str:
        """Build a user profile string from session data."""
        parts = []
        
        if session.user_name:
            parts.append(f"Name: {session.user_name}")
        if hasattr(session, 'user_age') and session.user_age:
            parts.append(f"Age: {session.user_age}")
        if hasattr(session, 'user_income') and session.user_income:
            parts.append(f"Monthly Income: {session.user_income} lakh")
        if hasattr(session, 'user_savings') and session.user_savings:
            parts.append(f"Monthly Savings: Rs {session.user_savings}")
        if hasattr(session, 'user_location') and session.user_location:
            parts.append(f"Location: {session.user_location}")
        if session.current_goal:
            parts.append(f"Goal: {session.current_goal.goal_type.value}")
            if session.current_goal.target_amount:
                parts.append(f"Target: Rs {session.current_goal.target_amount:,.0f}")
            if session.current_goal.timeline_years:
                parts.append(f"Timeline: {session.current_goal.timeline_years} years")
        
        if parts:
            return "[USER PROFILE]\n" + "\n".join(parts) + "\n[END PROFILE]"
        return ""
    
    def _build_messages(self, user_message: str, session, context: Optional[str] = None) -> list:
        """Build the messages array for the API call."""
        
        # Extract user info BEFORE building messages
        self._extract_user_info(user_message, session)
        
        # Build system message with user profile
        user_profile = self._build_user_profile(session)
        system_content = self._system_prompt
        if user_profile:
            system_content = f"{user_profile}\n\n{self._system_prompt}"
        
        messages = [{"role": "system", "content": system_content}]
        
        # Add conversation history (15 messages = ~7 turns)
        history = session.get_conversation_history(n=15)
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        # Add current message with any additional context
        current_message = user_message
        if context:
            current_message = f"{user_message}\n\n[Context: {context}]"
        
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    async def chat(self, user_message: str, session, context: Optional[str] = None) -> str:
        """Send a message and get a response."""
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            return self._get_fallback_response("No API key")
        
        if not self._rate_limiter.can_make_request():
            return self._get_fallback_response("Rate limit")
        
        messages = self._build_messages(user_message, session, context)
        
        try:
            self._rate_limiter.record_request()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500,
                        "top_p": 0.9
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"Groq API error {response.status_code}: {response.text}")
                    return self._get_fallback_response(response.text)
                    
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._get_fallback_response(str(e))
    
    async def chat_stream(self, user_message: str, session, context: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream a response word-by-word."""
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            yield self._get_fallback_response("No API key")
            return
        
        if not self._rate_limiter.can_make_request():
            yield self._get_fallback_response("Rate limit")
            return
        
        messages = self._build_messages(user_message, session, context)
        
        try:
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
                        "model": self.MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500,
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
    
    def _get_fallback_response(self, error: str) -> str:
        if "rate" in error.lower() or "limit" in error.lower():
            return "Ek second ruko, thoda busy hoon! Dobara try karo."
        return "Sorry, kuch technical issue aa gaya. Dobara try karo."


# Global client instance
groq_client = GroqClient()
