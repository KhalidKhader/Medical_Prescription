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


def prepare_image_data(image_base64: str) -> str:
    """
    Prepare image data for Gemini Vision processing
    
    Args:
        image_base64: Base64 encoded image
        
    Returns:
        Formatted image URL for Gemini
    """
    return f"data:image/jpeg;base64,{image_base64}"


def extract_quality_metrics(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract quality metrics from extracted prescription data
    
    Args:
        extracted_data: Parsed prescription data
        
    Returns:
        Quality metrics dictionary
    """
    metrics = {
        "has_prescriber_data": bool(extracted_data.get("prescriber", {}).get("full_name")),
        "has_patient_data": bool(extracted_data.get("patient", {}).get("full_name")),
        "medication_count": len(extracted_data.get("medications", [])),
        "has_date": bool(extracted_data.get("date_prescription_written")),
        "avg_certainty": 0
    }
    
    # Calculate average certainty
    certainties = []
    
    # Add prescriber certainty
    prescriber_cert = extracted_data.get("prescriber", {}).get("certainty")
    if prescriber_cert is not None:
        certainties.append(prescriber_cert)
    
    # Add patient certainty
    patient_cert = extracted_data.get("patient", {}).get("certainty")
    if patient_cert is not None:
        certainties.append(patient_cert)
    
    # Add medication certainties
    for med in extracted_data.get("medications", []):
        med_cert = med.get("certainty")
        if med_cert is not None:
            certainties.append(med_cert)
    
    if certainties:
        metrics["avg_certainty"] = sum(certainties) / len(certainties)
    
    return metrics
