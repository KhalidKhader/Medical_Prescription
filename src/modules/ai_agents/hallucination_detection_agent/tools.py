"""
Hallucination Detection Agent Tools
Contains tools for detecting inconsistencies and validating medical plausibility
"""

from typing import Dict, Any, List, Optional
from src.core.settings.logging import logger


def detect_data_inconsistencies(prescription_data: Dict[str, Any]) -> List[str]:
    """
    Detect basic data inconsistencies in prescription data
    
    Args:
        prescription_data: Complete prescription data
        
    Returns:
        List of consistency issues found
    """
    issues = []
    
    try:
        # Check prescriber data consistency
        prescriber = prescription_data.get("prescriber", {})
        if prescriber:
            # Check for empty prescriber with high certainty
            if prescriber.get("certainty", 0) > 70 and not prescriber.get("full_name"):
                issues.append("High certainty claimed for missing prescriber data")
            
            # Check NPI format if present
            npi = prescriber.get("npi_number")
            if npi and len(str(npi).replace("-", "").replace(" ", "")) != 10:
                if not any(char.isdigit() for char in str(npi)):
                    issues.append("Invalid NPI format detected")
        
        # Check patient data consistency
        patient = prescription_data.get("patient", {})
        if patient:
            # Check age and DOB consistency
            age = patient.get("age")
            dob = patient.get("date_of_birth")
            
            if age and dob:
                try:
                    from datetime import datetime
                    if "/" in str(dob):
                        # Try MM/DD/YYYY format
                        dob_date = datetime.strptime(str(dob), "%m/%d/%Y")
                    else:
                        # Try YYYY-MM-DD format
                        dob_date = datetime.strptime(str(dob), "%Y-%m-%d")
                    
                    calculated_age = datetime.now().year - dob_date.year
                    provided_age = int(str(age).split()[0])  # Handle "25 years" format
                    
                    if abs(calculated_age - provided_age) > 2:  # Allow 2 year tolerance
                        issues.append("Age significantly inconsistent with date of birth")
                        
                except (ValueError, TypeError):
                    pass
        
        # Check medication data consistency
        medications = prescription_data.get("medications", [])
        for i, med in enumerate(medications):
            med_name = med.get("drug_name", f"Medication {i+1}")
            
            # Check for impossible quantities
            quantity = med.get("quantity")
            if quantity:
                try:
                    qty_num = int(''.join(filter(str.isdigit, str(quantity))))
                    if qty_num > 10000:  # Unreasonably large quantity
                        issues.append(f"Unreasonably large quantity for {med_name}: {quantity}")
                except (ValueError, TypeError):
                    pass
            
            # Check for missing critical fields with high certainty
            certainty = med.get("certainty", 0)
            if certainty > 80:
                if not med.get("drug_name"):
                    issues.append(f"High certainty claimed for medication with missing drug name")
                if not med.get("instructions_for_use"):
                    issues.append(f"High certainty claimed for {med_name} with missing instructions")
            
            # Check refills consistency
            refills = med.get("refills")
            if refills:
                try:
                    refill_num = int(str(refills).replace("refills", "").strip())
                    if refill_num > 12:  # Unreasonably high refills
                        issues.append(f"Unreasonably high refill count for {med_name}: {refills}")
                except (ValueError, TypeError):
                    pass
        
        # Check overall data completeness vs certainty claims
        total_certainty = 0
        certainty_count = 0
        empty_fields = 0
        total_fields = 0
        
        for section_name, section_data in prescription_data.items():
            if isinstance(section_data, dict) and section_name in ["prescriber", "patient"]:
                section_certainty = section_data.get("certainty")
                if section_certainty:
                    total_certainty += section_certainty
                    certainty_count += 1
                
                for field_name, field_value in section_data.items():
                    if field_name != "certainty":
                        total_fields += 1
                        if not field_value:
                            empty_fields += 1
            elif isinstance(section_data, list) and section_name == "medications":
                for med in section_data:
                    if isinstance(med, dict):
                        med_certainty = med.get("certainty")
                        if med_certainty:
                            total_certainty += med_certainty
                            certainty_count += 1
        
        # Check if high average certainty but many empty fields
        if certainty_count > 0 and total_fields > 0:
            avg_certainty = total_certainty / certainty_count
            empty_ratio = empty_fields / total_fields
            
            if avg_certainty > 75 and empty_ratio > 0.5:
                issues.append("High certainty claimed despite significant missing data")
        
        logger.info(f"Data consistency check completed. Found {len(issues)} issues")
        return issues
        
    except Exception as e:
        logger.error(f"Data consistency check failed: {e}")
        return ["Data consistency check failed due to system error"]


