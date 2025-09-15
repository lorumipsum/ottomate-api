"""
Guardrails for token and time limits in OttoMate API.
"""

import time
import threading
from typing import Dict, Any
from datetime import datetime, timedelta

class Guardrails:
    """Manages usage limits and guardrails for API operations."""
    
    def __init__(self):
        # Daily limits
        self.daily_request_limit = 100
        self.daily_token_limit = 50000
        
        # Per-request limits
        self.max_tokens_per_request = 3000
        self.max_time_per_request = 60  # seconds
        
        # Usage tracking
        self.usage_data = {
            "daily_requests": 0,
            "daily_tokens": 0,
            "last_reset": time.time()
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def check_daily_limits(self) -> Dict[str, Any]:
        """Check if daily limits have been exceeded."""
        with self.lock:
            self._reset_if_new_day()
            
            return {
                "requests_ok": self.usage_data["daily_requests"] < self.daily_request_limit,
                "tokens_ok": self.usage_data["daily_tokens"] < self.daily_token_limit,
                "requests_used": self.usage_data["daily_requests"],
                "requests_limit": self.daily_request_limit,
                "tokens_used": self.usage_data["daily_tokens"],
                "tokens_limit": self.daily_token_limit
            }
    
    def record_usage(self, tokens_used: int = 0):
        """Record usage for guardrails tracking."""
        with self.lock:
            self._reset_if_new_day()
            self.usage_data["daily_requests"] += 1
            self.usage_data["daily_tokens"] += tokens_used
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        with self.lock:
            self._reset_if_new_day()
            
            return {
                "daily_limits": {
                    "requests": {
                        "used": self.usage_data["daily_requests"],
                        "limit": self.daily_request_limit,
                        "remaining": max(0, self.daily_request_limit - self.usage_data["daily_requests"])
                    },
                    "tokens": {
                        "used": self.usage_data["daily_tokens"],
                        "limit": self.daily_token_limit,
                        "remaining": max(0, self.daily_token_limit - self.usage_data["daily_tokens"])
                    }
                },
                "per_request_limits": {
                    "max_tokens": self.max_tokens_per_request,
                    "max_time_seconds": self.max_time_per_request
                },
                "last_reset": self.usage_data["last_reset"],
                "next_reset": self._get_next_reset_time()
            }
    
    def _reset_if_new_day(self):
        """Reset daily counters if it's a new day."""
        current_time = time.time()
        last_reset = self.usage_data["last_reset"]
        
        # Check if it's been more than 24 hours
        if current_time - last_reset >= 24 * 60 * 60:
            self.usage_data["daily_requests"] = 0
            self.usage_data["daily_tokens"] = 0
            self.usage_data["last_reset"] = current_time
    
    def _get_next_reset_time(self) -> float:
        """Get the timestamp for the next daily reset."""
        return self.usage_data["last_reset"] + (24 * 60 * 60)

# Global instance
guardrails = Guardrails()
