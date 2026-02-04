"""
Azure Speech TTS Service with SSML and Custom Lexicon
Provides high-quality Hindi/Hinglish pronunciation using:
- Azure Neural Voices (hi-IN and en-IN)
- SSML with phoneme tags for precise pronunciation
- Custom lexicon for financial terms
- Prosody control for natural speech

This is a ground-up approach that doesn't rely on brittle regex phonetic mappings.
"""

import httpx
import base64
import re
import os
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class VoiceConfig:
    """Voice configuration for Azure TTS."""
    name: str
    language: str
    gender: str
    style: str = "friendly"


class AzureTTSService:
    """
    Azure Cognitive Services Speech-to-Text with advanced SSML.
    Uses neural voices with phoneme-level control for Hinglish.
    """
    
    # Azure Neural Voices for Indian languages
    VOICES = {
        # Hindi voices - best for Hinglish pronunciation
        'swara': VoiceConfig('hi-IN-SwaraNeural', 'hi-IN', 'Female', 'friendly'),
        'madhur': VoiceConfig('hi-IN-MadhurNeural', 'hi-IN', 'Male', 'friendly'),
        
        # Indian English voices - good for English-heavy Hinglish
        'neerja': VoiceConfig('en-IN-NeerjaNeural', 'en-IN', 'Female', 'friendly'),
        'prabhat': VoiceConfig('en-IN-PrabhatNeural', 'en-IN', 'Male', 'friendly'),
        
        # Multilingual voice - handles code-switching well
        'ava': VoiceConfig('en-US-AvaMultilingualNeural', 'en-US', 'Female', 'friendly'),
    }
    
    DEFAULT_VOICE = 'swara'  # Hindi female voice - best for Hinglish
    
    # Custom pronunciation lexicon for financial terms and Hindi words
    # Uses IPA (International Phonetic Alphabet) for precise pronunciation
    LEXICON = {
        # Financial terms with Hindi pronunciation
        'SIP': ('sɪp', 'sip'),  # (IPA, fallback text)
        'EMI': ('iː ɛm aɪ', 'ee em aai'),
        'FD': ('ɛf diː', 'eff dee'),
        'RD': ('ɑːr diː', 'aar dee'),
        'PPF': ('piː piː ɛf', 'pee pee eff'),
        'NPS': ('ɛn piː ɛs', 'en pee ess'),
        'ELSS': ('iː ɛl ɛs ɛs', 'ee el ess ess'),
        'KYC': ('keɪ waɪ siː', 'kay why see'),
        'PAN': ('pæn', 'pan'),
        'ITR': ('aɪ tiː ɑːr', 'aai tee aar'),
        'GST': ('dʒiː ɛs tiː', 'jee ess tee'),
        'TDS': ('tiː diː ɛs', 'tee dee ess'),
        
        # Hindi words that need proper pronunciation
        'namaste': ('nəməsteɪ', 'na-mas-tay'),
        'rupaye': ('ruːpəjeɪ', 'roo-pa-yay'),
        'lakh': ('lɑːkʰ', 'laakh'),
        'crore': ('kəroːr', 'ka-rohr'),
        'bachat': ('bətʃət', 'ba-chat'),
        'nivesh': ('nɪveːʃ', 'ni-vesh'),
        'byaj': ('bjɑːdʒ', 'byaaj'),
        'karz': ('kərz', 'karz'),
        'bima': ('biːmɑː', 'bee-maa'),
        
        # Common Hinglish verbs/phrases
        'kijiye': ('kiːdʒijeɪ', 'kee-jee-yay'),
        'chahiye': ('tʃɑːhijeɪ', 'chaa-hee-yay'),
        'dekhiye': ('deːkʰijeɪ', 'day-khee-yay'),
        'samjhiye': ('səmdʒʰijeɪ', 'sam-jhee-yay'),
        'bataiye': ('bətɑːijeɪ', 'ba-taa-ee-yay'),
        
        # Samaira branding
        'Samaira': ('səmaɪrɑː', 'sa-my-raa'),
        'SamairaAI': ('səmaɪrɑː eɪ aɪ', 'sa-my-raa ay ai'),
    }
    
    # Words to speak as individual letters (spell out)
    SPELL_OUT_WORDS = {'SIP', 'EMI', 'FD', 'RD', 'PPF', 'NPS', 'ELSS', 'KYC', 'ITR', 'GST', 'TDS', 'UPI', 'ATM'}
    
    def __init__(self):
        self._api_key = None
        self._region = None
        self._initialized = False
        self._token = None
        self._token_expiry = 0
    
    def initialize(self):
        """Initialize Azure TTS service."""
        if self._initialized:
            return
        
        # Try to get from environment or settings
        self._api_key = os.getenv('AZURE_SPEECH_KEY')
        self._region = os.getenv('AZURE_SPEECH_REGION', 'centralindia')
        
        # Also try from settings module
        try:
            from config.settings import settings
            if hasattr(settings, 'AZURE_SPEECH_KEY') and settings.AZURE_SPEECH_KEY:
                self._api_key = settings.AZURE_SPEECH_KEY
            if hasattr(settings, 'AZURE_SPEECH_REGION') and settings.AZURE_SPEECH_REGION:
                self._region = settings.AZURE_SPEECH_REGION
        except ImportError:
            pass
        
        self._initialized = True
        
        if self._api_key:
            print("[OK] Azure Speech TTS initialized")
        else:
            print("[WARNING] Azure Speech TTS not configured (no API key)")
    
    def is_available(self) -> bool:
        """Check if Azure TTS is configured and available."""
        if not self._initialized:
            self.initialize()
        return bool(self._api_key)
    
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        language: str = 'hinglish'
    ) -> Optional[bytes]:
        """
        Synthesize speech from text using Azure Neural TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice name (swara, madhur, neerja, prabhat)
            language: Target language (hinglish, hindi, english)
        
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        if not self._initialized:
            self.initialize()
        
        if not self._api_key:
            return None
        
        # Select appropriate voice
        voice_config = self._select_voice(voice, language)
        
        # Build SSML
        ssml = self._build_ssml(text, voice_config, language)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1",
                    headers={
                        'Ocp-Apim-Subscription-Key': self._api_key,
                        'Content-Type': 'application/ssml+xml',
                        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
                        'User-Agent': 'SamairaAI'
                    },
                    content=ssml
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"Azure TTS error {response.status_code}: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"Azure TTS error: {e}")
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
    
    def _select_voice(self, voice: str, language: str) -> VoiceConfig:
        """Select the best voice based on preference and language."""
        if voice and voice in self.VOICES:
            return self.VOICES[voice]
        
        # Auto-select based on language
        if language == 'hindi':
            return self.VOICES['swara']
        elif language == 'english':
            return self.VOICES['neerja']
        else:  # hinglish - default to Hindi voice (handles both better)
            return self.VOICES['swara']
    
    def _build_ssml(self, text: str, voice: VoiceConfig, language: str) -> str:
        """
        Build SSML document with phoneme tags and prosody control.
        This is the key to precise pronunciation without regex hacks.
        """
        # Clean text first
        text = self._clean_text(text)
        
        # Apply phoneme substitutions for lexicon words
        text = self._apply_phonemes(text, use_ipa=True)
        
        # Apply number and currency handling
        text = self._handle_numbers_and_currency(text)
        
        # Build SSML
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
    xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{voice.language}">
    <voice name="{voice.name}">
        <mstts:express-as style="{voice.style}">
            <prosody rate="0.95" pitch="+0%">
                {text}
            </prosody>
        </mstts:express-as>
    </voice>
</speak>'''
        
        return ssml
    
    def _clean_text(self, text: str) -> str:
        """Clean text for TTS processing."""
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
        
        # Clean up whitespace
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        return text.strip()
    
    def _apply_phonemes(self, text: str, use_ipa: bool = True) -> str:
        """
        Apply phoneme tags for words in our lexicon.
        Uses SSML <phoneme> tag for precise pronunciation.
        """
        for word, (ipa, fallback) in self.LEXICON.items():
            # Case-insensitive replacement with word boundaries
            pattern = rf'\b{re.escape(word)}\b'
            
            if use_ipa:
                # Use IPA phoneme tag
                replacement = f'<phoneme alphabet="ipa" ph="{ipa}">{word}</phoneme>'
            else:
                # Use phonetic spelling as text
                replacement = fallback
            
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Handle spell-out acronyms that aren't in lexicon
        for acronym in self.SPELL_OUT_WORDS:
            if acronym not in self.LEXICON:
                pattern = rf'\b{re.escape(acronym)}\b'
                # Spell out with say-as tag
                replacement = f'<say-as interpret-as="characters">{acronym}</say-as>'
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _handle_numbers_and_currency(self, text: str) -> str:
        """Handle numbers, currency, and percentages with say-as tags."""
        
        # Currency: ₹50,000 -> speak as currency
        text = re.sub(
            r'₹\s*([\d,]+(?:\.\d+)?)',
            r'<say-as interpret-as="currency" language="hi-IN">INR \1</say-as>',
            text
        )
        
        # Rs./Rs -> rupees
        text = re.sub(r'\bRs\.?\s*', 'rupees ', text, flags=re.IGNORECASE)
        
        # Percentages
        text = re.sub(
            r'(\d+(?:\.\d+)?)\s*%',
            r'<say-as interpret-as="cardinal">\1</say-as> percent',
            text
        )
        
        # Large numbers with lakh/crore context
        text = re.sub(
            r'(\d{1,2})\s*lakh',
            r'<say-as interpret-as="cardinal">\1</say-as> <phoneme alphabet="ipa" ph="lɑːkʰ">lakh</phoneme>',
            text,
            flags=re.IGNORECASE
        )
        
        text = re.sub(
            r'(\d{1,2})\s*crore',
            r'<say-as interpret-as="cardinal">\1</say-as> <phoneme alphabet="ipa" ph="kəroːr">crore</phoneme>',
            text,
            flags=re.IGNORECASE
        )
        
        return text
    
    def add_lexicon_word(self, word: str, ipa: str, fallback: str):
        """Add a word to the runtime lexicon."""
        self.LEXICON[word] = (ipa, fallback)
    
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


# Global instance
azure_tts = AzureTTSService()
