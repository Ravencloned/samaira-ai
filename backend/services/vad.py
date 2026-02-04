"""
Voice Activity Detection (VAD) service using WebRTC VAD.
Detects speech vs silence for turn-taking in conversations.
"""

import numpy as np
from typing import Optional

from config.settings import settings


class VADService:
    """
    WebRTC VAD wrapper for detecting speech segments.
    Lightweight and cross-platform (Windows/Linux/Mac).
    """
    
    def __init__(self):
        self._vad = None
        self._aggressiveness = settings.VAD_AGGRESSIVENESS
        self._initialized = False
    
    def initialize(self):
        """Initialize WebRTC VAD."""
        if self._initialized:
            return
        
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad(self._aggressiveness)
            self._initialized = True
            print(f"[OK] VAD: WebRTC (aggressiveness={self._aggressiveness})")
        except ImportError:
            # Only log once by marking as initialized
            self._initialized = True
            print("[WARNING] webrtcvad not installed. VAD disabled - run: pip install webrtcvad")
            self._vad = None
        except Exception as e:
            self._initialized = True
            print(f"[WARNING] VAD initialization failed: {e}")
            self._vad = None
    
    def is_speech(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000
    ) -> bool:
        """
        Check if audio chunk contains speech.
        
        Args:
            audio_chunk: PCM audio bytes (16-bit signed int)
            sample_rate: Sample rate (must be 8000, 16000, 32000, or 48000)
        
        Returns:
            True if speech detected, False if silence
        """
        if not self._initialized:
            self.initialize()
        
        if self._vad is None:
            # No VAD available, assume speech
            return True
        
        try:
            # WebRTC VAD requires specific sample rates and frame durations
            # Frame duration must be 10, 20, or 30 ms
            # For 16000 Hz and 30ms: 480 samples = 960 bytes
            return self._vad.is_speech(audio_chunk, sample_rate)
        except Exception as e:
            print(f"[WARNING] VAD error: {e}")
            return True  # Default to speech on error
    
    def process_audio_buffer(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30
    ) -> list[tuple[float, float, bool]]:
        """
        Process audio buffer and return speech/silence segments.
        
        Args:
            audio_data: Audio as int16 numpy array
            sample_rate: Sample rate in Hz
            frame_duration_ms: Frame duration (10, 20, or 30 ms)
        
        Returns:
            List of (start_time, end_time, is_speech) tuples
        """
        if not self._initialized:
            self.initialize()
        
        if self._vad is None:
            # No VAD, return entire buffer as speech
            duration = len(audio_data) / sample_rate
            return [(0.0, duration, True)]
        
        # Calculate frame size
        frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        segments = []
        current_segment_start = None
        current_is_speech = None
        
        # Process frames
        for i in range(0, len(audio_data), frame_size):
            frame = audio_data[i:i + frame_size]
            
            # Pad last frame if needed
            if len(frame) < frame_size:
                frame = np.pad(frame, (0, frame_size - len(frame)), mode='constant')
            
            # Convert to bytes
            frame_bytes = frame.astype(np.int16).tobytes()
            
            # Check for speech
            try:
                is_speech = self._vad.is_speech(frame_bytes, sample_rate)
            except:
                is_speech = True  # Default to speech on error
            
            # Calculate time
            time_sec = i / sample_rate
            
            # Track segments
            if current_is_speech is None:
                # Start first segment
                current_segment_start = time_sec
                current_is_speech = is_speech
            elif is_speech != current_is_speech:
                # Segment boundary
                segments.append((current_segment_start, time_sec, current_is_speech))
                current_segment_start = time_sec
                current_is_speech = is_speech
        
        # Close final segment
        if current_segment_start is not None:
            final_time = len(audio_data) / sample_rate
            segments.append((current_segment_start, final_time, current_is_speech))
        
        return segments
    
    def filter_silence(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30
    ) -> np.ndarray:
        """
        Remove silence from audio, keep only speech segments.
        
        Args:
            audio_data: Audio as int16 numpy array
            sample_rate: Sample rate
            frame_duration_ms: Frame duration
        
        Returns:
            Filtered audio with silence removed
        """
        segments = self.process_audio_buffer(audio_data, sample_rate, frame_duration_ms)
        
        # Extract speech frames
        speech_frames = []
        for start, end, is_speech in segments:
            if is_speech:
                start_idx = int(start * sample_rate)
                end_idx = int(end * sample_rate)
                speech_frames.append(audio_data[start_idx:end_idx])
        
        if not speech_frames:
            # No speech detected, return empty
            return np.array([], dtype=audio_data.dtype)
        
        # Concatenate speech segments
        return np.concatenate(speech_frames)


# Global VAD instance
vad_service = VADService()
