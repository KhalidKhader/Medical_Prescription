"""
Image Extractor Agent Tools
Contains tools for image processing and JSON validation
"""

from typing import Dict, Any, Optional, Tuple
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.settings.logging import logger


def validate_extraction_json(json_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate extracted JSON using json_repair
    
    Args:
        json_text: Raw JSON text from extraction
        
    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    try:
        parsed_data = parse_json(json_text)
        
        if not parsed_data:
            return False, None, "Failed to parse JSON"
        
        # Basic structure validation
        required_keys = ["prescriber", "patient", "medications"]
        for key in required_keys:
            if key not in parsed_data:
                return False, None, f"Missing required key: {key}"
        
        # Ensure medications is a list
        if not isinstance(parsed_data.get("medications"), list):
            return False, None, "Medications must be a list"
        
        logger.info(f"Successfully validated extraction JSON with {len(parsed_data.get('medications', []))} medications")
        return True, parsed_data, None
        
    except Exception as e:
        logger.error(f"JSON validation error: {e}")
        return False, None, str(e)
