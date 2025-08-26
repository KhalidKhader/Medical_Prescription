"""
Drugs Agent Prompts
Contains prompts for extracting and processing medication information
"""

from typing import Dict, Any


def get_drugs_extraction_prompt() -> str:
    """
    Get prompt for extracting medication information from prescription
    
    Returns:
        Drugs extraction prompt
    """
    return """
You are a pharmacy intern working under a supervising pharmacist. Extract ONLY medication information from prescription images for pharmacist review.

Extract the following medication information with maximum accuracy:
- Drug name
- Strength/dosage
- Instructions for use (sig)
- Quantity
- Days of use (if specified)
- Number of refills

Rules:
1. Only extract information that is clearly visible in the image
2. Preserve exact spelling, abbreviations, and capitalization
3. For each medication, provide a certainty score (0-100)
4. If quantity is not written, set infer_qty to "Yes" and calculate for 30-day supply
5. If days of use is not written, set infer_days to "Yes" and infer from instructions

Return ONLY a JSON object with this structure:
{
    "medications": [
        {
            "drug_name": "string or null",
            "strength": "string or null",
            "instructions_for_use": "string or null",
            "quantity": "string or null",
            "infer_qty": "Yes or No",
            "days_of_use": "string or null",
            "infer_days": "Yes or No",
            "refills": "string or null",
            "certainty": "numeric 0-100"
        }
    ]
}

Extract each medication as a separate object in the medications array.
"""


def get_sig_generation_prompt(instructions: str) -> str:
    """
    Get prompt for generating clear English instructions (sig)
    
    Args:
        instructions: Raw prescription instructions
        
    Returns:
        Sig generation prompt
    """
    return f"""
You are a pharmacy technician. Convert the following prescription instructions into clear, patient-friendly English.

Raw instructions: "{instructions}"

Convert to clear instructions that include:
- Action verb (take, apply, instill, etc.)
- Quantity per dose
- Route of administration
- Frequency
- Duration if specified

Return ONLY the clear English instruction as a single string.

Examples:
- "1 po bid" → "Take 1 tablet by mouth twice daily"
- "gtts ii ou qid" → "Instill 2 drops in both eyes four times daily"
- "apply bid prn" → "Apply twice daily as needed"
"""


def get_quantity_calculation_prompt(instructions: str, days_supply: int = 30) -> str:
    """
    Get prompt for calculating medication quantity
    
    Args:
        instructions: Prescription instructions
        days_supply: Number of days supply to calculate for
        
    Returns:
        Quantity calculation prompt
    """
    return f"""
You are a pharmacy technician calculating medication quantities.

Instructions: "{instructions}"
Days supply: {days_supply} days

Calculate the total quantity needed for {days_supply} days based on the instructions.

Return ONLY a JSON object:
{{
    "calculated_quantity": "quantity as string",
    "calculation_reasoning": "brief explanation of calculation"
}}

Examples:
- "1 tablet twice daily" for 30 days = 60 tablets
- "2 drops in each eye daily" for 30 days = 1 bottle (typically 5-10ml)
- "Apply thin layer twice daily" for 30 days = 1 tube (typically 15-30g)
"""


def get_days_inference_prompt(quantity: str, instructions: str) -> str:
    """
    Get prompt for inferring days of use from quantity and instructions
    
    Args:
        quantity: Prescribed quantity
        instructions: Usage instructions
        
    Returns:
        Days inference prompt
    """
    return f"""
You are a pharmacy technician inferring days of use.

Quantity: "{quantity}"
Instructions: "{instructions}"

Calculate how many days this quantity will last based on the usage instructions.

Return ONLY a JSON object:
{{
    "inferred_days": "days as string",
    "inference_reasoning": "brief explanation"
}}

Examples:
- 60 tablets, "1 tablet twice daily" = 30 days
- 10ml bottle, "2 drops twice daily" = approximately 25-30 days
- 30g tube, "apply twice daily" = approximately 15-30 days
"""


def get_medication_validation_prompt(medication: Dict[str, Any]) -> str:
    """
    Get prompt for validating medication information
    
    Args:
        medication: Medication data to validate
        
    Returns:
        Validation prompt
    """
    return f"""
You are a clinical pharmacist validating medication information.

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