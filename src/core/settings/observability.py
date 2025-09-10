"""
Observability and audit logging for prescription processing system.
Integrates with LangFuse for comprehensive monitoring and compliance.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Callable
from functools import wraps
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger


def performance_tracked(operation_name: str):
    """Decorator to track performance of operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{operation_name} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{operation_name} failed after {execution_time:.2f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{operation_name} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{operation_name} failed after {execution_time:.2f}s: {e}")
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


class AuditLogger:
    """Audit logger for prescription processing compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        if settings.langfuse_enabled:
            try:
                self.langfuse = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host,
                    timeout=settings.langfuse_timeout
                )
            except Exception as e:
                logger.error(f"LangFuse initialization failed: {e}")
                self.langfuse = None
        else:
            self.langfuse = None
    
    def log_prescription_processing(self, user_id: str, action: str, metadata: Dict[str, Any]):
        """Log prescription processing for compliance (no sensitive data)"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "image_processed": True,
            "agents_used": metadata.get("agents", []),
            "processing_time": metadata.get("processing_time"),
            "status": metadata.get("status")
        }
        
        # Log to file
        self.logger.info(f"AUDIT: {audit_entry}")
        
        # Log to LangFuse if available
        if self.langfuse:
            try:
                self.langfuse.create_event(
                    name="prescription_audit",
                    input=audit_entry
                )
            except Exception as e:
                # Silently fail on LangFuse errors
                logger.error(f"LangFuse error: {e}")
    
    def log_agent_execution(self, agent_name: str, execution_time: float, success: bool):
        """Log individual agent execution"""
        if self.langfuse:
            try:
                self.langfuse.create_event(
                    name=f"agent_{agent_name}_execution",
                    input={
                        "agent": agent_name,
                        "execution_time": execution_time,
                        "success": success,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                # Silently fail on LangFuse errors
                logger.error(f"LangFuse error: {e}")