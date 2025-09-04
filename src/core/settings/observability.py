"""
Observability and audit logging for prescription processing system.
Integrates with LangFuse for comprehensive monitoring and compliance.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger


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