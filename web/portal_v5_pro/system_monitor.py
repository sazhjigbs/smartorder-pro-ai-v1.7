#!/usr/bin/env python3
"""
🔍 SAFELOGIC SmartOrder PRO — System Monitoring
Real-time logs, error tracking, API rate limits, latency monitoring
"""

import os
import time
import psutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import deque
import json

class SystemMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.api_calls = deque(maxlen=1000)  # Last 1000 API calls
        self.errors = deque(maxlen=100)  # Last 100 errors
        self.latency_samples = deque(maxlen=100)
        
    def get_uptime(self) -> str:
        """Get system uptime"""
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        return {
            "uptime": self.get_uptime(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "network_io": self._get_network_io(),
            "process_count": len(psutil.pids())
        }
    
    def _get_network_io(self) -> Dict:
        """Get network I/O stats"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except:
            return {}
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, latency_ms: float):
        """Log an API call"""
        self.request_count += 1
        
        call_data = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "latency_ms": latency_ms
        }
        
        self.api_calls.append(call_data)
        self.latency_samples.append(latency_ms)
        
        if status_code >= 400:
            self.error_count += 1
    
    def log_error(self, error_type: str, message: str, traceback: Optional[str] = None):
        """Log an error"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "traceback": traceback
        }
        self.errors.append(error_data)
    
    def get_api_stats(self) -> Dict:
        """Get API statistics"""
        if not self.api_calls:
            return {
                "total_requests": 0,
                "requests_per_minute": 0,
                "error_rate": 0,
                "avg_latency_ms": 0
            }
        
        # Calculate requests per minute
        now = datetime.now()
        one_min_ago = now - timedelta(minutes=1)
        recent_calls = [
            c for c in self.api_calls 
            if datetime.fromisoformat(c["timestamp"]) > one_min_ago
        ]
        
        return {
            "total_requests": self.request_count,
            "requests_per_minute": len(recent_calls),
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            "avg_latency_ms": sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0,
            "max_latency_ms": max(self.latency_samples) if self.latency_samples else 0,
            "min_latency_ms": min(self.latency_samples) if self.latency_samples else 0
        }
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors"""
        return list(self.errors)[-limit:]
    
    def get_health_status(self) -> Dict:
        """Get overall health status"""
        stats = self.get_system_stats()
        api_stats = self.get_api_stats()
        
        # Determine health status
        health = "healthy"
        issues = []
        
        if stats["cpu_percent"] > 80:
            health = "warning"
            issues.append("High CPU usage")
        
        if stats["memory_percent"] > 85:
            health = "warning"
            issues.append("High memory usage")
        
        if api_stats["error_rate"] > 10:
            health = "critical"
            issues.append("High error rate")
        
        if api_stats["avg_latency_ms"] > 1000:
            health = "warning"
            issues.append("High latency")
        
        return {
            "status": health,
            "issues": issues,
            "system": stats,
            "api": api_stats,
            "timestamp": datetime.now().isoformat()
        }

class RateLimitTracker:
    """Track API rate limits"""
    
    def __init__(self):
        self.limits = {
            "bybit": {"limit": 100, "window": 60, "calls": deque(maxlen=100)},
            "binance": {"limit": 1200, "window": 60, "calls": deque(maxlen=1200)},
            "telegram": {"limit": 30, "window": 1, "calls": deque(maxlen=30)}
        }
    
    def record_call(self, api: str):
        """Record an API call"""
        if api in self.limits:
            self.limits[api]["calls"].append(time.time())
    
    def get_remaining(self, api: str) -> int:
        """Get remaining calls for API"""
        if api not in self.limits:
            return -1
        
        limit_info = self.limits[api]
        window_start = time.time() - limit_info["window"]
        
        # Count calls in current window
        recent_calls = sum(1 for t in limit_info["calls"] if t > window_start)
        
        return max(0, limit_info["limit"] - recent_calls)
    
    def is_rate_limited(self, api: str) -> bool:
        """Check if API is rate limited"""
        return self.get_remaining(api) == 0
    
    def get_all_limits(self) -> Dict:
        """Get all rate limit info"""
        return {
            api: {
                "limit": info["limit"],
                "window_seconds": info["window"],
                "remaining": self.get_remaining(api),
                "is_limited": self.is_rate_limited(api)
            }
            for api, info in self.limits.items()
        }

# Global instances
system_monitor = SystemMonitor()
rate_limiter = RateLimitTracker()
