"""
Patient and Prescriber Info Agent Tools
Contains tools for processing and validating combined patient and prescriber information
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from src.core.settings.logging import logger
from src.modules.ai_agents.utils.json_parser import parse_json, clean_json_text, extract_json_from_text
from src.modules.ai_agents.utils.common_tools import (
    validate_patient_name,
    validate_date_of_birth,
    validate_npi_number,
    validate_dea_number,
    validate_phone_number,
    clean_text_field
)

def extract_combined_quality_metrics(patient_data: Dict[str, Any], prescriber_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract quality metrics for combined patient and prescriber data
    
    Args:
        patient_data: Patient information dictionary
        prescriber_data: Prescriber information dictionary
        
    Returns:
        Combined quality metrics dictionary
    """
    # Clean the input data first
    cleaned_patient_data = {
        k: clean_text_field(v) if isinstance(v, str) else v 
        for k, v in patient_data.items()
    }
    cleaned_prescriber_data = {
        k: clean_text_field(v) if isinstance(v, str) else v 
        for k, v in prescriber_data.items()
    }
    
    metrics = {
        "overall_completeness": 0,
        "patient_metrics": {
            "completeness_score": 0,
            "has_full_name": bool(cleaned_patient_data.get("full_name")),
            "has_dob": bool(cleaned_patient_data.get("date_of_birth")),
            "has_age": bool(cleaned_patient_data.get("age")),
            "has_address": bool(cleaned_patient_data.get("address")),
            "age_dob_consistent": True,
            "data_quality_issues": []
        },
        "prescriber_metrics": {
            "completeness_score": 0,
            "has_full_name": bool(cleaned_prescriber_data.get("full_name")),
            "has_npi": bool(cleaned_prescriber_data.get("npi_number")),
            "has_dea": bool(cleaned_prescriber_data.get("dea_number")),
            "has_license": bool(cleaned_prescriber_data.get("state_license_number")),
            "has_address": bool(cleaned_prescriber_data.get("address")),
            "has_contact": bool(cleaned_prescriber_data.get("contact_number")),
            "data_quality_issues": []
        }
    }
    
    # Calculate patient completeness
    patient_total_fields = 4  # full_name, date_of_birth, age, address
    patient_filled_fields = sum([
        metrics["patient_metrics"]["has_full_name"],
        metrics["patient_metrics"]["has_dob"],
        metrics["patient_metrics"]["has_age"],
        metrics["patient_metrics"]["has_address"]
    ])
    metrics["patient_metrics"]["completeness_score"] = (patient_filled_fields / patient_total_fields) * 100
    
    # Calculate prescriber completeness
    prescriber_total_fields = 6  # full_name, license, npi, dea, address, contact
    prescriber_filled_fields = sum([
        metrics["prescriber_metrics"]["has_full_name"],
        metrics["prescriber_metrics"]["has_license"],
        metrics["prescriber_metrics"]["has_npi"],
        metrics["prescriber_metrics"]["has_dea"],
        metrics["prescriber_metrics"]["has_address"],
        metrics["prescriber_metrics"]["has_contact"]
    ])
    metrics["prescriber_metrics"]["completeness_score"] = (prescriber_filled_fields / prescriber_total_fields) * 100
    
    # Calculate overall completeness
    metrics["overall_completeness"] = (
        metrics["patient_metrics"]["completeness_score"] +
        metrics["prescriber_metrics"]["completeness_score"]
    ) / 2
    
    # Validate all fields using common tools
    if cleaned_patient_data.get("full_name"):
        is_valid, _ = validate_patient_name(cleaned_patient_data["full_name"])
        if not is_valid:
            metrics["patient_metrics"]["data_quality_issues"].append("Invalid patient name format")
    
    if cleaned_patient_data.get("date_of_birth"):
        is_valid, _, _ = validate_date_of_birth(cleaned_patient_data["date_of_birth"])
        if not is_valid:
            metrics["patient_metrics"]["data_quality_issues"].append("Invalid date of birth format")
    
    # Validate prescriber information
    if cleaned_prescriber_data.get("npi_number"):
        is_valid, _ = validate_npi_number(cleaned_prescriber_data["npi_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid NPI number format")
    
    if cleaned_prescriber_data.get("dea_number"):
        is_valid, _ = validate_dea_number(cleaned_prescriber_data["dea_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid DEA number format")
    
    if cleaned_prescriber_data.get("contact_number"):
        is_valid, _ = validate_phone_number(cleaned_prescriber_data["contact_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid contact number format")
    
    # Check for critical missing fields
    if not metrics["patient_metrics"]["has_full_name"]:
        metrics["patient_metrics"]["data_quality_issues"].append("Missing patient name")
    if not metrics["prescriber_metrics"]["has_full_name"]:
        metrics["prescriber_metrics"]["data_quality_issues"].append("Missing prescriber name")
    
    # Flag if both DEA and NPI are missing for prescriber
    if not (metrics["prescriber_metrics"]["has_dea"] or metrics["prescriber_metrics"]["has_npi"]):
        metrics["prescriber_metrics"]["data_quality_issues"].append("Missing both DEA and NPI numbers")
    
    return metrics
    
    # Calculate patient completeness
    patient_total_fields = 4  # full_name, date_of_birth, age, address
    patient_filled_fields = sum([
        bool(patient_data.get("full_name")),
        bool(patient_data.get("date_of_birth")),
        bool(patient_data.get("age")),
        bool(patient_data.get("address"))
    ])
    metrics["patient_metrics"]["completeness_score"] = (patient_filled_fields / patient_total_fields) * 100
    
    # Calculate prescriber completeness
    prescriber_total_fields = 6  # full_name, license, npi, dea, address, contact
    prescriber_filled_fields = sum([
        bool(prescriber_data.get("full_name")),
        bool(prescriber_data.get("state_license_number")),
        bool(prescriber_data.get("npi_number")),
        bool(prescriber_data.get("dea_number")),
        bool(prescriber_data.get("address")),
        bool(prescriber_data.get("contact_number"))
    ])
    metrics["prescriber_metrics"]["completeness_score"] = (prescriber_filled_fields / prescriber_total_fields) * 100
    
    # Calculate overall completeness
    metrics["overall_completeness"] = (
        metrics["patient_metrics"]["completeness_score"] +
        metrics["prescriber_metrics"]["completeness_score"]
    ) / 2
    
    # Validate patient information
    if patient_data.get("full_name"):
        is_valid, _ = validate_patient_name(patient_data["full_name"])
        if not is_valid:
            metrics["patient_metrics"]["data_quality_issues"].append("Invalid patient name format")
    
    if patient_data.get("date_of_birth"):
        is_valid, _, _ = validate_date_of_birth(patient_data["date_of_birth"])
        if not is_valid:
            metrics["patient_metrics"]["data_quality_issues"].append("Invalid date of birth format")
    
    # Check age-DOB consistency
    if patient_data.get("age") and patient_data.get("date_of_birth"):
        try:
            dob = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d")
            age = int(patient_data["age"])
            calculated_age = (datetime.now() - dob).days // 365
            if abs(calculated_age - age) > 1:  # Allow 1 year difference
                metrics["patient_metrics"]["age_dob_consistent"] = False
                metrics["patient_metrics"]["data_quality_issues"].append("Age and DOB mismatch")
        except (ValueError, TypeError):
            metrics["patient_metrics"]["age_dob_consistent"] = False
    
    # Validate prescriber information
    if prescriber_data.get("full_name"):
        is_valid, _ = validate_prescriber_name(prescriber_data["full_name"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid prescriber name format")
    
    if prescriber_data.get("npi_number"):
        is_valid, _ = validate_npi_number(prescriber_data["npi_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid NPI number format")
    
    if prescriber_data.get("dea_number"):
        is_valid, _ = validate_dea_number(prescriber_data["dea_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid DEA number format")
    
    if prescriber_data.get("contact_number"):
        is_valid, _ = validate_phone_number(prescriber_data["contact_number"])
        if not is_valid:
            metrics["prescriber_metrics"]["data_quality_issues"].append("Invalid contact number format")
    
    return metrics
