"""
Text-to-speech client using ElevenLabs API.
"""
import logging
import asyncio
from typing import Optional, Dict, Any
import aiohttp
import json
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

class TTSClient:
    """Client for ElevenLabs TTS service."""
    
    def __init__(self):
        """Initialize the TTS client."""
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        self.model_id = "eleven_monolingual_v1"
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._audio_queue = asyncio.Queue()
        self._is_connected = False
        
        logger.info("TTS client initialized")
    
    async def connect(self):
        """Establish connection to ElevenLabs API."""
        if not self._session:
            self._session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            self._is_connected = True
            logger.info("Connected to ElevenLabs TTS service")
    
    async def synthesize(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> bytes:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)
            
        Returns:
            bytes: Audio data
        """
        if not self._is_connected:
            await self.connect()
        
        try:
            # Prepare request
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            data = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }
            
            # Make request
            async with self._session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"TTS API error: {error_text}")
                
                # Get audio data
                audio_data = await response.read()
                
                # Save audio file
                output_path = Path(settings.AUDIO_OUTPUT_DIR) / f"tts_{hash(text)}.mp3"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                logger.debug(f"Generated audio file: {output_path}")
                return audio_data
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {str(e)}")
            raise
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices.
        
        Returns:
            Dict[str, Any]: Available voices
        """
        if not self._is_connected:
            await self.connect()
        
        try:
            url = f"{self.base_url}/voices"
            async with self._session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"TTS API error: {error_text}")
                
                return await response.json()
            
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            raise
    
    async def set_voice(self, voice_id: str):
        """
        Set the voice to use.
        
        Args:
            voice_id: Voice ID to use
        """
        self.voice_id = voice_id
        logger.info(f"Voice set to {voice_id}")
    
    async def stop(self):
        """Stop the TTS client and close the connection."""
        if self._session:
            await self._session.close()
            self._session = None
            self._is_connected = False
            logger.info("TTS client stopped") 