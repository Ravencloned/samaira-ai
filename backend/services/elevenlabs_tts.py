"""
ElevenLabs TTS service for natural Indian voice.
Uses the free tier (10K characters/month) for high-quality speech.
"""

import httpx
import base64
from typing import Optional
from config.settings import settings


class ElevenLabsTTS:
    """
    ElevenLabs Text-to-Speech with natural Indian female voice.
    Free tier: 10,000 characters/month
    """
    
    API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    # Good voices for Indian English/Hinglish
    VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",  # Warm female
        "domi": "AZnzlk1XvdvUeBnXmlld",    # Young female
        "bella": "EXAVITQu4vr4xnSDxMaL",   # Soft female
        "elli": "MF3mGyEYCl7XYWbV9V6O",    # Middle-aged female
        "sarah": "EXAVITQu4vr4xnSDxMaL",   # Clear female
    }
    
    DEFAULT_VOICE = "rachel"  # Warm and friendly
    
    def __init__(self):
        self._api_key = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the TTS service."""
        if self._initialized:
            return
        self._api_key = settings.ELEVENLABS_API_KEY
        self._initialized = True
    
    async def synthesize(
        self,
        text: str,
        voice: str = None
    ) -> Optional[bytes]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice: Voice ID or name to use
        
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            return None
        
        # Resolve voice ID
        voice_id = self.VOICES.get(voice or self.DEFAULT_VOICE, self.VOICES[self.DEFAULT_VOICE])
        
        # Prepare text - clean for better pronunciation
        clean_text = self._prepare_text(text)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_URL}/{voice_id}",
                    headers={
                        "xi-api-key": self._api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": clean_text,
                        "model_id": "eleven_multilingual_v2",  # Best for Hinglish
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                            "style": 0.3,
                            "use_speaker_boost": True
                        }
                    }
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"ElevenLabs error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None
    
    async def synthesize_base64(self, text: str, voice: str = None) -> Optional[str]:
        """
        Convert text to speech and return as base64 string.
        Useful for sending audio in JSON responses.
        """
        audio_bytes = await self.synthesize(text, voice)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for better TTS pronunciation."""
        # Remove markdown formatting
        import re
        
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Remove headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove bullet points
        text = re.sub(r'^[-*]\s*', '', text, flags=re.MULTILINE)
        
        # Fix common pronunciation issues
        replacements = {
            "SIP": "S I P",
            "RD": "R D",
            "FD": "F D",
            "PPF": "P P F",
            "NPS": "N P S",
            "EMI": "E M I",
            "ELSS": "E L S S",
            "₹": "rupees ",
            "Rs.": "rupees",
            "Rs": "rupees",
            "%": " percent",
            "yr": "year",
            "yrs": "years",
            "lakh": "laakh",
            "crore": "karor",
            "&": "and",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_available(self) -> bool:
        """Check if ElevenLabs is configured."""
        if not self._initialized:
            self.initialize()
        return bool(self._api_key)


# Global instance
elevenlabs_tts = ElevenLabsTTS()
