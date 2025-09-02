"""
Prescriber Agent Tools
Contains tools for processing and validating prescriber information
"""

from typing import Dict, Any, Optional, Tuple
import re
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.settings.logging import logger


def validate_npi_number(npi: str) -> Tuple[bool, str]:
    """
    Validate NPI number format (should be 10 digits)
    
    Args:
        npi: NPI number to validate
        
    Returns:
        Tuple of (is_valid, cleaned_npi)
    """
    if not npi or not npi.strip():
        return False, ""
    
    # Remove all non-digit characters using string filtering
    cleaned_npi = ''.join(c for c in npi.strip() if c.isdigit())
    
    # NPI should be exactly 10 digits
    if len(cleaned_npi) == 10:
        return True, cleaned_npi
    
    return False, cleaned_npi


def validate_dea_number(dea: str) -> Tuple[bool, str]:
    """
    Validate DEA number format (should start with letter followed by digits)
    
    Args:
        dea: DEA number to validate
        
    Returns:
        Tuple of (is_valid, cleaned_dea)
    """
    if not dea or not dea.strip():
        return False, ""
    
    cleaned_dea = dea.strip().upper()
    
    # DEA format: 1 letter + 6-7 digits (sometimes with additional characters)
    if len(cleaned_dea) >= 7 and cleaned_dea[0].isalpha():
        # Extract the core DEA format using string slicing
        letter = cleaned_dea[0]
        digits = ''.join(c for c in cleaned_dea[1:] if c.isdigit())
        if len(digits) >= 6:
            core_dea = letter + digits[:7]  # Take first 7 digits max
            return True, core_dea
    
    return False, cleaned_dea


def validate_contact_number(phone: str) -> Tuple[bool, str]:
    """
    Validate and format contact number
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple of (is_valid, formatted_phone)
    """
    if not phone or not phone.strip():
        return False, ""
    
    # Extract digits only using string filtering
    digits = ''.join(c for c in phone.strip() if c.isdigit())
    
    # US phone numbers should have 10 digits (with area code)
    if len(digits) == 10:
        # Format as (XXX) XXX-XXXX
        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return True, formatted
    elif len(digits) == 11 and digits[0] == '1':
        # Handle numbers with country code
        formatted = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return True, formatted
    
    return False, digits


def validate_prescriber_name(name: str) -> Tuple[bool, str]:
    """
    Validate prescriber name format
    
    Args:
        name: Prescriber name to validate
        
    Returns:
        Tuple of (is_valid, cleaned_name)
    """
    if not name or not name.strip():
        return False, ""
    
    cleaned_name = name.strip()
    
    # Check for minimum length
    if len(cleaned_name) < 3:
        return False, cleaned_name
    
    # Should contain letters and may contain common medical prefixes/suffixes
    if any(c.isalpha() for c in cleaned_name):
        # Proper case formatting
        cleaned_name = ' '.join(word.capitalize() for word in cleaned_name.split())
        return True, cleaned_name
    
    return False, cleaned_name


def extract_prescriber_quality_metrics(prescriber_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract quality metrics for prescriber data
    
    Args:
        prescriber_data: Prescriber information dictionary
        
    Returns:
        Quality metrics dictionary
    """
    metrics = {
        "completeness_score": 0,
        "has_full_name": bool(prescriber_data.get("full_name")),
        "has_npi": bool(prescriber_data.get("npi_number")),
        "has_dea": bool(prescriber_data.get("dea_number")),
        "has_license": bool(prescriber_data.get("state_license_number")),
        "has_address": bool(prescriber_data.get("address")),
        "has_contact": bool(prescriber_data.get("contact_number")),
        "data_quality_issues": []
    }
    
    # Calculate completeness score
    total_fields = 6  # full_name, state_license_number, npi_number, dea_number, address, contact_number
    filled_fields = sum([
        bool(prescriber_data.get("full_name")),
        bool(prescriber_data.get("state_license_number")),
        bool(prescriber_data.get("npi_number")),
        bool(prescriber_data.get("dea_number")),
        bool(prescriber_data.get("address")),
        bool(prescriber_data.get("contact_number"))
    ])
    
    metrics["completeness_score"] = (filled_fields / total_fields) * 100
    
    # Validate individual fields
    if prescriber_data.get("npi_number"):
        is_valid, _ = validate_npi_number(prescriber_data["npi_number"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid NPI number format")
    
    if prescriber_data.get("dea_number"):
        is_valid, _ = validate_dea_number(prescriber_data["dea_number"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid DEA number format")
    
    if prescriber_data.get("contact_number"):
        is_valid, _ = validate_contact_number(prescriber_data["contact_number"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid contact number format")
    
    if prescriber_data.get("full_name"):
        is_valid, _ = validate_prescriber_name(prescriber_data["full_name"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid name format")
    
    return metrics


def repair_prescriber_json(json_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Repair and validate prescriber JSON using json_repair
    
    Args:
        json_text: Raw JSON text
        
    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    try:
        parsed_data = parse_json(json_text)
        
        if not parsed_data:
            return False, None, "Failed to parse JSON"
        
        # Ensure we have a dictionary, not a string
        if isinstance(parsed_data, str):
            # If it's still a string, try to parse again
            parsed_data = parse_json(parsed_data)
            if not parsed_data:
                return False, None, "Failed to parse JSON after second attempt"
        
        # Make a copy to avoid modifying original
        working_data = dict(parsed_data) if isinstance(parsed_data, dict) else {}
        
        # Ensure all expected fields are present
        expected_fields = ["full_name", "state_license_number", "npi_number", "dea_number", "address", "contact_number", "certainty"]
        for field in expected_fields:
            if field not in working_data:
                working_data[field] = None
        
        # Validate and clean specific fields
        if working_data.get("npi_number"):
            is_valid, cleaned_npi = validate_npi_number(working_data["npi_number"])
            if is_valid:
                working_data["npi_number"] = cleaned_npi
        
        if working_data.get("dea_number"):
            is_valid, cleaned_dea = validate_dea_number(working_data["dea_number"])
            if is_valid:
                working_data["dea_number"] = cleaned_dea
        
        if working_data.get("contact_number"):
            is_valid, formatted_phone = validate_contact_number(working_data["contact_number"])
            if is_valid:
                working_data["contact_number"] = formatted_phone
        
        # Validate certainty score
        if working_data.get("certainty") is not None:
            try:
                certainty = int(working_data["certainty"])
                if certainty < 0 or certainty > 100:
                    working_data["certainty"] = 50  # Default if invalid
            except (ValueError, TypeError):
                working_data["certainty"] = 50
        
        logger.info("Successfully repaired and validated prescriber JSON")
        return True, working_data, None
        
    except Exception as e:
        logger.error(f"Prescriber JSON repair failed: {e}")
        return False, None, str(e)
