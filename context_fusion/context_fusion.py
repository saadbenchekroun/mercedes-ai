"""
Context fusion module for combining different context sources.
"""
import logging
from typing import Dict, Any, List, Optional
import asyncio
import json
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

class ContextFusion:
    """Combines different context sources into a unified context."""
    
    def __init__(self):
        """Initialize the context fusion module."""
        self.context_file = Path(settings.DATA_DIR) / "fused_context.json"
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._context: Dict[str, Any] = self._load_context()
        self._context_lock = asyncio.Lock()
        
        logger.info("Context fusion initialized")
    
    def _load_context(self) -> Dict[str, Any]:
        """
        Load fused context from file.
        
        Returns:
            Dict[str, Any]: Loaded context
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading fused context: {str(e)}")
                return self._get_default_context()
        else:
            return self._get_default_context()
    
    def _get_default_context(self) -> Dict[str, Any]:
        """
        Get default fused context.
        
        Returns:
            Dict[str, Any]: Default context
        """
        return {
            "conversation": {
                "history": [],
                "current_topic": None,
                "user_intent": None,
                "entities": {}
            },
            "vehicle": {
                "state": {},
                "location": None,
                "environment": {}
            },
            "user": {
                "preferences": {},
                "profile": {},
                "history": []
            },
            "system": {
                "status": "ready",
                "active_features": [],
                "errors": []
            }
        }
    
    async def fuse_contexts(
        self,
        conversation_context: Dict[str, Any],
        vehicle_context: Dict[str, Any],
        user_context: Dict[str, Any],
        system_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fuse different context sources.
        
        Args:
            conversation_context: Conversation context
            vehicle_context: Vehicle context
            user_context: User context
            system_context: System context
            
        Returns:
            Dict[str, Any]: Fused context
        """
        async with self._context_lock:
            try:
                # Update conversation context
                self._context["conversation"].update({
                    "history": conversation_context.get("conversation_history", []),
                    "current_topic": conversation_context.get("current_intent"),
                    "user_intent": conversation_context.get("current_intent"),
                    "entities": conversation_context.get("entities", {})
                })
                
                # Update vehicle context
                self._context["vehicle"].update({
                    "state": vehicle_context,
                    "location": vehicle_context.get("navigation", {}).get("current_location"),
                    "environment": {
                        "weather": vehicle_context.get("environment", {}).get("weather"),
                        "traffic": vehicle_context.get("environment", {}).get("traffic")
                    }
                })
                
                # Update user context
                self._context["user"].update({
                    "preferences": user_context.get("preferences", {}),
                    "profile": user_context.get("profile", {}),
                    "history": user_context.get("history", [])
                })
                
                # Update system context
                self._context["system"].update({
                    "status": system_context.get("status", "ready"),
                    "active_features": system_context.get("active_features", []),
                    "errors": system_context.get("errors", [])
                })
                
                # Save fused context
                await self._save_context()
                
                return self._context
                
            except Exception as e:
                logger.error(f"Error fusing contexts: {str(e)}")
                raise
    
    async def _save_context(self):
        """Save fused context to file."""
        try:
            with open(self.context_file, "w") as f:
                json.dump(self._context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving fused context: {str(e)}")
            raise
    
    async def get_fused_context(self) -> Dict[str, Any]:
        """
        Get current fused context.
        
        Returns:
            Dict[str, Any]: Current context
        """
        async with self._context_lock:
            return self._context
    
    async def update_conversation_context(self, updates: Dict[str, Any]):
        """
        Update conversation context.
        
        Args:
            updates: Context updates to apply
        """
        async with self._context_lock:
            self._context["conversation"].update(updates)
            await self._save_context()
    
    async def update_vehicle_context(self, updates: Dict[str, Any]):
        """
        Update vehicle context.
        
        Args:
            updates: Context updates to apply
        """
        async with self._context_lock:
            self._context["vehicle"].update(updates)
            await self._save_context()
    
    async def update_user_context(self, updates: Dict[str, Any]):
        """
        Update user context.
        
        Args:
            updates: Context updates to apply
        """
        async with self._context_lock:
            self._context["user"].update(updates)
            await self._save_context()
    
    async def update_system_context(self, updates: Dict[str, Any]):
        """
        Update system context.
        
        Args:
            updates: Context updates to apply
        """
        async with self._context_lock:
            self._context["system"].update(updates)
            await self._save_context()
    
    async def clear_context(self):
        """Clear the fused context."""
        async with self._context_lock:
            self._context = self._get_default_context()
            await self._save_context()
            logger.info("Fused context cleared")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current context.
        
        Returns:
            Dict[str, Any]: Context summary
        """
        return {
            "conversation": {
                "current_topic": self._context["conversation"]["current_topic"],
                "user_intent": self._context["conversation"]["user_intent"],
                "entity_count": len(self._context["conversation"]["entities"])
            },
            "vehicle": {
                "location": self._context["vehicle"]["location"],
                "state": {
                    "climate": self._context["vehicle"]["state"].get("climate_control", {}),
                    "media": self._context["vehicle"]["state"].get("media", {}),
                    "navigation": self._context["vehicle"]["state"].get("navigation", {})
                }
            },
            "user": {
                "preference_count": len(self._context["user"]["preferences"]),
                "history_count": len(self._context["user"]["history"])
            },
            "system": {
                "status": self._context["system"]["status"],
                "active_feature_count": len(self._context["system"]["active_features"]),
                "error_count": len(self._context["system"]["errors"])
            }
        } 