"""
Main application entry point for the Mercedes-Benz S-Class AI Assistant.
"""
import logging
import asyncio
import signal
from typing import Dict, Any, Optional
import json
from pathlib import Path

from config import settings
from speech_recognition.asr_client import ASRClient
from speech_recognition.audio_processor import AudioProcessor
from speech_recognition.microphone_manager import MicrophoneManager
from nlu.intent_classifier import IntentClassifier
from nlu.entity_extractor import EntityExtractor
from nlu.context_manager import ContextManager
from dialogue.llm_client import LLMClient
from dialogue.dialogue_manager import DialogueManager
from tts.tts_client import TTSClient
from vehicle.vehicle_controller import VehicleController
from context_fusion.context_fusion import ContextFusion
from security.security_manager import SecurityManager
from optimization.optimizer import Optimizer
from deployment.deployment_manager import DeploymentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_DIR / "app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MercedesAI:
    """Main application class for the Mercedes-Benz AI Assistant."""
    
    def __init__(self):
        """Initialize the AI assistant."""
        # Initialize components
        self.asr_client = ASRClient()
        self.audio_processor = AudioProcessor()
        self.microphone_manager = MicrophoneManager()
        
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        
        self.llm_client = LLMClient()
        self.dialogue_manager = DialogueManager()
        
        self.tts_client = TTSClient()
        self.vehicle_controller = VehicleController()
        
        self.context_fusion = ContextFusion()
        self.security_manager = SecurityManager()
        self.optimizer = Optimizer()
        self.deployment_manager = DeploymentManager()
        
        # Application state
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info("Mercedes AI Assistant initialized")
    
    async def start(self):
        """Start the AI assistant."""
        try:
            self._is_running = True
            
            # Start components
            await self.microphone_manager.start()
            await self.tts_client.connect()
            
            # Start main processing loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error starting AI assistant: {str(e)}")
            await self.stop()
    
    async def stop(self):
        """Stop the AI assistant."""
        try:
            self._is_running = False
            self._shutdown_event.set()
            
            # Stop components
            await self.microphone_manager.stop()
            await self.tts_client.stop()
            
            logger.info("AI assistant stopped")
            
        except Exception as e:
            logger.error(f"Error stopping AI assistant: {str(e)}")
    
    async def _main_loop(self):
        """Main processing loop."""
        while self._is_running and not self._shutdown_event.is_set():
            try:
                # Get audio input
                audio_data = await self.microphone_manager.get_audio()
                
                # Process audio
                processed_audio = self.audio_processor.process(audio_data)
                
                # Convert speech to text
                text = await self.asr_client.transcribe(processed_audio)
                
                if text:
                    # Get vehicle state
                    vehicle_state = await self.vehicle_controller.get_state()
                    
                    # Process input
                    response = await self.dialogue_manager.process_input(
                        text,
                        vehicle_state
                    )
                    
                    # Update context
                    await self.context_fusion.fuse_contexts(
                        await self.context_manager.get_context(),
                        vehicle_state,
                        await self.context_manager.get_user_context(),
                        {"status": "active"}
                    )
                    
                    # Generate speech
                    audio = await self.tts_client.synthesize(response["text"])
                    
                    # Play response
                    await self.microphone_manager.play_audio(audio)
                    
                    # Record metrics
                    await self.optimizer.record_metric(
                        "application",
                        "response_time",
                        response.get("processing_time", 0.0)
                    )
                
                # Check system health
                health_status = await self.deployment_manager.check_health()
                if health_status["status"] != "healthy":
                    logger.warning(f"System health check failed: {health_status}")
                
                # Optimize performance if needed
                optimization_result = await self.optimizer.optimize_performance()
                if optimization_result["suggestions"]:
                    logger.info(f"Performance optimization suggestions: {optimization_result['suggestions']}")
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.stop()))

async def main():
    """Main entry point."""
    # Create and start AI assistant
    ai = MercedesAI()
    ai._setup_signal_handlers()
    
    try:
        await ai.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await ai.stop()

if __name__ == "__main__":
    asyncio.run(main()) 