"""
Prescriber Agent Prompts
Contains prompts for extracting and validating prescriber information
"""

from typing import Dict, Any


def get_prescriber_extraction_prompt() -> str:
    """
    Get prompt for extracting prescriber information from prescription
    
    Returns:
        Prescriber extraction prompt
    """
    return """
You are a pharmacy intern working under a supervising pharmacist. Extract ONLY prescriber/doctor information from prescription images for pharmacist review.

Extract the following prescriber information with maximum accuracy:
- Doctor's full name
- State license number
- NPI number (National Provider Identifier)
- DEA number (Drug Enforcement Administration)
- Address
- Contact number/phone

Rules:
1. Only extract information that is clearly visible in the image
2. Preserve exact spelling, abbreviations, and capitalization
3. Do not guess or infer missing information
4. Provide a certainty score (0-100) for the overall prescriber information

Return ONLY a JSON object with these exact keys:
{
    "full_name": "string or null",
    "state_license_number": "string or null",
    "npi_number": "string or null", 
    "dea_number": "string or null",
    "address": "string or null",
    "contact_number": "string or null",
    "certainty": "numeric 0-100"
}

If information is not visible, use null. Provide a certainty score based on the clarity and completeness of the visible prescriber information.
"""


def get_prescriber_validation_prompt(prescriber_data: Dict[str, Any]) -> str:
    """
    Get prompt for validating prescriber information
    
    Args:
        prescriber_data: Prescriber data to validate
        
    Returns:
        Validation prompt
    """
    return f"""
You are a healthcare credentialing specialist. Review and validate the following prescriber information.

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


def get_prescriber_enhancement_prompt(prescriber_data: Dict[str, Any]) -> str:
    """
    Get prompt for enhancing prescriber information
    
    Args:
        prescriber_data: Current prescriber data to enhance
        
    Returns:
        Enhancement prompt
    """
    return f"""
You are a healthcare data specialist. Enhance and standardize the following prescriber information.

Current prescriber data:
{prescriber_data}

Enhancement tasks:
1. Standardize name formatting (proper case)
2. Validate and format license numbers
3. Validate NPI number format (10 digits)
4. Validate DEA number format (letter + 6-7 digits)
5. Normalize address format if present
6. Standardize phone number format
7. Improve data quality and consistency

Return the enhanced prescriber information in the same JSON format with improved formatting and regulatory compliance.
Include a certainty score reflecting the quality of the information.
"""
