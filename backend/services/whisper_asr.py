"""
Whisper ASR (Automatic Speech Recognition) service for SamairaAI.
Converts voice input to text with Hinglish support.
"""

import whisper
import tempfile
import os
import re
from pathlib import Path
from typing import Optional
import numpy as np
import subprocess

from config.settings import settings

# Hinglish vocabulary - English mode romanizes Hindi words cleanly
# Keep this SHORT to avoid Whisper hallucinating from long prompts
HINGLISH_CONTEXT = """Hinglish conversation: mera naam Yash hai, main Bangalore mein rehta hoon, meri salary 1.5 lakh hai, SIP mutual fund investment savings."""

# Sentinel value for unclear audio
UNCLEAR_AUDIO = "[Audio unclear - please try again]"


class WhisperASR:
    """
    Whisper-based speech-to-text service.
    Optimized for Hinglish (Hindi + English) recognition.
    """
    
    def __init__(self):
        self._model = None
        self._model_name = settings.WHISPER_MODEL
        self._initialized = False
    
    def initialize(self):
        """Load the Whisper model."""
        if self._initialized:
            return
        
        print(f"Loading Whisper model: {self._model_name}")
        self._model = whisper.load_model(self._model_name)
        self._initialized = True
        print("Whisper model loaded successfully")
    
    def _clean_hinglish_text(self, text: str) -> str:
        """
        Clean up Hinglish transcription for better readability.
        Fixes common Whisper mistakes and removes hallucinations.
        """
        if not text:
            return text
        
        # CRITICAL: Detect and remove hallucinated repeated words/phrases
        # Whisper often produces "word word word word..." when confused
        words = text.split()
        if len(words) > 3:
            # Check for excessive repetition (same word appearing 3+ times consecutively)
            cleaned_words = []
            prev_word = None
            repeat_count = 0
            for word in words:
                if word == prev_word:
                    repeat_count += 1
                    if repeat_count < 2:  # Allow max 2 consecutive repeats
                        cleaned_words.append(word)
                else:
                    repeat_count = 0
                    cleaned_words.append(word)
                prev_word = word
            text = ' '.join(cleaned_words)
        
        # Check if text is mostly repetitive (hallucination indicator)
        unique_words = set(text.split())
        total_words = len(text.split())
        if total_words > 5 and len(unique_words) < total_words * 0.3:
            # More than 70% repetition - likely hallucination
            return UNCLEAR_AUDIO
        
        # Common Hinglish corrections (Whisper often mishears these)
        corrections = {
            # Numbers in Hindi
            "पन्द्रह": "15", "पंद्रह": "15", "पांच": "5", "पाँच": "5",
            "तीन": "3", "दस": "10", "बीस": "20", "सौ": "100",
            "लाख": "lakh", "करोड़": "crore", "हज़ार": "thousand",
            # Common financial terms
            "एसआईपी": "SIP", "पीपीएफ": "PPF", "एनपीएस": "NPS",
            "एफडी": "FD", "आरडी": "RD", "ईएमआई": "EMI",
            "म्यूचुअल फंड": "mutual fund", "म्युचुअल फंड": "mutual fund",
            # Common phrases that get garbled
            "मैं चाहता": "main chahta", "मैं चाहती": "main chahti",
            "कितना": "kitna", "कैसे": "kaise", "क्या": "kya",
        }
        
        for hindi, replacement in corrections.items():
            text = text.replace(hindi, replacement)
        
        # Remove repeated punctuation
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text.strip()
    
    def _convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convert audio to WAV format using ffmpeg if available."""
        try:
            # Try using ffmpeg for conversion
            result = subprocess.run(
                [
                    'ffmpeg', '-y', '-i', input_path,
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',       # Mono
                    '-f', 'wav',
                    output_path
                ],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (wav, mp3, webm, etc.)
            language: Force specific language (None for auto-detect)
        
        Returns:
            Dict with 'text', 'language', 'segments'
        """
        if not self._initialized:
            self.initialize()
        
        # For webm files, try to convert to wav first
        converted_path = None
        if audio_path.endswith('.webm'):
            converted_path = audio_path.replace('.webm', '_converted.wav')
            if self._convert_to_wav(audio_path, converted_path):
                audio_path = converted_path
        
        try:
            # Transcribe with Hinglish-optimized settings
            # KEY INSIGHT: For code-switched Hindi-English (Hinglish):
            # - Use language=None for auto-detect (handles switching better)
            # - OR use "en" which captures Hindi words in Roman script
            # - Avoid "hi" which forces Devanagari output
            
            result = self._model.transcribe(
                audio_path,
                language="en",  # FORCE ENGLISH - romanizes Hindi words, better for Hinglish
                task="transcribe",
                fp16=False,  # Use FP32 for better accuracy on CPU
                verbose=False,
                initial_prompt=HINGLISH_CONTEXT,
                # Settings to reduce hallucinations
                temperature=0.0,  # Deterministic
                compression_ratio_threshold=2.4,  # Default is 2.4
                logprob_threshold=-1.0,  # Default is -1.0
                no_speech_threshold=0.6,  # Default is 0.6
                condition_on_previous_text=False,  # Prevents hallucination loops
            )
            
            # Clean up the transcribed text
            text = result["text"].strip()
            text = self._clean_hinglish_text(text)
            
            return {
                "text": text,
                "language": result.get("language", "hi"),
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": self._clean_hinglish_text(seg["text"].strip())
                    }
                    for seg in result.get("segments", [])
                ]
            }
        finally:
            # Clean up converted file
            if converted_path and os.path.exists(converted_path):
                try:
                    os.unlink(converted_path)
                except:
                    pass
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        file_extension: str = "wav"
    ) -> dict:
        """
        Transcribe audio from bytes (e.g., from web upload).
        
        Args:
            audio_bytes: Raw audio bytes
            file_extension: Audio format extension
        
        Returns:
            Transcription result dict
        """
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}",
            delete=False
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            result = self.transcribe(tmp_path)
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
        
        return result
    
    def transcribe_numpy(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000
    ) -> dict:
        """
        Transcribe from numpy array.
        
        Args:
            audio_array: Audio as numpy array
            sample_rate: Sample rate (Whisper expects 16000)
        
        Returns:
            Transcription result dict
        """
        if not self._initialized:
            self.initialize()
        
        # Resample if needed
        if sample_rate != 16000:
            # Simple resampling (for production, use librosa)
            ratio = 16000 / sample_rate
            new_length = int(len(audio_array) * ratio)
            audio_array = np.interp(
                np.linspace(0, len(audio_array), new_length),
                np.arange(len(audio_array)),
                audio_array
            )
        
        # Ensure float32
        audio_array = audio_array.astype(np.float32)
        
        # Normalize if needed
        if np.abs(audio_array).max() > 1.0:
            audio_array = audio_array / np.abs(audio_array).max()
        
        result = self._model.transcribe(
            audio_array,
            language="hi",  # Force Hindi for better Hinglish recognition
            fp16=False,
            verbose=False,
            initial_prompt=HINGLISH_CONTEXT,
            temperature=0.0,
            condition_on_previous_text=True,
        )
        
        text = self._clean_hinglish_text(result["text"].strip())
        
        return {
            "text": text,
            "language": result.get("language", "hi"),
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": self._clean_hinglish_text(seg["text"].strip())
                }
                for seg in result.get("segments", [])
            ]
        }


# Global ASR instance
whisper_asr = WhisperASR()
