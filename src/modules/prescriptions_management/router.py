"""
FastAPI router for prescription processing endpoints.
Handles prescription image upload and processing with AI agents.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uuid
import base64
import os
from PIL import Image
import io

from src.modules.prescriptions_management.services import PrescriptionProcessingService
from src.modules.prescriptions_management.schema import (
    PrescriptionProcessingResponse
)
from src.core.settings.logging import logger
from src.core.settings.config import settings

# Create router instance
router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

# Dependency to get processing service
def get_processing_service() -> PrescriptionProcessingService:
    """Get prescription processing service instance"""
    return PrescriptionProcessingService()


@router.post(
    "/upload",
    summary="Upload and process prescription image",
    description="Upload a prescription image and process it using AI agents to extract structured data",
    response_model=PrescriptionProcessingResponse
)
async def upload_and_process_prescription(
    file: UploadFile = File(..., description="Prescription image file"),
    processing_service: PrescriptionProcessingService = Depends(get_processing_service)
):
    """
    Upload and process a prescription image using AI agents.
    
    This endpoint:
    1. Validates the uploaded image
    2. Optimizes the image for processing
    3. Runs the complete AI agent workflow including:
       - Image extraction with Gemini 2.5 Pro
       - Data validation and schema correction
       - Medication processing with RxNorm mapping
       - Spanish translation
       - Quality assurance and supervision
    4. Returns the structured prescription data
    
    Args:
        file: Prescription image file (JPEG, PNG, PDF)
        
    Returns:
        Structured prescription data with processing metadata
    """
    
    try:
        logger.info(f"Processing prescription upload: {file.filename}")
        
        # Read file data
        file_data = await file.read()
        
        # Validate image
        validation_result = await processing_service.validate_image(file_data)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["error"]
            )
        
        # Optimize image
        optimized_image_data = processing_service.optimize_image(file_data)
        
        # Convert to base64
        image_base64 = base64.b64encode(optimized_image_data).decode('utf-8')
        
        # Process prescription with AI agents
        result = await processing_service.process_prescription_image(
            image_base64=image_base64,
            request_metadata={
                "filename": file.filename,
                "file_size": len(file_data),
                "content_type": file.content_type,
                "validation_result": validation_result
            }
        )
        
        logger.info(f"Prescription processing completed: {result['processing_id']}")
        
        return PrescriptionProcessingResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing prescription upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process prescription: {str(e)}"
        )
