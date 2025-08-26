"""
Request handlers for prescription processing.
Contains business logic handlers for processing prescription requests.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from src.core.settings.logging import logger
from src.modules.prescriptions_management.services import PrescriptionProcessingService
from src.modules.prescriptions_management.schema import (
    PrescriptionProcessingRequest,
    PrescriptionProcessingResponse,
    PrescriptionImageUploadResponse
)
import asyncio


class PrescriptionProcessingHandler:
    """
    Handler class for prescription processing operations.
    Provides business logic layer between routes and services.
    """
    
    def __init__(self):
        """Initialize the prescription processing handler"""
        self.service = PrescriptionProcessingService()
        logger.info("Prescription processing handler initialized")
    
    async def _validate_processing_request(
        self,
        request: PrescriptionProcessingRequest
    ) -> Dict[str, Any]:
        """Validate prescription processing request"""
        try:
            validation_result = {"valid": True, "errors": []}
            
            # Validate image ID
            if not request.image_id or not self._validate_image_id(request.image_id):
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid or missing image ID")
            
            # Validate processing options
            if request.processing_options:
                if not isinstance(request.processing_options, dict):
                    validation_result["valid"] = False
                    validation_result["errors"].append("Processing options must be a dictionary")
            
            # Set error message if validation failed
            if not validation_result["valid"]:
                validation_result["error"] = "; ".join(validation_result["errors"])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating processing request: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def _validate_processing_id(self, processing_id: str) -> bool:
        """Validate processing ID format"""
        try:
            import uuid
            uuid.UUID(processing_id)
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_image_id(self, image_id: str) -> bool:
        """Validate image ID format"""
        try:
            import uuid
            uuid.UUID(image_id)
            return True
        except (ValueError, TypeError):
            return False
    
    
    def _get_quality_recommendation(self, confidence: float) -> str:
        """Get quality-based recommendation"""
        if confidence > 0.8:
            return "Data quality is high - ready for use"
        elif confidence > 0.6:
            return "Data quality is medium - review recommended"
        else:
            return "Data quality is low - manual verification required"
