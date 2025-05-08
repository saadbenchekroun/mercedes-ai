"""
Deepgram ASR client for speech recognition.
"""
import asyncio
import logging
from typing import Optional, Dict, Any

import deepgram
from deepgram import DeepgramClient, LiveTranscriptionEvents

from config import settings

logger = logging.getLogger(__name__)

class DeepgramASRClient:
    """Client for Deepgram's ASR service."""
    
    def __init__(self):
        """Initialize the Deepgram ASR client."""
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.connection: Optional[Any] = None
        self._transcription_queue = asyncio.Queue()
        self._is_connected = False
        
    async def connect(self):
        """Establish connection to Deepgram's streaming API."""
        try:
            self.connection = await self.client.listen.live.v("1")
            
            @self.connection.on(LiveTranscriptionEvents.Transcript)
            async def handle_transcript(transcript):
                if transcript.channel.alternatives:
                    text = transcript.channel.alternatives[0].transcript
                    await self._transcription_queue.put(text)
            
            @self.connection.on(LiveTranscriptionEvents.Error)
            async def handle_error(error):
                logger.error(f"Deepgram error: {error}")
                self._is_connected = False
            
            @self.connection.on(LiveTranscriptionEvents.Close)
            async def handle_close():
                logger.info("Deepgram connection closed")
                self._is_connected = False
            
            self._is_connected = True
            logger.info("Connected to Deepgram ASR service")
            
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {str(e)}")
            raise
    
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            str: Transcribed text
        """
        if not self._is_connected:
            await self.connect()
        
        try:
            # Send audio data to Deepgram
            await self.connection.send(audio_data)
            
            # Wait for transcription
            text = await self._transcription_queue.get()
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the ASR client and close the connection."""
        if self.connection:
            await self.connection.finish()
            self._is_connected = False
            logger.info("ASR client stopped") 