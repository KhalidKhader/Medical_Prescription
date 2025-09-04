
import io
from typing import Dict, Any
from datetime import datetime
from PIL import Image
from src.core.settings.config import settings


async def validate_image(image_data: bytes) -> Dict[str, Any]:
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
        logger.error(f"Image validation failed: {e}")