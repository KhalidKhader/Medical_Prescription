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


def build_testing_workflow() -> PrescriptionOrchestrator:
    """
    Build workflow optimized for testing
    
    Returns:
        Testing-optimized orchestrator
    """
    logger.info("Building testing workflow")
    
    test_config = {
        "max_retries": 1,  # Faster testing
        "enable_hallucination_detection": True,
        "enable_spanish_translation": True,
        "enable_rxnorm_mapping": True
    }
    
    return build_prescription_workflow(test_config)


def build_production_workflow() -> PrescriptionOrchestrator:
    """
    Build workflow optimized for production
    
    Returns:
        Production-optimized orchestrator
    """
    logger.info("Building production workflow")
    
    production_config = {
        "max_retries": settings.max_agent_retries,
        "enable_comprehensive_validation": True,
        "enable_quality_assurance": True,
        "enable_audit_logging": True
    }
    
    return build_prescription_workflow(production_config)


def validate_workflow_configuration(config: Dict[str, Any]) -> bool:
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




def build_production_workflow() -> PrescriptionOrchestrator:
    """
    Build workflow optimized for production
    
    Returns:
        Production-optimized orchestrator
    """
    logger.info("Building production workflow")
    
    production_config = {
        "max_retries": settings.max_agent_retries,
        "enable_comprehensive_validation": True,
        "enable_quality_assurance": True,
        "enable_audit_logging": True
    }
    
    return build_prescription_workflow(production_config)


def validate_workflow_configuration(config: Dict[str, Any]) -> bool:
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