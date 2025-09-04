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


workflow = build_prescription_workflow()
    
async def process_prescription_image(
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
        final_state = await workflow.ainvoke(initial_state)
        
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

   
    