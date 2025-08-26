"""
Hallucination Detection Agent Prompts
Contains prompts for detecting inconsistencies and medical implausibilities
"""

from typing import Dict, Any, List


def get_hallucination_check_prompt(prescription_data: Dict[str, Any]) -> str:
    """
    Get prompt for general hallucination detection
    
    Args:
        prescription_data: Complete prescription data to check
        
    Returns:
        Hallucination detection prompt
    """
    return f"""
You are a pharmacy intern working under a supervising pharmacist. Review extracted prescription data for potential errors or inconsistencies for pharmacist evaluation.

Prescription data to review:
{prescription_data}

Check for the following potential issues:
1. Inconsistent or contradictory information
2. Unrealistic values (impossible ages, quantities, etc.)
3. Missing critical information
4. Data that doesn't make clinical sense
5. Potential extraction errors

Return your assessment in JSON format:
{{
    "hallucination_detected": boolean,
    "issues": ["list of specific issues found"],
    "confidence": float (0.0-1.0),
    "recommendations": ["list of recommendations"]
}}

Focus on clinical plausibility and data consistency. Document findings for supervising pharmacist review.
"""


def get_consistency_check_prompt(prescription_data: Dict[str, Any]) -> str:
    """
    Get prompt for consistency checking
    
    Args:
        prescription_data: Prescription data to check for consistency
        
    Returns:
        Consistency check prompt
    """
    return f"""
You are a data quality specialist reviewing prescription information for internal consistency.

Data to review:
{prescription_data}

Check for consistency issues:
1. Age vs. date of birth alignment
2. Medication appropriateness for patient age
3. Prescriber credentials completeness
4. Medication dosing reasonableness
5. Overall data coherence

Identify any inconsistencies or red flags that suggest extraction errors.

Return your findings in a clear assessment format.
"""


def get_medical_plausibility_check_prompt(medications: List[Dict[str, Any]], patient_info: Dict[str, Any]) -> str:
    """
    Get prompt for medical plausibility checking
    
    Args:
        medications: List of medications to check
        patient_info: Patient information for context
        
    Returns:
        Medical plausibility check prompt
    """
    return f"""
You are a clinical pharmacist reviewing medication prescriptions for medical plausibility.

Patient information:
{patient_info}

Medications prescribed:
{medications}

Evaluate the medical plausibility:
1. Are the medications appropriate for the patient age/condition?
2. Are the dosages within normal ranges?
3. Are there any concerning drug combinations?
4. Do the quantities make sense for the instructions?
5. Are there any obvious safety concerns?

Provide your clinical assessment focusing on:
- Questionable prescribing patterns
- Unusual drug combinations
- Dosing concerns
- Safety red flags

Return a brief clinical assessment.
"""