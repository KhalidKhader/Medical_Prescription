"""
Patient Info Agent Tools
Contains tools for processing and validating patient information
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import re
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.settings.logging import logger


def validate_patient_name(name: str) -> Tuple[bool, str]:
    """
    Validate patient name format
    
    Args:
        name: Patient name to validate
        
    Returns:
        Tuple of (is_valid, cleaned_name)
    """
    if not name or not name.strip():
        return False, ""
    
    cleaned_name = name.strip()
    
    # Check for minimum length
    if len(cleaned_name) < 2:
        return False, cleaned_name
    
    # Check for invalid characters using character checking
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-')
    if not all(c in allowed_chars for c in cleaned_name):
        return False, cleaned_name
    
    # Proper case formatting
    cleaned_name = ' '.join(word.capitalize() for word in cleaned_name.split())
    
    return True, cleaned_name


def validate_date_of_birth(dob: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate and standardize date of birth
    
    Args:
        dob: Date of birth string
        
    Returns:
        Tuple of (is_valid, standardized_date, calculated_age)
    """
    if not dob or not dob.strip():
        return False, None, None
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',    # 2023-01-15
        '%m/%d/%Y',    # 01/15/2023
        '%d/%m/%Y',    # 15/01/2023
        '%m-%d-%Y',    # 01-15-2023
        '%d-%m-%Y',    # 15-01-2023
        '%B %d, %Y',   # January 15, 2023
        '%b %d, %Y',   # Jan 15, 2023
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(dob.strip(), date_format)
            
            # Check if date is reasonable (not in future, not too old)
            current_year = datetime.now().year
            if parsed_date.year > current_year or parsed_date.year < 1900:
                continue
            
            # Calculate age
            today = datetime.now()
            age = today.year - parsed_date.year
            if today.month < parsed_date.month or (today.month == parsed_date.month and today.day < parsed_date.day):
                age -= 1
            
            # Standardize to YYYY-MM-DD format
            standardized_date = parsed_date.strftime('%Y-%m-%d')
            
            return True, standardized_date, age
            
        except ValueError:
            logger.error("Failed to parse date of birth")
            continue
    
    return False, None, None


def check_age_dob_consistency(age: str, dob: str) -> bool:
    """
    Check consistency between age and date of birth
    
    Args:
        age: Provided age
        dob: Date of birth
        
    Returns:
        True if consistent, False otherwise
    """
    if not age or not dob:
        return True  # Can't check if either is missing
    
    try:
        provided_age = int(age.split()[0])  # Handle "25 years" format
        _, _, calculated_age = validate_date_of_birth(dob)
        
        if calculated_age is not None:
            # Allow 1 year tolerance
            return abs(provided_age - calculated_age) <= 1
        
    except (ValueError, TypeError):
        logger.warning("Failed to check age-DOB consistency")
        pass
    
    return False


def extract_patient_quality_metrics(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract quality metrics for patient data
    
    Args:
        patient_data: Patient information dictionary
        
    Returns:
        Quality metrics dictionary
    """
    metrics = {
        "completeness_score": 0,
        "has_full_name": bool(patient_data.get("full_name")),
        "has_dob": bool(patient_data.get("date_of_birth")),
        "has_age": bool(patient_data.get("age")),
        "has_address": bool(patient_data.get("address")),
        "age_dob_consistent": True,
        "data_quality_issues": []
    }
    
    # Calculate completeness score
    total_fields = 5  # full_name, date_of_birth, age, facility_name, address
    filled_fields = sum([
        bool(patient_data.get("full_name")),
        bool(patient_data.get("date_of_birth")),
        bool(patient_data.get("age")),
        bool(patient_data.get("facility_name")),
        bool(patient_data.get("address"))
    ])
    
    metrics["completeness_score"] = (filled_fields / total_fields) * 100
    
    # Check age-DOB consistency
    if patient_data.get("age") and patient_data.get("date_of_birth"):
        metrics["age_dob_consistent"] = check_age_dob_consistency(
            patient_data["age"], 
            patient_data["date_of_birth"]
        )
        
        if not metrics["age_dob_consistent"]:
            metrics["data_quality_issues"].append("Age inconsistent with date of birth")
    
    # Validate name format
    if patient_data.get("full_name"):
        is_valid, _ = validate_patient_name(patient_data["full_name"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid name format")
    
    return metrics


def repair_patient_json(json_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Repair and validate patient JSON using json_repair
    
    Args:
        json_text: Raw JSON text
        
    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    try:
        parsed_data = parse_json(json_text)
        
        if not parsed_data:
            return False, None, "Failed to parse JSON"
        
        # Ensure all expected fields are present
        expected_fields = ["full_name", "date_of_birth", "age", "facility_name", "address", "certainty"]
        for field in expected_fields:
            if field not in parsed_data:
                parsed_data[field] = None
        
        # Validate certainty score
        if parsed_data.get("certainty") is not None:
            try:
                certainty = int(parsed_data["certainty"])
                if certainty < 0 or certainty > 100:
                    parsed_data["certainty"] = 50  # Default if invalid
            except (ValueError, TypeError):
                parsed_data["certainty"] = 50
        
        logger.info("Successfully repaired and validated patient JSON")
        return True, parsed_data, None
        
    except Exception as e:
        logger.error(f"Patient JSON repair failed: {e}")
        return False, None, str(e)
