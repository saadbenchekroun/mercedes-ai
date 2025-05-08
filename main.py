"""
Main entry point for the Mercedes AI system.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from config import settings
from speech_recognition.asr_client import DeepgramASRClient
from speech_recognition.microphone_manager import MicrophoneManager
from nlu.intent_classifier import IntentClassifier
from nlu.entity_extractor import EntityExtractor
from nlu.context_manager import ContextManager
from dialogue.llm_client import GPT4Client
from dialogue.conversation_manager import ConversationManager
from tts.azure_tts_client import AzureTTSClient
from vehicle.mbux_interface import MBUXInterface
from vehicle.vehicle_controller import VehicleController
from context_fusion.context_aggregator import ContextAggregator
from security.encryption import EncryptionManager
from optimization.tensorrt_wrapper import TensorRTWrapper
from deployment.ota_manager import OTAManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MercedesAI:
    def __init__(self):
        """Initialize the Mercedes AI system components."""
        logger.info("Initializing Mercedes AI system...")
        
        # Initialize security
        self.encryption = EncryptionManager()
        
        # Initialize speech components
        self.microphone = MicrophoneManager()
        self.asr_client = DeepgramASRClient()
        
        # Initialize NLU components
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        
        # Initialize dialogue components
        self.llm_client = GPT4Client()
        self.conversation_manager = ConversationManager()
        
        # Initialize TTS
        self.tts_client = AzureTTSClient()
        
        # Initialize vehicle integration
        self.mbux = MBUXInterface()
        self.vehicle_controller = VehicleController()
        
        # Initialize context fusion
        self.context_aggregator = ContextAggregator()
        
        # Initialize optimization
        self.tensorrt = TensorRTWrapper()
        
        # Initialize deployment
        self.ota_manager = OTAManager()
        
        logger.info("Mercedes AI system initialized successfully")

    async def start(self):
        """Start the Mercedes AI system."""
        try:
            logger.info("Starting Mercedes AI system...")
            
            # Start OTA update checker
            asyncio.create_task(self.ota_manager.start_update_checker())
            
            # Start context fusion
            asyncio.create_task(self.context_aggregator.start())
            
            # Start the main conversation loop
            while True:
                try:
                    # Get audio input
                    audio_data = await self.microphone.get_audio()
                    
                    # Process speech to text
                    text = await self.asr_client.transcribe(audio_data)
                    
                    # Process NLU
                    intent = await self.intent_classifier.classify(text)
                    entities = await self.entity_extractor.extract(text)
                    
                    # Get context
                    context = await self.context_manager.get_context()
                    
                    # Generate response
                    response = await self.conversation_manager.generate_response(
                        text, intent, entities, context
                    )
                    
                    # Convert response to speech
                    audio_response = await self.tts_client.synthesize(response)
                    
                    # Play response
                    await self.microphone.play_audio(audio_response)
                    
                except Exception as e:
                    logger.error(f"Error in conversation loop: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Fatal error in Mercedes AI system: {str(e)}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the Mercedes AI system."""
        logger.info("Shutting down Mercedes AI system...")
        
        # Stop all components
        await self.microphone.stop()
        await self.asr_client.stop()
        await self.context_aggregator.stop()
        await self.ota_manager.stop()
        
        logger.info("Mercedes AI system shut down successfully")

async def main():
    """Main entry point."""
    mercedes_ai = MercedesAI()
    
    try:
        await mercedes_ai.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await mercedes_ai.shutdown()

if __name__ == "__main__":
    # Set up asyncio event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main function
    asyncio.run(main()) 