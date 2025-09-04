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


def optimize_image(image_data: bytes) -> bytes:
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
        logger.error(f"Image optimization failed: {e}")
        return image_data  # Return original if optimization fails
