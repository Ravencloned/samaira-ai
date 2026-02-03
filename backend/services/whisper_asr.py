"""
Whisper ASR (Automatic Speech Recognition) service for SamairaAI.
Converts voice input to text with Hinglish support.
"""

import whisper
import tempfile
import os
from pathlib import Path
from typing import Optional
import numpy as np
import subprocess

from config.settings import settings


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
            # Using initial_prompt to bias towards Hindi/English mix
            result = self._model.transcribe(
                audio_path,
                language=language,  # None = auto-detect (good for Hinglish)
                task="transcribe",
                fp16=False,  # Use FP32 for better accuracy on CPU
                verbose=False,
                # Initial prompt to help with Hinglish context
                initial_prompt="Namaste, main Hinglish mein baat kar raha hoon. Financial planning, SIP, PPF, mutual funds ke baare mein.",
            )
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
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
            fp16=False,
            verbose=False
        )
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                }
                for seg in result.get("segments", [])
            ]
        }


# Global ASR instance
whisper_asr = WhisperASR()
