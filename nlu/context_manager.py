"""
Context management module for maintaining conversation state.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

from config import settings

logger = logging.getLogger(__name__)

class ContextManager:
    """Manages conversation context and state."""
    
    def __init__(self):
        """Initialize the context manager."""
        self.context_file = Path(settings.DATA_DIR) / "context.json"
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._context: Dict[str, Any] = self._load_context()
        self._context_lock = asyncio.Lock()
        self._context_ttl = timedelta(minutes=30)  # Context expires after 30 minutes
        
        logger.info("Context manager initialized")
    
    def _load_context(self) -> Dict[str, Any]:
        """
        Load context from file.
        
        Returns:
            Dict[str, Any]: Loaded context
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading context: {str(e)}")
                return self._get_default_context()
        else:
            return self._get_default_context()
    
    def _get_default_context(self) -> Dict[str, Any]:
        """
        Get default context structure.
        
        Returns:
            Dict[str, Any]: Default context
        """
        return {
            "conversation_history": [],
            "current_intent": None,
            "entities": {},
            "user_preferences": {},
            "vehicle_state": {},
            "last_update": datetime.now().isoformat()
        }
    
    async def get_context(self) -> Dict[str, Any]:
        """
        Get current context.
        
        Returns:
            Dict[str, Any]: Current context
        """
        async with self._context_lock:
            # Check if context has expired
            last_update = datetime.fromisoformat(self._context["last_update"])
            if datetime.now() - last_update > self._context_ttl:
                self._context = self._get_default_context()
                await self._save_context()
            
            return self._context
    
    async def update_context(self, updates: Dict[str, Any]):
        """
        Update context with new information.
        
        Args:
            updates: Context updates to apply
        """
        async with self._context_lock:
            # Update context
            for key, value in updates.items():
                if key in self._context:
                    if isinstance(self._context[key], dict) and isinstance(value, dict):
                        self._context[key].update(value)
                    else:
                        self._context[key] = value
            
            # Update timestamp
            self._context["last_update"] = datetime.now().isoformat()
            
            # Save context
            await self._save_context()
    
    async def add_to_history(self, text: str, intent: str, entities: Dict[str, Any]):
        """
        Add a conversation turn to history.
        
        Args:
            text: User input text
            intent: Detected intent
            entities: Extracted entities
        """
        async with self._context_lock:
            # Create history entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "text": text,
                "intent": intent,
                "entities": entities
            }
            
            # Add to history
            self._context["conversation_history"].append(entry)
            
            # Limit history size
            if len(self._context["conversation_history"]) > settings.CONTEXT_WINDOW_SIZE:
                self._context["conversation_history"] = self._context["conversation_history"][-settings.CONTEXT_WINDOW_SIZE:]
            
            # Update timestamp
            self._context["last_update"] = datetime.now().isoformat()
            
            # Save context
            await self._save_context()
    
    async def _save_context(self):
        """Save context to file."""
        try:
            with open(self.context_file, "w") as f:
                json.dump(self._context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            raise
    
    async def clear_context(self):
        """Clear the context."""
        async with self._context_lock:
            self._context = self._get_default_context()
            await self._save_context()
            logger.info("Context cleared")
    
    def get_recent_history(self, turns: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            turns: Number of recent turns to return
            
        Returns:
            List[Dict[str, Any]]: Recent conversation history
        """
        return self._context["conversation_history"][-turns:]
    
    async def update_user_preferences(self, preferences: Dict[str, Any]):
        """
        Update user preferences.
        
        Args:
            preferences: User preferences to update
        """
        async with self._context_lock:
            self._context["user_preferences"].update(preferences)
            self._context["last_update"] = datetime.now().isoformat()
            await self._save_context()
    
    async def update_vehicle_state(self, state: Dict[str, Any]):
        """
        Update vehicle state.
        
        Args:
            state: Vehicle state to update
        """
        async with self._context_lock:
            self._context["vehicle_state"].update(state)
            self._context["last_update"] = datetime.now().isoformat()
            await self._save_context() 