"""
Edge TTS Service - FREE Neural Text-to-Speech
Uses Microsoft Edge's TTS API - same quality as Azure but NO API KEY required!

Features:
- High-quality neural voices (same as Azure)
- Hindi voices (Swara, Madhur) for perfect Hinglish
- Indian English voices (Neerja, Prabhat)
- SSML support for pronunciation control
- Completely FREE with no limits
"""

import edge_tts
import asyncio
import base64
import re
import io
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class VoiceConfig:
    """Voice configuration."""
    name: str
    language: str
    gender: str


class EdgeTTSService:
    """
    FREE Text-to-Speech using Microsoft Edge's neural voices.
    No API key required - uses the same voices as Azure Speech.
    """
    
    # Available Indian voices (same quality as Azure!)
    VOICES = {
        # Hindi voices - BEST for Hinglish
        'swara': VoiceConfig('hi-IN-SwaraNeural', 'hi-IN', 'Female'),
        'madhur': VoiceConfig('hi-IN-MadhurNeural', 'hi-IN', 'Male'),
        
        # Indian English voices
        'neerja': VoiceConfig('en-IN-NeerjaNeural', 'en-IN', 'Female'),
        'prabhat': VoiceConfig('en-IN-PrabhatNeural', 'en-IN', 'Male'),
        
        # Alternative voices
        'ava': VoiceConfig('en-US-AvaNeural', 'en-US', 'Female'),
        'guy': VoiceConfig('en-US-GuyNeural', 'en-US', 'Male'),
    }
    
    DEFAULT_VOICE = 'swara'  # Hindi female - best for Hinglish
    
    # Custom pronunciation mappings for financial terms
    # Edge TTS handles Hindi well, but we help with acronyms
    PRONUNCIATION_FIXES = {
        # Spell out acronyms for clarity
        'SIP': 'S I P',
        'EMI': 'E M I',
        'FD': 'F D',
        'RD': 'R D',
        'PPF': 'P P F',
        'NPS': 'N P S',
        'ELSS': 'E L S S',
        'KYC': 'K Y C',
        'PAN': 'PAN card',
        'ITR': 'I T R',
        'GST': 'G S T',
        'TDS': 'T D S',
        'UPI': 'U P I',
        'ATM': 'A T M',
        'NEFT': 'N E F T',
        'RTGS': 'R T G S',
        'IMPS': 'I M P S',
        
        # Brand names
        'SamairaAI': 'Samaira A I',
        
        # Numbers with units (helps Hindi voice)
        '₹': 'rupees ',
        'Rs.': 'rupees ',
        'Rs': 'rupees ',
    }
    
    def __init__(self):
        self._initialized = False
    
    def initialize(self):
        """Initialize the Edge TTS service."""
        if self._initialized:
            return
        self._initialized = True
        print("[OK] Edge TTS: Ready (FREE neural voices)")
    
    def is_available(self) -> bool:
        """Edge TTS is always available - no API key needed!"""
        return True
    
    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for TTS."""
        # Remove emojis
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
        text = re.sub(r'[\U00002600-\U000026FF]', '', text)
        text = re.sub(r'[\U00002700-\U000027BF]', '', text)
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)
        text = re.sub(r'[\U0001FA00-\U0001FAFF]', '', text)
        
        # Remove markdown
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-*•]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Apply pronunciation fixes
        for original, replacement in self.PRONUNCIATION_FIXES.items():
            # Case-insensitive for acronyms, case-sensitive for symbols
            if original.isupper() or len(original) <= 3:
                pattern = rf'\b{re.escape(original)}\b'
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            else:
                text = text.replace(original, replacement)
        
        # Handle percentages
        text = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', text)
        
        # Handle lakh/crore numbers
        text = re.sub(r'(\d+)\s*lakh', r'\1 lakh', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*crore', r'\1 crore', text, flags=re.IGNORECASE)
        
        # Clean up whitespace
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _select_voice(self, voice: str = None, language: str = 'hinglish') -> VoiceConfig:
        """Select the best voice."""
        if voice and voice in self.VOICES:
            return self.VOICES[voice]
        
        # Auto-select based on language preference
        if language == 'english':
            return self.VOICES['neerja']
        elif language == 'hindi':
            return self.VOICES['swara']
        else:  # hinglish - use Hindi voice (handles both well)
            return self.VOICES['swara']
    
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        language: str = 'hinglish',
        rate: str = '-5%',  # Slightly slower for clarity
        pitch: str = '+0Hz'
    ) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (swara, madhur, neerja, prabhat)
            language: Target language (hinglish, hindi, english)
            rate: Speech rate adjustment (e.g., '-10%', '+20%')
            pitch: Pitch adjustment (e.g., '+10Hz', '-5Hz')
        
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        if not self._initialized:
            self.initialize()
        
        # Clean text
        clean_text = self._clean_text(text)
        
        if not clean_text:
            return None
        
        # Select voice
        voice_config = self._select_voice(voice, language)
        
        try:
            # Create communicate instance
            communicate = edge_tts.Communicate(
                clean_text,
                voice_config.name,
                rate=rate,
                pitch=pitch
            )
            
            # Collect audio chunks
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            if audio_chunks:
                return b''.join(audio_chunks)
            return None
            
        except Exception as e:
            print(f"Edge TTS error: {e}")
            return None
    
    async def synthesize_base64(
        self,
        text: str,
        voice: str = None,
        language: str = 'hinglish'
    ) -> Optional[str]:
        """Synthesize and return as base64 string."""
        audio_bytes = await self.synthesize(text, voice, language)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        language: str = 'hinglish'
    ) -> bool:
        """Save synthesized speech to a file."""
        audio_bytes = await self.synthesize(text, voice, language)
        if audio_bytes:
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            return True
        return False
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices."""
        return [
            {
                'id': key,
                'name': config.name,
                'language': config.language,
                'gender': config.gender
            }
            for key, config in self.VOICES.items()
        ]
    
    @staticmethod
    async def list_all_voices() -> List[Dict]:
        """List all available Edge TTS voices (for debugging)."""
        voices = await edge_tts.list_voices()
        # Filter for Indian languages
        indian_voices = [v for v in voices if 'IN' in v['Locale']]
        return indian_voices


# Global instance
edge_tts_service = EdgeTTSService()
