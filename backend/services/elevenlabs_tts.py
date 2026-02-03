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
        "elli": "MF3mGyEYCl7XYWbV9V6O",    # Middle-aged female - best for masi vibe
        "sarah": "EXAVITQu4vr4xnSDxMaL",   # Clear female
    }
    
    DEFAULT_VOICE = "elli"  # Warmer, more aunt-like for Indian context
    
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
                            "stability": 0.35,       # Lower = more expressive, natural variation
                            "similarity_boost": 0.70, # Slightly lower for natural speech
                            "style": 0.45,           # Higher = more personality and warmth
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
    
    # Comprehensive Hindi/Hinglish pronunciation dictionary
    PHONETIC_CORRECTIONS = {
        # Common Hindi verbs and phrases
        'hai': 'hay',
        'hain': 'hain',
        'mein': 'main',
        'hoti': 'ho-tee',
        'hota': 'ho-taa',
        'kijiye': 'kee-jee-yay',
        'chahiye': 'chaa-hee-yay',
        'karein': 'ka-rain',
        'karna': 'kar-naa',
        'karo': 'ka-ro',
        'sakti': 'sak-tee',
        'sakta': 'sak-taa',
        'sakte': 'sak-tay',
        'milta': 'mil-taa',
        'milti': 'mil-tee',
        'milne': 'mil-nay',
        
        # Pronouns and possessives
        'aapka': 'aap-kaa',
        'aapki': 'aap-kee',
        'aapko': 'aap-ko',
        'tumhare': 'tum-haa-ray',
        'tumhari': 'tum-haa-ree',
        'mera': 'may-raa',
        'meri': 'may-ree',
        
        # Question words
        'kaise': 'kai-say',
        'kya': 'kyaa',
        'kahan': 'ka-haan',
        'kaun': 'kaun',
        'kitna': 'kit-naa',
        'kitne': 'kit-nay',
        
        # Common adjectives
        'bahut': 'ba-hut',
        'accha': 'ach-chaa',
        'achha': 'ach-chaa',
        'acha': 'ach-chaa',
        'bada': 'ba-daa',
        'badi': 'ba-dee',
        'chota': 'cho-taa',
        'choti': 'cho-tee',
        'safal': 'sa-fal',
        'asafal': 'a-sa-fal',
        
        # Financial terms in Hindi
        'paisa': 'pai-saa',
        'paise': 'pai-say',
        'rupaye': 'ru-pa-yay',
        'rupiya': 'ru-pee-yaa',
        'bachat': 'ba-chat',
        'nivesh': 'ni-vesh',
        'faayda': 'faa-ee-daa',
        'fayda': 'faa-ee-daa',
        'nuksaan': 'nuk-saan',
        'nuksan': 'nuk-saan',
        'byaj': 'byaaj',
        'dhan': 'dhan',
        'sampatti': 'sam-pat-tee',
        'karz': 'karz',
        'rin': 'rin',
        'bima': 'bee-maa',
        
        # Greetings and polite words
        'namaste': 'na-mas-tay',
        'namaskar': 'na-mas-kaar',
        'dhanyavaad': 'dhan-ya-vaad',
        'shukriya': 'shuk-ri-yaa',
        'kripya': 'krip-yaa',
        
        # Common conversation words
        'dekho': 'day-kho',
        'dekh': 'daykh',
        'suno': 'su-no',
        'bolo': 'bo-lo',
        'batao': 'ba-taa-o',
        'bataiye': 'ba-taa-ee-yay',
        'samjho': 'sam-jho',
        'samjhiye': 'sam-jhi-yay',
        'sochiye': 'so-chi-yay',
        'socho': 'so-cho',
        
        # Connectors
        'aur': 'aur',
        'ya': 'yaa',
        'lekin': 'lay-kin',
        'magar': 'ma-gar',
        'isliye': 'is-li-yay',
        'kyunki': 'kyun-ki',
        'agar': 'a-gar',
        'toh': 'toh',
        'to': 'toh',
        'phir': 'phir',
        'matlab': 'mat-lab',
        'yaani': 'yaa-nee',
        'jaise': 'jai-say',
        'jab': 'jab',
        'tab': 'tab',
        
        # Time-related
        'pehle': 'peh-lay',
        'baad': 'baad',
        'abhi': 'ab-hee',
        'jaldi': 'jal-dee',
        'dheere': 'dhee-ray',
        'hamesha': 'ha-may-shaa',
        'kabhi': 'kab-hee',
        'saal': 'saal',
        'mahina': 'ma-hee-naa',
        'hafte': 'haf-tay',
        
        # Emotion/reaction words
        'wah': 'waah',
        'arre': 'ar-ray',
        'haan': 'haan',
        'nahi': 'na-hee',
        'nahin': 'na-heen',
        'bilkul': 'bil-kul',
        'zaroor': 'za-roor',
        'zaruri': 'za-roo-ree',
        'shayad': 'shaa-yad',
        
        # Relationship words  
        'beta': 'bay-taa',
        'beti': 'bay-tee',
        'bhai': 'bhaai',
        'behen': 'be-hen',
        'didi': 'dee-dee',
        'masi': 'maa-see',
        'chacha': 'chaa-chaa',
        'dada': 'daa-daa',
        'dadi': 'daa-dee',
        'nana': 'naa-naa',
        'nani': 'naa-nee',
        'parivaar': 'pa-ri-vaar',
        'bachche': 'bach-chay',
        'bachchi': 'bach-chee',
        
        # Financial advice phrases
        'salah': 'sa-laah',
        'sujhav': 'suj-haav',
        'sambhavana': 'sam-bhaa-va-naa',
        'suraksha': 'su-rak-shaa',
        'lakshya': 'laksh-ya',
        
        # Numbers in Hindi
        'ek': 'ayk',
        'do': 'doh',
        'teen': 'teen',
        'char': 'chaar',
        'paanch': 'paanch',
        'das': 'das',
        'bees': 'bees',
        'pachaas': 'pa-chaas',
        'sau': 'sau',
        'hazaar': 'ha-zaar',
        
        # Brand name
        'Samaira': 'Sa-mai-raa',
        'SamairaAI': 'Sa-mai-raa A I',
    }
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for natural, human-like TTS pronunciation."""
        
        # Step 1: Remove ALL emojis (this fixes the robot-reading-emoji issue)
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Misc symbols, pictographs
        text = re.sub(r'[\U00002600-\U000026FF]', '', text)  # Misc symbols
        text = re.sub(r'[\U00002700-\U000027BF]', '', text)  # Dingbats
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport symbols
        text = re.sub(r'[\U0001FA00-\U0001FAFF]', '', text)  # Chess, symbols
        
        # Step 2: Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Headers
        text = re.sub(r'^[-*•]\s*', '', text, flags=re.MULTILINE)  # Bullets
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)  # Numbered lists
        
        # Step 3: Apply Hindi phonetic corrections
        for word, phonetic in self.PHONETIC_CORRECTIONS.items():
            # Case-insensitive word boundary replacement
            text = re.sub(rf'\b{re.escape(word)}\b', phonetic, text, flags=re.IGNORECASE)
        
        # Step 4: Fix acronyms and financial terms
        acronym_fixes = {
            'SIP': 'sip',
            'RD': 'aar dee',
            'FD': 'eff dee',
            'PPF': 'pee pee eff',
            'NPS': 'en pee ess',
            'EMI': 'ee em aai',
            'ELSS': 'ee el es es',
            'ITR': 'aai tee aar',
            'TDS': 'tee dee es',
            'GST': 'jee es tee',
            'PAN': 'pan card',
            'KYC': 'kay why see',
            'SSY': 'sukanya samridhi yojana',
            'EPF': 'ee pee eff',
            'PMJDY': 'pradhan mantri jan dhan yojana',
        }
        for acronym, spoken in acronym_fixes.items():
            text = re.sub(rf'\b{acronym}\b', spoken, text)
        
        # Step 5: Fix symbols and numbers
        text = text.replace('₹', 'rupees ')
        text = text.replace('Rs.', 'rupees ')
        text = text.replace('Rs', 'rupees ')
        text = text.replace('%', ' percent')
        text = text.replace('&', ' and ')
        text = re.sub(r'\blakh\b', 'laakh', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcrore\b', 'karor', text, flags=re.IGNORECASE)
        
        # Step 6: Add natural pauses for conversational flow
        # Add slight pause after certain words for natural breathing
        pause_after = ['Dekho,', 'Haan,', 'Accha,', 'Toh,', 'Actually,']
        for word in pause_after:
            text = text.replace(word, word + '..')
        
        # Step 7: Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_available(self) -> bool:
        """Check if ElevenLabs is configured."""
        if not self._initialized:
            self.initialize()
        return bool(self._api_key)


# Global instance
elevenlabs_tts = ElevenLabsTTS()
