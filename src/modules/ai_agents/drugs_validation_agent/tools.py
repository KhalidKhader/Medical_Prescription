"""
Drugs Validation Agent Tools
Contains utility functions for medication validation
"""

from typing import Dict, Any, List
from src.modules.ai_agents.utils.common_tools import (
    validate_medication_data,
    extract_numeric_value,
    extract_strength_components
)
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.settings.logging import logger


def validate_drug_strength(drug_name: str, strength: str, indication: str = None) -> Dict[str, Any]:
    """Validate if drug strength is appropriate for indication"""
    if not strength:
        return {"valid": False, "issue": "Missing strength"}
    
    strength_components = extract_strength_components(strength)
    if not strength_components["value"]:
        return {"valid": False, "issue": "Invalid strength format"}
    
    # Basic strength validation - can be enhanced with drug-specific rules
    return {"valid": True, "components": strength_components}


def check_medication_completeness(medication: Dict[str, Any]) -> Dict[str, Any]:
    """Check if medication has all required fields"""
    issues = validate_medication_data(medication)
    
    completeness_score = 0
    total_fields = 7  # Essential fields count
    
    if medication.get("drug_name"):
        completeness_score += 1
    if medication.get("strength"):
        completeness_score += 1
    if medication.get("instructions_for_use"):
        completeness_score += 1
    if medication.get("quantity"):
        completeness_score += 1
    if medication.get("days_of_use"):
        completeness_score += 1
    if medication.get("sig_english"):
        completeness_score += 1
    if medication.get("rxcui"):
        completeness_score += 1
    
    return {
        "completeness_percentage": (completeness_score / total_fields) * 100,
        "missing_fields": issues,
        "score": completeness_score,
        "total_fields": total_fields
    }


def validate_dosage_form_route_compatibility(form: str, route: str) -> bool:
    """Check if dosage form is compatible with route of administration"""
    if not form or not route:
        return True  # Cannot validate without both
    
    form_lower = form.lower()
    route_lower = route.lower()
    
    # Define incompatible combinations
    incompatible = [
        ("tablet", "injection"),
        ("capsule", "injection"),
        ("injection", "oral"),
        ("topical", "oral"),
        ("inhaler", "oral")
    ]
    
    for incompatible_form, incompatible_route in incompatible:
        if incompatible_form in form_lower and incompatible_route in route_lower:
            return False
    
    return True


def calculate_validation_confidence(medication: Dict[str, Any]) -> int:
    """Calculate confidence score for medication validation"""
    confidence = 100
    
    # Reduce confidence for missing critical fields
    if not medication.get("drug_name"):
        confidence -= 30
    if not medication.get("rxcui"):
        confidence -= 20
    if not medication.get("strength"):
        confidence -= 15
    if not medication.get("instructions_for_use"):
        confidence -= 15
    if not medication.get("sig_english"):
        confidence -= 10
    
    # Reduce confidence for potential issues
    if medication.get("verification_status") == "error":
        confidence -= 25
    if medication.get("precision_match") is False:
        confidence -= 10
    
    return max(0, confidence)


def format_validation_summary(validations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format validation results into summary"""
    total = len(validations)
    valid_count = sum(1 for v in validations if v.get("validation_status") == "valid")
    warning_count = sum(1 for v in validations if v.get("validation_status") == "warning")
    critical_count = sum(1 for v in validations if v.get("validation_status") == "critical")
    
    return {
        "total_medications": total,
        "valid_medications": valid_count,
        "medications_with_warnings": warning_count,
        "critical_issues": critical_count,
        "overall_safety_score": (valid_count / total * 100) if total > 0 else 0
    }