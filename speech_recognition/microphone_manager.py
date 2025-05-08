"""
Microphone array management for audio input and output.
"""
import asyncio
import logging
import sounddevice as sd
import numpy as np
from typing import Optional, List, Tuple

from config import settings
from .audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

class MicrophoneManager:
    """Manages the 4-mic array for audio input and output."""
    
    def __init__(self):
        """Initialize the microphone manager."""
        self.sample_rate = settings.ASR_SAMPLE_RATE
        self.channels = settings.ASR_CHANNELS
        self.chunk_size = settings.ASR_CHUNK_SIZE
        self.audio_processor = AudioProcessor()
        
        self._input_stream: Optional[sd.InputStream] = None
        self._output_stream: Optional[sd.OutputStream] = None
        self._audio_queue = asyncio.Queue()
        self._is_recording = False
        
    async def start(self):
        """Start the microphone manager."""
        try:
            # Initialize input stream
            self._input_stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.int16,
                callback=self._audio_callback
            )
            
            # Initialize output stream
            self._output_stream = sd.OutputStream(
                channels=1,  # Output is mono
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.int16
            )
            
            self._input_stream.start()
            self._output_stream.start()
            self._is_recording = True
            
            logger.info("Microphone manager started")
            
        except Exception as e:
            logger.error(f"Failed to start microphone manager: {str(e)}")
            raise
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        """
        Callback for audio input stream.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time: Time information
            status: Status information
        """
        if status:
            logger.warning(f"Audio input status: {status}")
        
        if self._is_recording:
            # Convert to bytes and put in queue
            audio_data = indata.tobytes()
            asyncio.create_task(self._audio_queue.put(audio_data))
    
    async def get_audio(self) -> bytes:
        """
        Get audio data from the microphone.
        
        Returns:
            bytes: Audio data
        """
        if not self._is_recording:
            await self.start()
        
        try:
            # Get audio data from queue
            audio_data = await self._audio_queue.get()
            
            # Preprocess audio
            processed_audio = self.audio_processor.preprocess(audio_data)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error getting audio: {str(e)}")
            raise
    
    async def play_audio(self, audio_data: bytes):
        """
        Play audio through the sound system.
        
        Args:
            audio_data: Audio data to play
        """
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Play audio
            self._output_stream.write(audio_array)
            
        except Exception as e:
            logger.error(f"Error playing audio: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the microphone manager."""
        self._is_recording = False
        
        if self._input_stream:
            self._input_stream.stop()
            self._input_stream.close()
        
        if self._output_stream:
            self._output_stream.stop()
            self._output_stream.close()
        
        logger.info("Microphone manager stopped")
    
    def get_device_info(self) -> List[Tuple[int, str]]:
        """
        Get information about available audio devices.
        
        Returns:
            List[Tuple[int, str]]: List of (device_id, device_name) tuples
        """
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] >= self.channels:
                devices.append((i, device['name']))
        return devices
    
    async def set_input_device(self, device_id: int):
        """
        Set the input device.
        
        Args:
            device_id: Device ID to use
        """
        if self._is_recording:
            await self.stop()
        
        try:
            # Verify device supports required channels
            device_info = sd.query_devices(device_id)
            if device_info['max_input_channels'] < self.channels:
                raise ValueError(f"Device {device_id} does not support {self.channels} channels")
            
            # Update device
            sd.default.device[0] = device_id
            
            if self._is_recording:
                await self.start()
            
            logger.info(f"Input device set to {device_info['name']}")
            
        except Exception as e:
            logger.error(f"Error setting input device: {str(e)}")
            raise 