def validate_medical_plausibility(medications: List[Dict[str, Any]], patient_info: Dict[str, Any]) -> List[str]:
    """
    Validate medical plausibility of medications
    
    Args:
        medications: List of medication data
        patient_info: Patient information for context
        
    Returns:
        List of plausibility issues
    """
    issues = []
    
    try:
        for med in medications:
            drug_name = med.get("drug_name", "").lower()
            strength = med.get("strength", "").lower()
            quantity = med.get("quantity", "")
            
            # Check for common medication name patterns
            if drug_name:
                # Flag obviously non-medical names
                if any(word in drug_name for word in ["test", "example", "sample", "placeholder"]):
                    issues.append(f"Non-medical drug name detected: {drug_name}")
                
                # Check for impossible strength combinations
                if strength:
                    # Flag if strength contains obviously wrong units
                    if any(unit in strength for unit in ["kg", "pounds", "miles", "hours"]):
                        issues.append(f"Invalid strength units for {drug_name}: {strength}")
            
            # Check quantity plausibility
            if quantity:
                try:
                    qty_str = str(quantity).lower()
                    # Extract numeric part
                    qty_numbers = ''.join(filter(str.isdigit, qty_str))
                    if qty_numbers:
                        qty_num = int(qty_numbers)
                        
                        # Check for unreasonable quantities based on common medication types
                        if "drop" in qty_str or "ml" in qty_str:
                            if qty_num > 100:  # More than 100ml for drops is unusual
                                issues.append(f"Unusually large volume for {drug_name}: {quantity}")
                        elif "tablet" in qty_str or "capsule" in qty_str:
                            if qty_num > 1000:  # More than 1000 tablets is unusual for most prescriptions
                                issues.append(f"Unusually large tablet/capsule count for {drug_name}: {quantity}")
                        elif "tube" in qty_str or "jar" in qty_str:
                            if qty_num > 10:  # More than 10 tubes/jars is unusual
                                issues.append(f"Unusually large container count for {drug_name}: {quantity}")
                                
                except (ValueError, TypeError):
                    pass
        
        # Check for drug interaction patterns (basic)
        drug_names = [med.get("drug_name", "").lower() for med in medications if med.get("drug_name")]
        
        # Flag if multiple similar medications
        antibiotic_count = sum(1 for name in drug_names if any(ab in name for ab in ["cillin", "mycin", "floxacin", "cef"]))
        if antibiotic_count > 2:
            issues.append("Multiple antibiotics prescribed simultaneously")
        
        pain_med_count = sum(1 for name in drug_names if any(pm in name for pm in ["codeine", "morphine", "oxycodone", "hydrocodone"]))
        if pain_med_count > 1:
            issues.append("Multiple opioid pain medications prescribed")
        
        logger.info(f"Medical plausibility check completed. Found {len(issues)} issues")
        return issues
        
    except Exception as e:
        logger.error(f"Medical plausibility check failed: {e}")
        return ["Medical plausibility check failed"]


def check_prescription_completeness(prescription_data: Dict[str, Any]) -> List[str]:
    """
    Check for prescription completeness and safety requirements
    
    Args:
        prescription_data: Complete prescription data
        
    Returns:
        List of completeness/safety issues
    """
    issues = []
    
    try:
        # Check prescriber information completeness
        prescriber = prescription_data.get("prescriber", {})
        if not prescriber.get("full_name"):
            issues.append("Missing prescriber name")
        
        if not prescriber.get("dea_number") and not prescriber.get("npi_number"):
            issues.append("Missing prescriber identification (DEA or NPI)")
        
        # Check patient information completeness
        patient = prescription_data.get("patient", {})
        if not patient.get("full_name"):
            issues.append("Missing patient name")
        
        # Check medication completeness
        medications = prescription_data.get("medications", [])
        if not medications:
            issues.append("No medications found in prescription")
        
        for i, med in enumerate(medications):
            med_id = med.get("drug_name", f"Medication {i+1}")
            
            # Critical medication fields
            if not med.get("drug_name"):
                issues.append(f"Missing drug name for medication {i+1}")
            
            if not med.get("instructions_for_use"):
                issues.append(f"Missing instructions for {med_id}")
            
            if not med.get("quantity") and not med.get("infer_qty") == "Yes":
                issues.append(f"Missing quantity for {med_id}")
            
            # Safety-related checks
            strength = med.get("strength")
            if not strength:
                issues.append(f"Missing strength for {med_id}")
            
            # Check for controlled substances without DEA
            drug_name = med.get("drug_name", "").lower()
            controlled_indicators = ["codeine", "morphine", "oxycodone", "hydrocodone", "adderall", "xanax", "ativan"]
            if any(indicator in drug_name for indicator in controlled_indicators):
                if not prescriber.get("dea_number"):
                    issues.append(f"Controlled substance {med_id} prescribed without DEA number")
        
        # Check prescription date
        if not prescription_data.get("date_prescription_written"):
            issues.append("Missing prescription date")
        
        logger.info(f"Prescription completeness check completed. Found {len(issues)} issues")
        return issues
        
    except Exception as e:
        logger.error(f"Prescription completeness check failed: {e}")
        return ["Prescription completeness check failed"]
