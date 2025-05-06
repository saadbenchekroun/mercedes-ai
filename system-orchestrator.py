"""
Mercedes-Benz S-Class (2021) Conversational AI System
====================================================
Main application entry point and system orchestrator.
"""

import os
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor

# Core components
from speech_recognition import SpeechRecognizer
from nlu import NaturalLanguageUnderstanding
from dialogue_manager import DialogueManager
from tts import TextToSpeech
from vehicle_integration import VehicleInterface
from context_fusion import ContextFusionEngine
from security import SecurityManager
from telemetry import TelemetryCollector

# Utilities and config
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.error_handler import ErrorHandler

class MercedesAISystem:
    """Main orchestrator for the Mercedes-Benz S-Class Conversational AI System."""
    
    def __init__(self, config_path: str = "/etc/mercedes-ai/config.json"):
        """
        Initialize the AI system with all required components.
        
        Args:
            config_path: Path to the configuration file
        """
        # Setup logging
        self.logger = setup_logger("MercedesAISystem", logging.INFO)
        self.logger.info("Initializing Mercedes-Benz S-Class Conversational AI System")
        
        # Load configuration
        self.config = ConfigLoader(config_path).load()
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self.config["error_handling"])
        
        # Initialize security manager
        self.security_manager = SecurityManager(
            self.config["security"],
            self.error_handler
        )
        
        # Initialize components
        self._init_components()
        
        # System state
        self.is_active = False
        self.conversation_active = False
        self.current_context = {}
        self.command_history = []
        
        # Component health status
        self.component_health = {
            "speech_recognition": False,
            "nlu": False,
            "dialogue_manager": False,
            "tts": False,
            "vehicle_integration": False,
            "context_fusion": False
        }
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=self.config["system"]["max_workers"])
        
        self.logger.info("System initialization complete")
    
    def _init_components(self) -> None:
        """Initialize all system components with proper error handling."""
        try:
            # Initialize speech recognition
            self.speech_recognizer = SpeechRecognizer(
                self.config["speech_recognition"],
                self.error_handler
            )
            
            # Initialize NLU
            self.nlu = NaturalLanguageUnderstanding(
                self.config["nlu"],
                self.error_handler
            )
            
            # Initialize dialogue manager
            self.dialogue_manager = DialogueManager(
                self.config["dialogue_manager"],
                self.error_handler
            )
            
            # Initialize text-to-speech
            self.tts = TextToSpeech(
                self.config["tts"],
                self.error_handler
            )
            
            # Initialize vehicle integration
            self.vehicle_interface = VehicleInterface(
                self.config["vehicle_integration"],
                self.error_handler
            )
            
            # Initialize context fusion engine
            self.context_fusion = ContextFusionEngine(
                self.config["context_fusion"],
                self.error_handler
            )
            
            # Initialize telemetry collector
            self.telemetry = TelemetryCollector(
                self.config["telemetry"],
                self.error_handler
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}")
            self.error_handler.handle(e, "system_initialization")
            raise
    
    async def start(self) -> None:
        """Start the AI system and all its components."""
        try:
            self.logger.info("Starting Mercedes-Benz AI System")
            
            # Start security services
            await self.security_manager.start()
            
            # Perform security checks
            if not await self.security_manager.verify_system_integrity():
                self.logger.critical("System integrity check failed. Aborting startup.")
                return
            
            # Start all components
            await self._start_components()
            
            # Perform health check
            health_status = await self.health_check()
            if not all(health_status.values()):
                failed_components = [k for k, v in health_status.items() if not v]
                self.logger.error(f"Component health check failed for: {failed_components}")
                await self._handle_failed_startup(failed_components)
                return
            
            # Set system as active
            self.is_active = True
            self.telemetry.log_event("system_start", {"status": "success"})
            
            # Start the main processing loop
            await self._processing_loop()
            
        except Exception as e:
            self.logger.critical(f"Failed to start system: {str(e)}")
            self.error_handler.handle(e, "system_startup")
            await self.shutdown()
    
    async def _start_components(self) -> None:
        """Start all system components."""
        self.logger.info("Starting system components")
        
        # Start each component with proper error handling
        component_start_tasks = [
            self.speech_recognizer.start(),
            self.nlu.start(),
            self.dialogue_manager.start(),
            self.tts.start(),
            self.vehicle_interface.start(),
            self.context_fusion.start(),
            self.telemetry.start()
        ]
        
        # Wait for all components to start
        await asyncio.gather(*component_start_tasks)
        
        # Subscribe to vehicle events
        self.vehicle_interface.subscribe_to_events(self._handle_vehicle_event)
        
        # Connect speech recognition output to NLU input
        self.speech_recognizer.set_recognition_callback(self._handle_speech_input)
        
        self.logger.info("All components started successfully")
    
    async def _handle_failed_startup(self, failed_components: List[str]) -> None:
        """Handle failed components during startup."""
        self.logger.warning(f"Attempting recovery for failed components: {failed_components}")
        
        recovery_success = True
        for component in failed_components:
            try:
                if component == "speech_recognition":
                    await self.speech_recognizer.restart()
                elif component == "nlu":
                    await self.nlu.restart()
                elif component == "dialogue_manager":
                    await self.dialogue_manager.restart()
                elif component == "tts":
                    await self.tts.restart()
                elif component == "vehicle_integration":
                    await self.vehicle_interface.restart()
                elif component == "context_fusion":
                    await self.context_fusion.restart()
                
                self.logger.info(f"Successfully recovered {component}")
            except Exception as e:
                self.logger.error(f"Failed to recover {component}: {str(e)}")
                recovery_success = False
        
        if recovery_success:
            self.logger.info("All failed components recovered, starting system")
            self.is_active = True
            await self._processing_loop()
        else:
            self.logger.critical("Failed to recover all components, system startup aborted")
            await self.shutdown(emergency=True)
    
    async def _processing_loop(self) -> None:
        """Main processing loop for the AI system."""
        self.logger.info("Entering main processing loop")
        
        while self.is_active:
            try:
                # Update vehicle context
                vehicle_data = await self.vehicle_interface.get_current_state()
                
                # Update context fusion engine
                await self.context_fusion.update_vehicle_data(vehicle_data)
                
                # Check for wake word detection
                if (not self.conversation_active and 
                    await self.speech_recognizer.is_wake_word_detected()):
                    await self._start_conversation()
                
                # Process any pending speech input
                # (Speech input processing is handled by callbacks)
                
                # Short sleep to prevent CPU overuse
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}")
                self.error_handler.handle(e, "processing_loop")
                
                # Perform recovery attempt for non-critical errors
                if not self.error_handler.is_critical_error(e):
                    continue
                else:
                    await self.shutdown(emergency=True)
                    break
    
    async def _start_conversation(self) -> None:
        """Start a new conversation session."""
        self.logger.info("Starting new conversation session")
        
        # Get initial context
        context = await self.context_fusion.get_current_context()
        
        # Reset conversation state
        self.conversation_active = True
        self.current_context = context
        
        # Acknowledge wake word with visual and audio feedback
        await self.vehicle_interface.set_ui_state("listening")
        await self.tts.speak("I'm listening", interrupt=True)
        
        # Log conversation start
        self.telemetry.log_event("conversation_start", {
            "context": self.current_context
        })
    
    async def _handle_speech_input(self, transcription: str, confidence: float) -> None:
        """
        Handle speech input from the speech recognition component.
        
        Args:
            transcription: The transcribed text
            confidence: Confidence score (0-1)
        """
        if not self.conversation_active:
            return
        
        self.logger.info(f"Received speech input: '{transcription}' (conf: {confidence:.2f})")
        
        # Update UI to show processing
        await self.vehicle_interface.set_ui_state("processing")
        
        # Ignore low confidence transcriptions
        if confidence < self.config["speech_recognition"]["min_confidence"]:
            self.logger.warning(f"Low confidence transcription ignored: {confidence:.2f}")
            await self.tts.speak("I didn't catch that. Could you please repeat?")
            return
        
        try:
            # Process through NLU
            nlu_result = await self.nlu.process(transcription)
            
            # Get updated context
            context = await self.context_fusion.get_current_context()
            
            # Process through dialogue manager
            response = await self.dialogue_manager.process_turn(
                nlu_result,
                context
            )
            
            # Execute any commands if present
            if response.get("commands"):
                await self._execute_vehicle_commands(response["commands"])
            
            # Speak the response
            if response.get("speech_response"):
                await self.tts.speak(response["speech_response"])
            
            # Update UI if needed
            if response.get("ui_update"):
                await self.vehicle_interface.update_ui(response["ui_update"])
            
            # Update conversation state
            self.current_context = context
            self.command_history.append({
                "input": transcription,
                "intent": nlu_result.get("intent"),
                "response": response
            })
            
            # Log interaction
            self.telemetry.log_interaction(
                transcription,
                nlu_result,
                response
            )
            
            # Check if conversation should end
            if response.get("end_conversation", False):
                await self._end_conversation()
                
        except Exception as e:
            self.logger.error(f"Error processing speech input: {str(e)}")
            self.error_handler.handle(e, "speech_processing")
            await self.tts.speak("I'm sorry, I encountered an error. Please try again.")
    
    async def _execute_vehicle_commands(self, commands: List[Dict]) -> None:
        """
        Execute vehicle commands.
        
        Args:
            commands: List of command dictionaries
        """
        self.logger.info(f"Executing vehicle commands: {commands}")
        
        for command in commands:
            try:
                command_type = command.get("type")
                params = command.get("parameters", {})
                
                if command_type == "climate_control":
                    await self.vehicle_interface.set_climate(
                        temperature=params.get("temperature"),
                        fan_speed=params.get("fan_speed"),
                        zone=params.get("zone")
                    )
                elif command_type == "navigation":
                    await self.vehicle_interface.set_navigation_destination(
                        destination=params.get("destination"),
                        route_preferences=params.get("route_preferences")
                    )
                elif command_type == "media":
                    await self.vehicle_interface.control_media(
                        action=params.get("action"),
                        source=params.get("source"),
                        content=params.get("content")
                    )
                elif command_type == "vehicle_settings":
                    await self.vehicle_interface.update_settings(
                        settings=params
                    )
                else:
                    self.logger.warning(f"Unknown command type: {command_type}")
                
            except Exception as e:
                self.logger.error(f"Error executing command {command}: {str(e)}")
                self.error_handler.handle(e, "command_execution")
    
    async def _handle_vehicle_event(self, event_type: str, event_data: Dict) -> None:
        """
        Handle events from the vehicle.
        
        Args:
            event_type: Type of the event
            event_data: Event data
        """
        self.logger.debug(f"Received vehicle event: {event_type}")
        
        # Update context with new vehicle event
        await self.context_fusion.update_vehicle_event(event_type, event_data)
        
        # Check if we need to proactively notify the user
        proactive_response = await self.dialogue_manager.check_proactive_trigger(
            event_type,
            event_data,
            await self.context_fusion.get_current_context()
        )
        
        if proactive_response:
            # If we're not in a conversation, start one
            if not self.conversation_active:
                self.conversation_active = True
                await self.vehicle_interface.set_ui_state("speaking")
            
            # Speak the proactive notification
            await self.tts.speak(proactive_response["speech"])
            
            # Execute any associated commands
            if proactive_response.get("commands"):
                await self._execute_vehicle_commands(proactive_response["commands"])
            
            # Log the proactive interaction
            self.telemetry.log_event("proactive_notification", {
                "event_type": event_type,
                "response": proactive_response
            })
    
    async def _end_conversation(self) -> None:
        """End the current conversation session."""
        self.logger.info("Ending conversation session")
        
        # Reset conversation state
        self.conversation_active = False
        
        # Reset UI
        await self.vehicle_interface.set_ui_state("idle")
        
        # Log conversation end
        self.telemetry.log_event("conversation_end", {
            "turn_count": len(self.command_history),
            "duration": time.time() - self.telemetry.get_last_event_time("conversation_start")
        })
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Perform a health check on all system components.
        
        Returns:
            Dict with component names as keys and health status as values
        """
        health_status = {}
        
        # Check each component
        health_status["speech_recognition"] = await self.speech_recognizer.health_check()
        health_status["nlu"] = await self.nlu.health_check()
        health_status["dialogue_manager"] = await self.dialogue_manager.health_check()
        health_status["tts"] = await self.tts.health_check()
        health_status["vehicle_integration"] = await self.vehicle_interface.health_check()
        health_status["context_fusion"] = await self.context_fusion.health_check()
        
        # Update component health status
        self.component_health = health_status
        
        # Log health check results
        self.telemetry.log_event("health_check", {
            "status": health_status,
            "all_healthy": all(health_status.values())
        })
        
        return health_status
    
    async def shutdown(self, emergency: bool = False) -> None:
        """
        Shutdown the AI system.
        
        Args:
            emergency: Whether this is an emergency shutdown
        """
        self.logger.info(f"{'Emergency ' if emergency else ''}Shutting down Mercedes-Benz AI System")
        
        # Set system as inactive
        self.is_active = False
        self.conversation_active = False
        
        try:
            # Shutdown all components in reverse order
            await self.telemetry.stop()
            await self.context_fusion.stop()
            await self.vehicle_interface.stop()
            await self.tts.stop()
            await self.dialogue_manager.stop()
            await self.nlu.stop()
            await self.speech_recognizer.stop()
            
            # Shutdown security manager
            await self.security_manager.stop()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            self.logger.info("System shutdown complete")
            
        except Exception as e:
            self.logger.critical(f"Error during shutdown: {str(e)}")
            # In case of emergency shutdown, we can't do much more
            if not emergency:
                self.error_handler.handle(e, "system_shutdown")


# If running directly, start the system
if __name__ == "__main__":
    # Create system instance
    system = MercedesAISystem()
    
    # Run the system
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        print("\nShutting down Mercedes-Benz AI System...")
        asyncio.run(system.shutdown())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        asyncio.run(system.shutdown(emergency=True))
