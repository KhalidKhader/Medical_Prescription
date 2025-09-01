"""
FastAPI router for prescription processing endpoints.
Handles prescription image upload and processing with AI agents.
"""

from fastapi import APIRouter, UploadFile, File, Depends
from src.modules.prescriptions_management.handlers import PrescriptionProcessingHandler
from src.modules.prescriptions_management.schema import PrescriptionProcessingResponse

# Create router instance
router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

# Dependency to get processing handler
def get_processing_handler() -> PrescriptionProcessingHandler:
    """Get prescription processing handler instance"""
    return PrescriptionProcessingHandler()


@router.post(
    "/upload",
    summary="Upload and process prescription image",
    description="Upload a prescription image and process it using AI agents to extract structured data",
    response_model=PrescriptionProcessingResponse
)
async def upload_and_process_prescription(
    file: UploadFile = File(..., description="Prescription image file"),
    processing_handler: PrescriptionProcessingHandler = Depends(get_processing_handler)
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
    
    # Read file data
    file_data = await file.read()
    
    # Delegate to handler for business logic
    result = await processing_handler.handle_prescription_upload(
        file_data=file_data,
        filename=file.filename,
        content_type=file.content_type
    )
    
    return PrescriptionProcessingResponse(**result)
