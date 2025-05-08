"""
Audio preprocessing module for speech recognition.
"""
import logging
import numpy as np
from typing import Tuple, List

from config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio preprocessing for speech recognition."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.sample_rate = settings.ASR_SAMPLE_RATE
        self.channels = settings.ASR_CHANNELS
        self.chunk_size = settings.ASR_CHUNK_SIZE
        
    def preprocess(self, audio_data: bytes) -> bytes:
        """
        Preprocess audio data for ASR.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            bytes: Preprocessed audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Reshape for multi-channel audio
            audio_array = audio_array.reshape(-1, self.channels)
            
            # Apply noise reduction
            audio_array = self._reduce_noise(audio_array)
            
            # Normalize audio
            audio_array = self._normalize_audio(audio_array)
            
            # Convert back to bytes
            return audio_array.tobytes()
            
        except Exception as e:
            logger.error(f"Audio preprocessing error: {str(e)}")
            raise
    
    def _reduce_noise(self, audio_array: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction to audio data.
        
        Args:
            audio_array: Audio data as numpy array
            
        Returns:
            np.ndarray: Noise-reduced audio data
        """
        # Simple noise gate
        threshold = np.std(audio_array) * 0.5
        audio_array[np.abs(audio_array) < threshold] = 0
        
        return audio_array
    
    def _normalize_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """
        Normalize audio data to prevent clipping.
        
        Args:
            audio_array: Audio data as numpy array
            
        Returns:
            np.ndarray: Normalized audio data
        """
        # Normalize to prevent clipping
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            audio_array = audio_array / max_val * 32767
        
        return audio_array.astype(np.int16)
    
    def split_into_chunks(self, audio_data: bytes) -> List[bytes]:
        """
        Split audio data into chunks for streaming.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            List[bytes]: List of audio chunks
        """
        chunk_size = self.chunk_size * self.channels * 2  # 2 bytes per sample
        return [audio_data[i:i + chunk_size] for i in range(0, len(audio_data), chunk_size)]
    
    def combine_channels(self, audio_data: bytes) -> bytes:
        """
        Combine multiple audio channels into a single channel.
        
        Args:
            audio_data: Multi-channel audio data in bytes
            
        Returns:
            bytes: Single-channel audio data
        """
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_array = audio_array.reshape(-1, self.channels)
            
            # Average channels
            mono_audio = np.mean(audio_array, axis=1)
            
            # Convert back to bytes
            return mono_audio.astype(np.int16).tobytes()
            
        except Exception as e:
            logger.error(f"Channel combination error: {str(e)}")
            raise 