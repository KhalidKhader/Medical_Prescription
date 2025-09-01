"""
Prescription Processing Service
Main service for processing prescription images through AI agents
"""

import uuid
import json
import io
from typing import Dict, Any, Optional
from datetime import datetime
from PIL import Image

from src.core.settings.logging import logger
from src.core.settings.config import settings
from src.modules.ai_agents.workflow.streamlined_orchestrator import build_prescription_workflow


class PrescriptionProcessingService:
    """
    Main service for processing prescription images using AI agents.
    """
    
    def __init__(self):
        """Initialize the prescription processing service"""
        self.workflow = build_prescription_workflow()
        logger.info("Prescription processing service initialized")
    
    async def process_prescription_image(
        self,
        image_base64: str,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a prescription image using the complete AI agent workflow.
        
        Args:
            image_base64: Base64 encoded prescription image
            request_metadata: Optional request metadata
            
        Returns:
            Processing result with extracted prescription data
        """
        
        processing_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting prescription processing: {processing_id}")
        
        try:
            # Create initial workflow state
            initial_state = {
                "image_base64": image_base64,
                "retry_count": 0
            }
            
            # Execute the workflow
            logger.info("Executing prescription processing workflow")
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Extract results
            final_json_output = final_state.get("final_json_output")
            quality_warnings = final_state.get("quality_warnings", [])
            
            # Parse the final JSON output
            try:
                prescription_data = json.loads(final_json_output) if final_json_output else {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse final JSON output: {e}")
                prescription_data = {"error": "Failed to parse final output"}
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Prepare response
            return {
                "processing_id": processing_id,
                "status": "completed",
                "processing_time_seconds": processing_time,
                "prescription_data": prescription_data,
                "quality_warnings": quality_warnings,
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "request_metadata": request_metadata or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Prescription processing failed: {e}")
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "processing_id": processing_id,
                "status": "failed",
                "processing_time_seconds": processing_time,
                "error": str(e),
                "prescription_data": None,
                "quality_warnings": [f"Processing failed: {str(e)}"],
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "request_metadata": request_metadata or {}
                }
            }
    
    async def validate_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Validate uploaded image format and size.
        
        Args:
            image_data: Raw image data
            
        Returns:
            Validation result
        """
        try:
            # Check file size
            if len(image_data) > settings.max_image_size_mb * 1024 * 1024:
                return {
                    "valid": False,
                    "error": f"Image size exceeds maximum allowed size of {settings.max_image_size_mb}MB"
                }
            
            # Validate image format
            image = Image.open(io.BytesIO(image_data))
            
            # Check if format is supported
            if image.format.lower() not in [fmt.lower() for fmt in settings.supported_image_formats_list]:
                return {
                    "valid": False,
                    "error": f"Unsupported image format. Supported formats: {', '.join(settings.supported_image_formats_list)}"
                }
            
            # Check image dimensions
            width, height = image.size
            if width < 100 or height < 100:
                return {
                    "valid": False,
                    "error": "Image dimensions too small. Minimum size: 100x100 pixels"
                }
            
            return {
                "valid": True,
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Image validation failed: {str(e)}"
            }
    
    def optimize_image(self, image_data: bytes) -> bytes:
        """
        Optimize image for processing.
        
        Args:
            image_data: Raw image data
            
        Returns:
            Optimized image data
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 2048x2048)
            max_size = 2048
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return image_data  # Return original if optimization fails
