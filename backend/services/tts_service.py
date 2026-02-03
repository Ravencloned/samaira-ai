"""
Text-to-Speech service for SamairaAI.
Supports browser-based TTS and Google Cloud TTS.
"""

from typing import Optional
from enum import Enum


class TTSProvider(str, Enum):
    """Available TTS providers."""
    BROWSER = "browser"  # Use Web Speech API on frontend
    GOOGLE = "google"    # Google Cloud TTS (requires API key)


class TTSService:
    """
    Text-to-Speech service.
    For the prototype, we primarily use browser-based TTS.
    This service provides text preprocessing and SSML generation.
    """
    
    def __init__(self, provider: TTSProvider = TTSProvider.BROWSER):
        self.provider = provider
    
    def prepare_text_for_speech(self, text: str) -> str:
        """
        Prepare text for TTS by cleaning up formatting.
        Removes markdown, adjusts for natural speech.
        """
        # Remove markdown formatting
        text = text.replace("**", "")
        text = text.replace("*", "")
        text = text.replace("#", "")
        text = text.replace("`", "")
        
        # Convert bullet points to natural pauses
        text = text.replace("• ", "... ")
        text = text.replace("- ", "... ")
        
        # Handle rupee symbol
        text = text.replace("₹", "rupees ")
        
        # Handle common abbreviations
        text = text.replace("p.a.", "per annum")
        text = text.replace("i.e.", "that is")
        text = text.replace("e.g.", "for example")
        
        # Handle lakhs/crores naturally
        text = text.replace(" lakhs", " lakh")
        text = text.replace(" crores", " crore")
        
        # Clean up extra whitespace
        text = " ".join(text.split())
        
        return text
    
    def get_tts_config(self) -> dict:
        """
        Get TTS configuration for the frontend.
        This is sent to the browser to configure Web Speech API.
        """
        return {
            "provider": self.provider.value,
            "settings": {
                "lang": "hi-IN",  # Hindi (India) - works well for Hinglish
                "rate": 0.9,      # Slightly slower for clarity
                "pitch": 1.0,
                "volume": 1.0,
            },
            "fallback_lang": "en-IN"  # English (India) as fallback
        }
    
    def generate_ssml(self, text: str) -> str:
        """
        Generate SSML for more natural speech (used with Google TTS).
        """
        # Clean text first
        text = self.prepare_text_for_speech(text)
        
        # Wrap in SSML with pauses for natural flow
        ssml = f"""<speak>
            <prosody rate="95%" pitch="0%">
                {text}
            </prosody>
        </speak>"""
        
        return ssml
    
    def split_for_chunked_speech(self, text: str, max_chars: int = 200) -> list[str]:
        """
        Split long text into chunks for smoother TTS playback.
        Splits at sentence boundaries.
        """
        sentences = []
        current_chunk = ""
        
        # Split by common sentence endings
        parts = text.replace("। ", ".|").replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if len(current_chunk) + len(part) < max_chars:
                current_chunk += " " + part if current_chunk else part
            else:
                if current_chunk:
                    sentences.append(current_chunk.strip())
                current_chunk = part
        
        if current_chunk:
            sentences.append(current_chunk.strip())
        
        return sentences


# Global TTS service instance
tts_service = TTSService()
