"""
Text-to-Speech service for SamairaAI.
Supports multiple providers:
1. Edge TTS (FREE! Same quality as Azure, no API key needed)
2. Azure Neural TTS (SSML + phonemes, requires API key)
3. ElevenLabs (natural voices, requires API key)
4. Browser TTS (fallback, uses Web Speech API)
"""

from typing import Optional
from enum import Enum


class TTSProvider(str, Enum):
    """Available TTS providers in order of preference."""
    EDGE = "edge"        # Edge TTS - FREE neural voices (RECOMMENDED)
    AZURE = "azure"      # Azure Neural TTS with SSML
    ELEVENLABS = "elevenlabs"  # ElevenLabs natural voices
    BROWSER = "browser"  # Web Speech API fallback


class TTSService:
    """
    Unified Text-to-Speech service with multiple providers.
    Priority: Edge (FREE) > Azure > ElevenLabs > Browser
    """
    
    def __init__(self):
        self._edge_tts = None
        self._azure_tts = None
        self._elevenlabs_tts = None
        self._initialized = False
        self._preferred_provider = TTSProvider.EDGE
    
    def initialize(self):
        """Initialize TTS providers."""
        if self._initialized:
            return
        
        # Try Edge TTS first - FREE and high quality!
        try:
            from services.edge_tts_service import edge_tts_service
            edge_tts_service.initialize()
            if edge_tts_service.is_available():
                self._edge_tts = edge_tts_service
                self._preferred_provider = TTSProvider.EDGE
                print("[OK] TTS Provider: Edge (FREE neural voices)")
        except ImportError as e:
            print(f"[WARNING] Edge TTS not available: {e}")
        
        # Try Azure as backup (if API key configured)
        try:
            from services.azure_tts import azure_tts
            azure_tts.initialize()
            if azure_tts.is_available():
                self._azure_tts = azure_tts
                if not self._edge_tts:
                    self._preferred_provider = TTSProvider.AZURE
                    print("[OK] TTS Provider: Azure Neural")
        except ImportError:
            pass
        
        # Try ElevenLabs as another backup
        try:
            from services.elevenlabs_tts import elevenlabs_tts
            elevenlabs_tts.initialize()
            if elevenlabs_tts.is_available():
                self._elevenlabs_tts = elevenlabs_tts
                if not self._edge_tts and not self._azure_tts:
                    self._preferred_provider = TTSProvider.ELEVENLABS
                    print("[OK] TTS Provider: ElevenLabs")
        except ImportError:
            pass
        
        # Browser fallback is always available
        if not self._edge_tts and not self._azure_tts and not self._elevenlabs_tts:
            self._preferred_provider = TTSProvider.BROWSER
            print("[OK] TTS Provider: Browser (Web Speech API)")
        
        self._initialized = True
    
    async def synthesize(
        self,
        text: str,
        provider: Optional[TTSProvider] = None,
        voice: str = None
    ) -> Optional[dict]:
        """
        Synthesize speech from text.
        
        Returns:
            dict with 'audio' (base64), 'provider', 'voice' or None
        """
        if not self._initialized:
            self.initialize()
        
        provider = provider or self._preferred_provider
        
        # Try Edge TTS first (FREE!)
        if (provider == TTSProvider.EDGE or provider is None) and self._edge_tts:
            audio = await self._edge_tts.synthesize_base64(text, voice)
            if audio:
                return {
                    'audio': audio,
                    'provider': 'edge',
                    'voice': voice or 'swara',
                    'format': 'mp3'
                }
        
        # Try Azure if configured
        if (provider == TTSProvider.AZURE) and self._azure_tts:
            audio = await self._azure_tts.synthesize_base64(text, voice)
            if audio:
                return {
                    'audio': audio,
                    'provider': 'azure',
                    'voice': voice or 'swara',
                    'format': 'mp3'
                }
        
        # Fallback to ElevenLabs
        if (provider == TTSProvider.ELEVENLABS or (self._edge_tts is None and self._azure_tts is None)) and self._elevenlabs_tts:
            audio = await self._elevenlabs_tts.synthesize_base64(text)
            if audio:
                return {
                    'audio': audio,
                    'provider': 'elevenlabs',
                    'voice': 'elli',
                    'format': 'mp3'
                }
        
        # Return None to signal browser should handle TTS
        return None
    
    def get_provider_info(self) -> dict:
        """Get info about available TTS providers."""
        if not self._initialized:
            self.initialize()
        
        providers = []
        
        if self._edge_tts:
            providers.append({
                'name': 'edge',
                'available': True,
                'voices': self._edge_tts.get_available_voices(),
                'features': ['neural', 'hinglish', 'free', 'no-api-key']
            })
        
        if self._azure_tts:
            providers.append({
                'name': 'azure',
                'available': True,
                'voices': self._azure_tts.get_available_voices(),
                'features': ['ssml', 'phonemes', 'neural', 'hinglish']
            })
        
        if self._elevenlabs_tts:
            providers.append({
                'name': 'elevenlabs',
                'available': True,
                'features': ['natural', 'emotional']
            })
        
        providers.append({
            'name': 'browser',
            'available': True,
            'features': ['offline', 'no-api-key']
        })
        
        return {
            'preferred': self._preferred_provider.value,
            'providers': providers
        }
    
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
            "provider": self._preferred_provider.value,
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
