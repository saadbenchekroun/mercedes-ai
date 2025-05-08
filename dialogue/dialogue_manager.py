"""
Dialogue management module for handling conversation flow.
"""
import logging
from typing import Dict, Any, List, Optional
import asyncio

from config import settings
from .llm_client import LLMClient
from nlu.intent_classifier import IntentClassifier
from nlu.entity_extractor import EntityExtractor
from nlu.context_manager import ContextManager

logger = logging.getLogger(__name__)

class DialogueManager:
    """Manages dialogue flow and state."""
    
    def __init__(self):
        """Initialize the dialogue manager."""
        self.llm_client = LLMClient()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        
        self._response_queue = asyncio.Queue()
        self._is_processing = False
        
        logger.info("Dialogue manager initialized")
    
    async def process_input(
        self,
        text: str,
        vehicle_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user input and generate response.
        
        Args:
            text: User input text
            vehicle_state: Current vehicle state
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            self._is_processing = True
            
            # Get current context
            context = await self.context_manager.get_context()
            
            # Classify intent
            intent, confidence = await self.intent_classifier.classify(text)
            
            # Extract entities
            entities = await self.entity_extractor.extract(text)
            
            # Update context
            await self.context_manager.add_to_history(text, intent, entities)
            
            # Generate response
            response = await self.llm_client.generate_response(
                text,
                context,
                vehicle_state
            )
            
            # Add response to context
            await self.context_manager.add_to_history(
                response["text"],
                "assistant",
                {}
            )
            
            # Generate follow-up questions if needed
            if response.get("action") == "clarify":
                follow_ups = await self.llm_client.generate_follow_up(context)
                response["follow_up_questions"] = follow_ups
            
            # Put response in queue
            await self._response_queue.put(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            return {
                "text": "I apologize, but I'm having trouble processing your request right now.",
                "action": "error",
                "confidence": 0.0
            }
        finally:
            self._is_processing = False
    
    async def get_response(self) -> Dict[str, Any]:
        """
        Get the next response from the queue.
        
        Returns:
            Dict[str, Any]: Response data
        """
        return await self._response_queue.get()
    
    async def update_vehicle_state(self, state: Dict[str, Any]):
        """
        Update vehicle state in context.
        
        Args:
            state: Vehicle state to update
        """
        await self.context_manager.update_vehicle_state(state)
    
    async def update_user_preferences(self, preferences: Dict[str, Any]):
        """
        Update user preferences in context.
        
        Args:
            preferences: User preferences to update
        """
        await self.context_manager.update_user_preferences(preferences)
    
    async def clear_context(self):
        """Clear the conversation context."""
        await self.context_manager.clear_context()
    
    def is_processing(self) -> bool:
        """
        Check if currently processing input.
        
        Returns:
            bool: True if processing, False otherwise
        """
        return self._is_processing
    
    async def get_recent_history(self, turns: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            turns: Number of recent turns to return
            
        Returns:
            List[Dict[str, Any]]: Recent conversation history
        """
        return self.context_manager.get_recent_history(turns) 