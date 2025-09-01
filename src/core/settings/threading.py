import asyncio
import time
import json
import hashlib
from typing import List, Dict, Optional, Union, Any, Callable
from dataclasses import dataclass
from functools import wraps
from datetime import datetime, timedelta
import random

# Performance and Caching Utilities for Medical Prescription Processing

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.timestamp + timedelta(seconds=self.ttl_seconds)

class InMemoryCache:
    """High-performance in-memory cache for RxNorm and Gemini responses"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self.hits += 1
                return entry.data
            else:
                del self._cache[key]
        self.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value with TTL"""
        if len(self._cache) >= self.max_size:
            # Remove oldest entries
            oldest_keys = sorted(self._cache.keys(), 
                               key=lambda k: self._cache[k].timestamp)[:10]
            for old_key in oldest_keys:
                del self._cache[old_key]
        
        self._cache[key] = CacheEntry(value, datetime.utcnow(), ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache)
        }

class CircuitBreaker:
    """Circuit breaker pattern for external API calls"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker OPEN - service unavailable")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (self.last_failure_time and 
                datetime.utcnow() > self.last_failure_time + timedelta(seconds=self.recovery_timeout))
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class PerformanceMonitor:
    """Monitor performance metrics for agents and API calls"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
    
    def record_timing(self, operation: str, duration: float):
        """Record operation timing"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        
        # Keep only last 100 measurements
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def increment_counter(self, counter: str):
        """Increment counter"""
        self.counters[counter] = self.counters.get(counter, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {"counters": self.counters, "timings": {}}
        
        for operation, timings in self.metrics.items():
            if timings:
                stats["timings"][operation] = {
                    "avg": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "count": len(timings)
                }
        return stats

# Global instances for system-wide use
global_cache = InMemoryCache(max_size=2000)
global_performance_monitor = PerformanceMonitor()

# Utility functions for agent optimization
async def parallel_agent_execution(tasks: List[Callable], max_concurrent: int = 3) -> List[Any]:
    """Execute multiple agent tasks in parallel with controlled concurrency"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:
            start_time = time.time()
            try:
                if asyncio.iscoroutinefunction(task):
                    result = await task()
                else:
                    result = task()
                
                duration = time.time() - start_time
                global_performance_monitor.record_timing(f"{task.__name__}_execution", duration)
                return result
            except Exception as e:
                global_performance_monitor.increment_counter(f"{task.__name__}_failures")
                raise e
    
    return await asyncio.gather(*[bounded_task(task) for task in tasks])

def performance_tracked(operation_name: str):
    """Decorator to track performance of agent operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                global_performance_monitor.record_timing(operation_name, duration)
                global_performance_monitor.increment_counter(f"{operation_name}_success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                global_performance_monitor.record_timing(operation_name, duration)
                global_performance_monitor.increment_counter(f"{operation_name}_failures")
                raise e
        return wrapper
    return decorator