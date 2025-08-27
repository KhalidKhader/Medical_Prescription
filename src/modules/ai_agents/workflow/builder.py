"""
Workflow Builder - Factory for creating prescription processing workflows
Provides a clean interface for building and configuring workflows
"""

from typing import Dict, Any, Optional
from .orchestrator import PrescriptionOrchestrator
from src.core.settings.logging import logger
from src.core.settings.config import settings


def build_prescription_workflow(
    config: Optional[Dict[str, Any]] = None
) -> PrescriptionOrchestrator:
    """
    Build prescription processing workflow with optional configuration
    
    Args:
        config: Optional workflow configuration
        
    Returns:
        Configured prescription orchestrator
    """
    try:
        logger.info("Building prescription processing workflow")
        
        # Create orchestrator with default configuration
        orchestrator = PrescriptionOrchestrator()
        
        # Apply custom configuration if provided
        if config:
            logger.info(f"Applying custom workflow configuration: {config}")
            # Configuration can be applied here if needed
        
        logger.info("Prescription workflow built successfully")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to build prescription workflow: {e}")
        raise

    """
    Validate workflow configuration
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
    """
    required_keys = []  # Add required configuration keys if needed
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration key: {key}")
            return False
    
    # Validate specific configuration values
    max_retries = config.get("max_retries")
    if max_retries is not None and (max_retries < 0 or max_retries > 10):
        logger.error(f"Invalid max_retries value: {max_retries}")
        return False
    
    logger.info("Workflow configuration validated successfully")
    return True