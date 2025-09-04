"""
Prescription Processing Service
Main service for processing prescription images through AI agents
"""

from src.core.settings.logging import logger
from src.modules.ai_agents.workflow.streamlined_orchestrator import build_prescription_workflow
from src.core.services.image.process_prescription_image import process_prescription_image
from src.core.services.image.validate_image import validate_image
from src.core.services.image.optimize_image import optimize_image

class PrescriptionProcessingService:
    """
    Main service for processing prescription images using AI agents.
    """
    
    def __init__(self):
        """Initialize the prescription processing service"""
        self.process_prescription_image = process_prescription_image
        self.validate_image = validate_image
        self.optimize_image = optimize_image
        logger.info("Prescription processing service initialized")