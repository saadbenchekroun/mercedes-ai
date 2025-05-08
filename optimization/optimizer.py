"""
Optimization module for performance tuning.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import time
import psutil
import numpy as np
from sklearn.ensemble import IsolationForest

from config import settings

logger = logging.getLogger(__name__)

class Optimizer:
    """Handles performance optimization and monitoring."""
    
    def __init__(self):
        """Initialize the optimizer."""
        self.metrics_file = Path(settings.DATA_DIR) / "performance_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._metrics: Dict[str, Any] = self._load_metrics()
        self._metrics_lock = asyncio.Lock()
        
        # Initialize anomaly detection
        self._anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Performance thresholds
        self._thresholds = {
            "cpu_usage": 80.0,  # 80% CPU usage
            "memory_usage": 80.0,  # 80% memory usage
            "response_time": 1.0,  # 1 second
            "error_rate": 0.05  # 5% error rate
        }
        
        logger.info("Optimizer initialized")
    
    def _load_metrics(self) -> Dict[str, Any]:
        """
        Load performance metrics from file.
        
        Returns:
            Dict[str, Any]: Loaded metrics
        """
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metrics: {str(e)}")
                return self._get_default_metrics()
        else:
            return self._get_default_metrics()
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """
        Get default metrics structure.
        
        Returns:
            Dict[str, Any]: Default metrics
        """
        return {
            "system": {
                "cpu_usage": [],
                "memory_usage": [],
                "disk_usage": [],
                "network_usage": []
            },
            "application": {
                "response_time": [],
                "error_rate": [],
                "request_count": [],
                "cache_hits": []
            },
            "models": {
                "asr_accuracy": [],
                "intent_accuracy": [],
                "entity_accuracy": [],
                "response_time": []
            }
        }
    
    async def _save_metrics(self):
        """Save metrics to file."""
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(self._metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
            raise
    
    async def record_metric(self, category: str, metric: str, value: float):
        """
        Record a performance metric.
        
        Args:
            category: Metric category
            metric: Metric name
            value: Metric value
        """
        async with self._metrics_lock:
            if category in self._metrics and metric in self._metrics[category]:
                self._metrics[category][metric].append({
                    "timestamp": time.time(),
                    "value": value
                })
                
                # Keep only last 1000 measurements
                if len(self._metrics[category][metric]) > 1000:
                    self._metrics[category][metric] = self._metrics[category][metric][-1000:]
                
                await self._save_metrics()
    
    async def get_metrics(self, category: str, metric: str, window: int = 100) -> List[float]:
        """
        Get recent metric values.
        
        Args:
            category: Metric category
            metric: Metric name
            window: Number of recent values to return
            
        Returns:
            List[float]: Recent metric values
        """
        async with self._metrics_lock:
            if category in self._metrics and metric in self._metrics[category]:
                values = [m["value"] for m in self._metrics[category][metric]]
                return values[-window:]
            return []
    
    async def check_performance(self) -> Dict[str, bool]:
        """
        Check if performance metrics are within thresholds.
        
        Returns:
            Dict[str, bool]: Performance status
        """
        async with self._metrics_lock:
            status = {}
            
            # Check system metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            status["cpu_usage"] = cpu_usage < self._thresholds["cpu_usage"]
            status["memory_usage"] = memory_usage < self._thresholds["memory_usage"]
            
            # Check application metrics
            response_times = await self.get_metrics("application", "response_time")
            error_rates = await self.get_metrics("application", "error_rate")
            
            if response_times:
                status["response_time"] = np.mean(response_times) < self._thresholds["response_time"]
            if error_rates:
                status["error_rate"] = np.mean(error_rates) < self._thresholds["error_rate"]
            
            return status
    
    async def detect_anomalies(self, category: str, metric: str) -> List[bool]:
        """
        Detect anomalies in metric values.
        
        Args:
            category: Metric category
            metric: Metric name
            
        Returns:
            List[bool]: Anomaly flags
        """
        async with self._metrics_lock:
            values = await self.get_metrics(category, metric)
            if not values:
                return []
            
            # Reshape for sklearn
            X = np.array(values).reshape(-1, 1)
            
            # Fit and predict
            self._anomaly_detector.fit(X)
            predictions = self._anomaly_detector.predict(X)
            
            # Convert predictions to boolean flags
            return [pred == -1 for pred in predictions]
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """
        Optimize system performance.
        
        Returns:
            Dict[str, Any]: Optimization results
        """
        try:
            # Check current performance
            status = await self.check_performance()
            
            # Collect optimization suggestions
            suggestions = []
            
            if not status.get("cpu_usage", True):
                suggestions.append({
                    "component": "system",
                    "issue": "high_cpu_usage",
                    "suggestion": "Consider reducing concurrent operations or optimizing CPU-intensive tasks"
                })
            
            if not status.get("memory_usage", True):
                suggestions.append({
                    "component": "system",
                    "issue": "high_memory_usage",
                    "suggestion": "Consider implementing memory cleanup or reducing memory footprint"
                })
            
            if not status.get("response_time", True):
                suggestions.append({
                    "component": "application",
                    "issue": "slow_response_time",
                    "suggestion": "Consider optimizing database queries or implementing caching"
                })
            
            if not status.get("error_rate", True):
                suggestions.append({
                    "component": "application",
                    "issue": "high_error_rate",
                    "suggestion": "Review error handling and implement better error recovery"
                })
            
            # Check for anomalies
            for category in self._metrics:
                for metric in self._metrics[category]:
                    anomalies = await self.detect_anomalies(category, metric)
                    if any(anomalies):
                        suggestions.append({
                            "component": category,
                            "issue": f"anomaly_in_{metric}",
                            "suggestion": f"Investigate unusual patterns in {metric}"
                        })
            
            return {
                "status": status,
                "suggestions": suggestions,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing performance: {str(e)}")
            return {
                "status": {},
                "suggestions": [],
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Dict[str, Any]: Performance summary
        """
        async with self._metrics_lock:
            summary = {}
            
            for category in self._metrics:
                summary[category] = {}
                for metric in self._metrics[category]:
                    values = [m["value"] for m in self._metrics[category][metric]]
                    if values:
                        summary[category][metric] = {
                            "mean": np.mean(values),
                            "std": np.std(values),
                            "min": np.min(values),
                            "max": np.max(values),
                            "latest": values[-1]
                        }
            
            return summary 