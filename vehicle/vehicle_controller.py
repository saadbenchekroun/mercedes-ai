"""
Vehicle controller for managing vehicle state and control.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

class VehicleController:
    """Controls vehicle systems and manages vehicle state."""
    
    def __init__(self):
        """Initialize the vehicle controller."""
        self.state_file = Path(settings.DATA_DIR) / "vehicle_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._state: Dict[str, Any] = self._load_state()
        self._state_lock = asyncio.Lock()
        self._command_queue = asyncio.Queue()
        
        logger.info("Vehicle controller initialized")
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Load vehicle state from file.
        
        Returns:
            Dict[str, Any]: Vehicle state
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading vehicle state: {str(e)}")
                return self._get_default_state()
        else:
            return self._get_default_state()
    
    def _get_default_state(self) -> Dict[str, Any]:
        """
        Get default vehicle state.
        
        Returns:
            Dict[str, Any]: Default state
        """
        return {
            "climate_control": {
                "temperature": 22.0,
                "fan_speed": 2,
                "mode": "auto",
                "recirculation": False
            },
            "media": {
                "source": "radio",
                "volume": 50,
                "muted": False,
                "current_track": None
            },
            "navigation": {
                "destination": None,
                "route": None,
                "eta": None,
                "distance": None
            },
            "phone": {
                "connected": False,
                "active_call": None,
                "contacts": []
            },
            "vehicle": {
                "speed": 0,
                "fuel_level": 100,
                "battery_level": 100,
                "doors_locked": True,
                "lights": "auto"
            }
        }
    
    async def get_state(self) -> Dict[str, Any]:
        """
        Get current vehicle state.
        
        Returns:
            Dict[str, Any]: Current state
        """
        async with self._state_lock:
            return self._state
    
    async def update_state(self, updates: Dict[str, Any]):
        """
        Update vehicle state.
        
        Args:
            updates: State updates to apply
        """
        async with self._state_lock:
            # Update state
            for key, value in updates.items():
                if key in self._state:
                    if isinstance(self._state[key], dict) and isinstance(value, dict):
                        self._state[key].update(value)
                    else:
                        self._state[key] = value
            
            # Save state
            await self._save_state()
    
    async def _save_state(self):
        """Save vehicle state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving vehicle state: {str(e)}")
            raise
    
    async def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a vehicle command.
        
        Args:
            command: Command to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Put command in queue
            await self._command_queue.put(command)
            
            # Execute command
            success = await self._process_command(command)
            
            if success:
                logger.info(f"Executed command: {command}")
            else:
                logger.warning(f"Failed to execute command: {command}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return False
    
    async def _process_command(self, command: Dict[str, Any]) -> bool:
        """
        Process a vehicle command.
        
        Args:
            command: Command to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            command_type = command.get("type")
            params = command.get("params", {})
            
            if command_type == "climate_control":
                return await self._handle_climate_control(params)
            elif command_type == "media":
                return await self._handle_media_control(params)
            elif command_type == "navigation":
                return await self._handle_navigation(params)
            elif command_type == "phone":
                return await self._handle_phone_control(params)
            elif command_type == "vehicle":
                return await self._handle_vehicle_control(params)
            else:
                logger.warning(f"Unknown command type: {command_type}")
                return False
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return False
    
    async def _handle_climate_control(self, params: Dict[str, Any]) -> bool:
        """
        Handle climate control commands.
        
        Args:
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {}
            
            if "temperature" in params:
                updates["temperature"] = float(params["temperature"])
            if "fan_speed" in params:
                updates["fan_speed"] = int(params["fan_speed"])
            if "mode" in params:
                updates["mode"] = params["mode"]
            if "recirculation" in params:
                updates["recirculation"] = bool(params["recirculation"])
            
            await self.update_state({"climate_control": updates})
            return True
            
        except Exception as e:
            logger.error(f"Error handling climate control: {str(e)}")
            return False
    
    async def _handle_media_control(self, params: Dict[str, Any]) -> bool:
        """
        Handle media control commands.
        
        Args:
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {}
            
            if "source" in params:
                updates["source"] = params["source"]
            if "volume" in params:
                updates["volume"] = int(params["volume"])
            if "muted" in params:
                updates["muted"] = bool(params["muted"])
            if "current_track" in params:
                updates["current_track"] = params["current_track"]
            
            await self.update_state({"media": updates})
            return True
            
        except Exception as e:
            logger.error(f"Error handling media control: {str(e)}")
            return False
    
    async def _handle_navigation(self, params: Dict[str, Any]) -> bool:
        """
        Handle navigation commands.
        
        Args:
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {}
            
            if "destination" in params:
                updates["destination"] = params["destination"]
            if "route" in params:
                updates["route"] = params["route"]
            if "eta" in params:
                updates["eta"] = params["eta"]
            if "distance" in params:
                updates["distance"] = params["distance"]
            
            await self.update_state({"navigation": updates})
            return True
            
        except Exception as e:
            logger.error(f"Error handling navigation: {str(e)}")
            return False
    
    async def _handle_phone_control(self, params: Dict[str, Any]) -> bool:
        """
        Handle phone control commands.
        
        Args:
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {}
            
            if "connected" in params:
                updates["connected"] = bool(params["connected"])
            if "active_call" in params:
                updates["active_call"] = params["active_call"]
            if "contacts" in params:
                updates["contacts"] = params["contacts"]
            
            await self.update_state({"phone": updates})
            return True
            
        except Exception as e:
            logger.error(f"Error handling phone control: {str(e)}")
            return False
    
    async def _handle_vehicle_control(self, params: Dict[str, Any]) -> bool:
        """
        Handle vehicle control commands.
        
        Args:
            params: Command parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {}
            
            if "speed" in params:
                updates["speed"] = float(params["speed"])
            if "fuel_level" in params:
                updates["fuel_level"] = float(params["fuel_level"])
            if "battery_level" in params:
                updates["battery_level"] = float(params["battery_level"])
            if "doors_locked" in params:
                updates["doors_locked"] = bool(params["doors_locked"])
            if "lights" in params:
                updates["lights"] = params["lights"]
            
            await self.update_state({"vehicle": updates})
            return True
            
        except Exception as e:
            logger.error(f"Error handling vehicle control: {str(e)}")
            return False 