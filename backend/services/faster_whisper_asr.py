"""
Faster-Whisper ASR service for low-latency Hinglish transcription.
Uses CTranslate2 for optimized inference on CPU/GPU.
"""

import tempfile
import os
import subprocess
from pathlib import Path
from typing import Optional, Generator
import numpy as np

from config.settings import settings

# Short prompt - long prompts cause hallucinations
HINGLISH_CONTEXT = """Financial discussion. Terms: SIP, mutual fund, PPF, lakh, crore, savings, invest, EMI, Bangalore, Mumbai."""


class FasterWhisperASR:
    """
    Faster-Whisper ASR with optimized inference for real-time Hinglish.
    Much faster than openai-whisper on CPU, supports streaming.
    """
    
    def __init__(self):
        self._model = None
        self._model_name = settings.FASTER_WHISPER_MODEL
        self._device = settings.FASTER_WHISPER_DEVICE
        self._compute_type = settings.FASTER_WHISPER_COMPUTE_TYPE
        self._initialized = False
    
    def _filter_hallucinations(self, text: str) -> str:
        """
        Filter out hallucinated/repetitive text from Whisper output.
        Common issue: Whisper produces "word word word word..." when confused.
        """
        if not text or len(text) < 10:
            return text
        
        words = text.split()
        if len(words) < 3:
            return text
        
        # Remove consecutive duplicate words (keep max 2)
        cleaned_words = []
        prev_word = None
        repeat_count = 0
        
        for word in words:
            word_lower = word.lower().strip('.,!?')
            if word_lower == prev_word:
                repeat_count += 1
                if repeat_count < 2:  # Allow max 1 repeat
                    cleaned_words.append(word)
            else:
                repeat_count = 0
                cleaned_words.append(word)
            prev_word = word_lower
        
        text = ' '.join(cleaned_words)
        
        # Check for overall repetitiveness (hallucination indicator)
        unique_words = set(w.lower().strip('.,!?') for w in text.split())
        total_words = len(text.split())
        
        if total_words > 5 and len(unique_words) < total_words * 0.25:
            # More than 75% repetition - definitely hallucination
            return "[Audio unclear - please speak again]"
        
        if total_words > 10 and len(unique_words) < total_words * 0.35:
            # More than 65% repetition - likely hallucination
            return "[Could not understand clearly - please try again]"
        
        return text.strip()
    
    def initialize(self):
        """Load the faster-whisper model."""
        if self._initialized:
            return
        
        try:
            from faster_whisper import WhisperModel
            
            print(f"Loading Faster-Whisper model: {self._model_name} ({self._device}, {self._compute_type})")
            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
                download_root=None,  # Use default cache
                local_files_only=False
            )
            self._initialized = True
            print(f"✓ Faster-Whisper loaded: {self._model_name}")
        except ImportError:
            print("[ERROR] faster-whisper not installed. Run: pip install faster-whisper")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to load Faster-Whisper: {e}")
            raise
    
    def _convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convert audio to 16kHz mono WAV using ffmpeg."""
        try:
            result = subprocess.run(
                [
                    'ffmpeg', '-y', '-i', input_path,
                    '-ar', '16000',  # 16kHz
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
        language: Optional[str] = None,
        return_segments: bool = False
    ) -> dict:
        """
        Transcribe audio file with faster-whisper.
        
        Args:
            audio_path: Path to audio file
            language: Force language (None=auto, 'hi'=Hindi for Hinglish)
            return_segments: Include detailed segments with timestamps
        
        Returns:
            Dict with 'text', 'language', optionally 'segments'
        """
        if not self._initialized:
            self.initialize()
        
        # Convert non-WAV to 16kHz mono WAV
        converted_path = None
        if not audio_path.endswith('.wav'):
            converted_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
            if not self._convert_to_wav(audio_path, converted_path):
                print(f"[WARNING] Could not convert {audio_path}, trying direct transcription")
            else:
                audio_path = converted_path
        
        try:
            # Transcribe with settings to REDUCE hallucinations
            # Use English - Whisper handles Hindi words better in English mode
            # This dramatically reduces repetitive hallucinations
            segments, info = self._model.transcribe(
                audio_path,
                language=language if language else "en",  # English mode for Hinglish
                task="transcribe",
                beam_size=5,
                best_of=5,
                temperature=0.0,  # Deterministic - no randomness
                condition_on_previous_text=False,  # CRITICAL: prevents hallucination loops
                initial_prompt=HINGLISH_CONTEXT,
                vad_filter=True,  # Filter out silence/noise
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=300,  # Minimum speech to transcribe
                    min_silence_duration_ms=500,  # Minimum silence to split
                ),
                compression_ratio_threshold=2.0,  # Lower = stricter hallucination filter
                log_prob_threshold=-0.5,  # Higher = stricter, filters low confidence
                no_speech_threshold=0.5,  # Higher = stricter silence detection
            )
            
            # Collect segments
            text_parts = []
            segment_list = []
            
            for segment in segments:
                text_parts.append(segment.text)
                if return_segments:
                    segment_list.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip()
                    })
            
            full_text = " ".join(text_parts).strip()
            
            # CRITICAL: Filter hallucinated/repetitive text
            full_text = self._filter_hallucinations(full_text)
            
            result = {
                "text": full_text,
                "language": info.language if info else "unknown",
                "language_probability": info.language_probability if info else 0.0
            }
            
            if return_segments:
                result["segments"] = segment_list
            
            return result
            
        finally:
            # Cleanup converted file
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
        Transcribe audio from bytes (e.g., web upload).
        
        Args:
            audio_bytes: Raw audio bytes
            file_extension: Format extension
        
        Returns:
            Transcription dict
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
            os.unlink(tmp_path)
        
        return result
    
    def transcribe_numpy(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000
    ) -> dict:
        """
        Transcribe from numpy array (streaming use case).
        
        Args:
            audio_array: Audio as float32 numpy array
            sample_rate: Sample rate (must be 16000 for Whisper)
        
        Returns:
            Transcription dict
        """
        if not self._initialized:
            self.initialize()
        
        # Ensure 16000 Hz
        if sample_rate != 16000:
            raise ValueError(f"Sample rate must be 16000 Hz for Whisper, got {sample_rate}")
        
        # Ensure float32 and normalized
        audio_array = audio_array.astype(np.float32)
        if np.abs(audio_array).max() > 1.0:
            audio_array = audio_array / np.abs(audio_array).max()
        
        # Transcribe directly from numpy array (faster-whisper supports this)
        segments, info = self._model.transcribe(
            audio_array,
            language=None,  # Auto-detect for Hinglish
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            initial_prompt=HINGLISH_CONTEXT,
            vad_filter=True,
        )
        
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
        
        full_text = " ".join(text_parts).strip()
        
        return {
            "text": full_text,
            "language": info.language if info else "unknown",
            "language_probability": info.language_probability if info else 0.0
        }
    
    def transcribe_stream(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000
    ) -> Generator[dict, None, None]:
        """
        Stream transcription results segment-by-segment (for real-time).
        
        Yields:
            Dict with 'text', 'start', 'end', 'is_final' for each segment
        """
        if not self._initialized:
            self.initialize()
        
        # Ensure proper format
        if sample_rate != 16000:
            raise ValueError(f"Sample rate must be 16000 Hz, got {sample_rate}")
        
        audio_array = audio_array.astype(np.float32)
        if np.abs(audio_array).max() > 1.0:
            audio_array = audio_array / np.abs(audio_array).max()
        
        # Stream segments
        segments, info = self._model.transcribe(
            audio_array,
            language=None,
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            initial_prompt=HINGLISH_CONTEXT,
            vad_filter=True,
        )
        
        for segment in segments:
            yield {
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end,
                "is_final": True  # Each segment is final in faster-whisper
            }


# Global instance
faster_whisper_asr = FasterWhisperASR()
