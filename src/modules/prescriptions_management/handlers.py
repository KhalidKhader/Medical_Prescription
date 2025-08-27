"""
Request handlers for prescription processing.
Contains business logic handlers for processing prescription requests.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from src.core.settings.logging import logger
from src.modules.prescriptions_management.services import PrescriptionProcessingService
from src.modules.prescriptions_management.schema import (
    PrescriptionProcessingResponse
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
    
    async def handle_prescription_upload(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str
    ) -> Dict[str, Any]:
        """
        Handle prescription image upload and processing.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            content_type: File content type
            
        Returns:
            Processing result with structured data
        """
        try:
            logger.info(f"Processing prescription upload: {filename}")
            
            # Validate image
            validation_result = await self.service.validate_image(file_data)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_result["error"]
                )
            
            # Optimize image
            optimized_image_data = self.service.optimize_image(file_data)
            
            # Convert to base64
            import base64
            image_base64 = base64.b64encode(optimized_image_data).decode('utf-8')
            
            # Process prescription with AI agents
            result = await self.service.process_prescription_image(
                image_base64=image_base64,
                request_metadata={
                    "filename": filename,
                    "file_size": len(file_data),
                    "content_type": content_type,
                    "validation_result": validation_result
                }
            )
            
            logger.info(f"Prescription processing completed: {result['processing_id']}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing prescription upload: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process prescription: {str(e)}"
            )
    

    

