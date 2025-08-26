"""
Prescriber Validation Agent Prompts
Contains prompts for validating prescriber information
"""

from typing import Dict, Any


def get_prescriber_validation_prompt(prescriber_data: Dict[str, Any]) -> str:
    """
    Get prompt for validating prescriber information
    
    Args:
        prescriber_data: Prescriber data to validate
        
    Returns:
        Validation prompt
    """
    return f"""
You are a pharmacy intern working under a supervising pharmacist. Review and validate the following prescriber information for pharmacist evaluation.

Prescriber data to validate:
{prescriber_data}

Validation tasks:
1. Validate NPI number format (should be 10 digits)
2. Validate DEA number format (should start with letter followed by digits)
3. Check state license number format
4. Verify contact number format
5. Ensure proper name formatting
6. Assign confidence scores

Return a validation report in JSON format:
{{
    "is_valid": boolean,
    "confidence": float (0.0-1.0),
    "errors": ["list of validation errors found"],
    "warnings": ["list of potential issues"],
    "validated_data": {{
        "full_name": "validated name or null",
        "state_license_number": "validated license or null",
        "npi_number": "validated NPI or null",
        "dea_number": "validated DEA or null",
        "address": "validated address or null",
        "contact_number": "validated contact or null",
        "certainty": "numeric 0-100"
    }}
}}

Focus on regulatory compliance and data accuracy for healthcare provider information.
"""
