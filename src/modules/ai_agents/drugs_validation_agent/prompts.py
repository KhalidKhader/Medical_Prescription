"""
Drugs Validation Agent Prompts
Contains prompts for validating medication information
"""

from typing import Dict, Any


def get_drugs_validation_prompt(medication: Dict[str, Any]) -> str:
    """
    Get prompt for validating medication information
    
    Args:
        medication: Medication data to validate
        
    Returns:
        Validation prompt
    """
    return f"""
You are a pharmacy intern working under a supervising pharmacist. Validate medication information for pharmacist review.

Medication to validate:
{medication}

Validation tasks:
1. Check drug name validity
2. Verify strength format (should include units)
3. Validate quantity format
4. Check instruction clarity
5. Verify refill count (should be numeric or "0")
6. Assess overall data quality

Return a validation report in JSON format:
{{
    "is_valid": boolean,
    "confidence": float (0.0-1.0),
    "errors": ["list of validation errors"],
    "warnings": ["list of potential issues"],
    "validated_medication": {{
        "drug_name": "validated name",
        "strength": "validated strength",
        "instructions_for_use": "validated instructions",
        "quantity": "validated quantity",
        "infer_qty": "Yes or No",
        "days_of_use": "validated days",
        "infer_days": "Yes or No",
        "refills": "validated refills",
        "certainty": "numeric 0-100"
    }}
}}

Focus on clinical safety and prescription accuracy.
"""
