"""
Deployment module for managing system deployment and updates.
"""
import logging
import asyncio
import json
import shutil
from pathlib import Path
import time
from typing import Dict, Any, List, Optional
import aiohttp
import docker
from docker.errors import DockerException

from config import settings

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Handles system deployment and updates."""
    
    def __init__(self):
        """Initialize the deployment manager."""
        self.deployment_file = Path(settings.DATA_DIR) / "deployment_status.json"
        self.deployment_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._status: Dict[str, Any] = self._load_status()
        self._status_lock = asyncio.Lock()
        
        # Initialize Docker client
        try:
            self._docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self._docker_client = None
        
        # Deployment configuration
        self._config = {
            "backup_dir": Path(settings.DATA_DIR) / "backups",
            "update_timeout": 300,  # 5 minutes
            "rollback_timeout": 180,  # 3 minutes
            "health_check_interval": 10,  # 10 seconds
            "max_retries": 3
        }
        
        # Create backup directory
        self._config["backup_dir"].mkdir(parents=True, exist_ok=True)
        
        logger.info("Deployment manager initialized")
    
    def _load_status(self) -> Dict[str, Any]:
        """
        Load deployment status from file.
        
        Returns:
            Dict[str, Any]: Loaded status
        """
        if self.deployment_file.exists():
            try:
                with open(self.deployment_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading deployment status: {str(e)}")
                return self._get_default_status()
        else:
            return self._get_default_status()
    
    def _get_default_status(self) -> Dict[str, Any]:
        """
        Get default deployment status.
        
        Returns:
            Dict[str, Any]: Default status
        """
        return {
            "version": "1.0.0",
            "status": "stable",
            "last_update": None,
            "components": {
                "asr": {"version": "1.0.0", "status": "stable"},
                "nlu": {"version": "1.0.0", "status": "stable"},
                "dialogue": {"version": "1.0.0", "status": "stable"},
                "tts": {"version": "1.0.0", "status": "stable"},
                "vehicle": {"version": "1.0.0", "status": "stable"}
            },
            "backup": {
                "last_backup": None,
                "backup_path": None
            }
        }
    
    async def _save_status(self):
        """Save deployment status to file."""
        try:
            with open(self.deployment_file, "w") as f:
                json.dump(self._status, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving deployment status: {str(e)}")
            raise
    
    async def create_backup(self) -> Dict[str, Any]:
        """
        Create a system backup.
        
        Returns:
            Dict[str, Any]: Backup information
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = self._config["backup_dir"] / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration
            shutil.copytree(
                settings.CONFIG_DIR,
                backup_path / "config",
                dirs_exist_ok=True
            )
            
            # Backup data
            shutil.copytree(
                settings.DATA_DIR,
                backup_path / "data",
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("backups/*")
            )
            
            # Update status
            async with self._status_lock:
                self._status["backup"] = {
                    "last_backup": timestamp,
                    "backup_path": str(backup_path)
                }
                await self._save_status()
            
            return {
                "status": "success",
                "backup_path": str(backup_path),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Restore system from backup.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            Dict[str, Any]: Restore status
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                raise ValueError("Backup path does not exist")
            
            # Restore configuration
            shutil.copytree(
                backup_path / "config",
                settings.CONFIG_DIR,
                dirs_exist_ok=True
            )
            
            # Restore data
            shutil.copytree(
                backup_path / "data",
                settings.DATA_DIR,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("backups/*")
            )
            
            # Update status
            async with self._status_lock:
                self._status = self._load_status()
                await self._save_status()
            
            return {
                "status": "success",
                "restored_from": str(backup_path)
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def update_component(self, component: str, version: str) -> Dict[str, Any]:
        """
        Update a system component.
        
        Args:
            component: Component name
            version: New version
            
        Returns:
            Dict[str, Any]: Update status
        """
        try:
            if component not in self._status["components"]:
                raise ValueError(f"Unknown component: {component}")
            
            # Create backup before update
            backup_info = await self.create_backup()
            if backup_info["status"] == "error":
                raise Exception("Failed to create backup before update")
            
            # Update component
            async with self._status_lock:
                self._status["components"][component]["version"] = version
                self._status["components"][component]["status"] = "updating"
                await self._save_status()
            
            # Simulate update process
            await asyncio.sleep(2)
            
            # Update status
            async with self._status_lock:
                self._status["components"][component]["status"] = "stable"
                self._status["version"] = version
                self._status["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
                await self._save_status()
            
            return {
                "status": "success",
                "component": component,
                "version": version,
                "backup": backup_info
            }
            
        except Exception as e:
            logger.error(f"Error updating component {component}: {str(e)}")
            
            # Rollback on failure
            try:
                await self.restore_backup(backup_info["backup_path"])
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            
            return {
                "status": "error",
                "component": component,
                "error": str(e)
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check system health.
        
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            health_status = {
                "status": "healthy",
                "components": {},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Check Docker containers
            if self._docker_client:
                containers = self._docker_client.containers.list()
                for container in containers:
                    health_status["components"][container.name] = {
                        "status": container.status,
                        "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
                    }
            
            # Check component status
            async with self._status_lock:
                for component, info in self._status["components"].items():
                    health_status["components"][component] = {
                        "version": info["version"],
                        "status": info["status"]
                    }
            
            # Check for any unhealthy components
            for component, info in health_status["components"].items():
                if info["status"] not in ["stable", "running", "healthy"]:
                    health_status["status"] = "unhealthy"
                    break
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    async def get_deployment_info(self) -> Dict[str, Any]:
        """
        Get deployment information.
        
        Returns:
            Dict[str, Any]: Deployment information
        """
        async with self._status_lock:
            return {
                "version": self._status["version"],
                "status": self._status["status"],
                "last_update": self._status["last_update"],
                "components": self._status["components"],
                "backup": self._status["backup"]
            } 