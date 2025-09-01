"""
Pydantic models and schemas for prescription processing.
Defines the strict JSON structure for prescription data extraction.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PrescriptionProcessingResponse(BaseModel):
    """Response model for prescription processing"""
    processing_id: str = Field(..., description="Unique processing identifier")
    status: str = Field(..., description="Processing status (completed/failed)")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    prescription_data: Optional[Dict[str, Any]] = Field(None, description="Extracted prescription data")
    quality_warnings: List[str] = Field(default_factory=list, description="Quality warnings and issues")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
