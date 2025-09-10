"""
Common Tools - Shared utilities for all AI agents
Provides standardized functions for common operations
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import re
from src.core.settings.logging import logger
from src.modules.ai_agents.utils.json_parser import parse_json
from datetime import datetime


def normalize_drug_name(drug_name: str) -> str:
    """Normalize drug name for consistent processing"""
    if not drug_name:
        return ""
    return ' '.join(drug_name.strip().split())


def extract_strength_components(strength: str) -> Dict[str, Any]:
    """Extract numeric value and unit from strength string"""
    if not strength:
        return {"value": None, "unit": "", "original": strength}
    
    numeric_match = re.search(r'(\d+(?:\.\d+)?)', strength)
    numeric_value = float(numeric_match.group(1)) if numeric_match else None
    
    unit_match = re.search(r'([a-zA-Z]+(?:/[a-zA-Z]+)?)', strength)
    unit = unit_match.group(1) if unit_match else ""
    
    return {
        "value": numeric_value,
        "unit": unit,
        "original": strength
    }


def clean_text_field(text: str) -> str:
    """Clean and normalize text field"""
    if not text:
        return ""
    
    cleaned = ' '.join(str(text).strip().split())
    cleaned = re.sub(r'[^\w\s\-\.\,\(\)\/]', '', cleaned)
    
    return cleaned

# Patient validation functions
def validate_patient_name(name: str) -> tuple[bool, str]:
    """Validate patient name format"""
    if not name or not name.strip():
        return False, ""
    
    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        return False, cleaned_name
    
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \'-')
    if not all(c in allowed_chars for c in cleaned_name):
        return False, cleaned_name
    
    cleaned_name = ' '.join(word.capitalize() for word in cleaned_name.split())
    return True, cleaned_name


def validate_date_of_birth(dob: str) -> tuple[bool, Optional[str], Optional[int]]:
    """Validate and standardize date of birth"""
    if not dob or not dob.strip():
        return False, None, None
    
    date_formats = [
        '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
        '%B %d, %Y', '%b %d, %Y'
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(dob.strip(), date_format)
            current_year = datetime.now().year
            if parsed_date.year > current_year or parsed_date.year < 1900:
                continue
            
            today = datetime.now()
            age = today.year - parsed_date.year
            if today.month < parsed_date.month or (today.month == parsed_date.month and today.day < parsed_date.day):
                age -= 1
            
            standardized_date = parsed_date.strftime('%Y-%m-%d')
            return True, standardized_date, age
            
        except ValueError:
            continue
    
    return False, None, None


def calculate_patient_quality_metrics(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate quality metrics for patient data"""
    metrics = {
        "completeness_score": 0,
        "has_full_name": bool(patient_data.get("full_name")),
        "has_dob": bool(patient_data.get("date_of_birth")),
        "has_address": bool(patient_data.get("address")),
        "data_quality_issues": []
    }
    
    total_fields = 3
    filled_fields = sum([
        bool(patient_data.get("full_name")),
        bool(patient_data.get("date_of_birth")),
        bool(patient_data.get("address"))
    ])
    
    metrics["completeness_score"] = (filled_fields / total_fields) * 100
    
    if patient_data.get("full_name"):
        is_valid, _ = validate_patient_name(patient_data["full_name"])
        if not is_valid:
            metrics["data_quality_issues"].append("Invalid name format")
    
    return metrics


# Prescriber validation functions
def validate_npi_number(npi: str) -> tuple[bool, str]:
    """Validate NPI number format (10 digits)"""
    if not npi or not npi.strip():
        return False, ""
    
    cleaned_npi = ''.join(c for c in npi.strip() if c.isdigit())
    return (len(cleaned_npi) == 10, cleaned_npi)


def validate_dea_number(dea: str) -> tuple[bool, str]:
    """Validate DEA number format"""
    if not dea or not dea.strip():
        return False, ""
    
    cleaned_dea = dea.strip().upper()
    if len(cleaned_dea) >= 7 and cleaned_dea[0].isalpha():
        letter = cleaned_dea[0]
        digits = ''.join(c for c in cleaned_dea[1:] if c.isdigit())
        if len(digits) >= 6:
            core_dea = letter + digits[:7]
            return True, core_dea
    
    return False, cleaned_dea


def validate_phone_number(phone: str) -> tuple[bool, str]:
    """Validate and format phone number"""
    if not phone or not phone.strip():
        return False, ""
    
    digits = ''.join(c for c in phone.strip() if c.isdigit())
    
    if len(digits) == 10:
        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return True, formatted
    elif len(digits) == 11 and digits[0] == '1':
        formatted = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return True, formatted
    
    return False, digits



def calculate_quantity_from_sig(instructions: str, days_supply: int = 30) -> Tuple[str, bool]:
    """Calculate quantity needed based on instructions using string matching"""
    if not instructions or not instructions.strip():
        return "30", True  # Default fallback
    
    instructions_lower = instructions.lower()
    
    # Common patterns for quantity calculation
    daily_dose = 1  # Default
    frequency = 1   # Default
    
    # Extract frequency using string matching
    if "twice" in instructions_lower or "bid" in instructions_lower or "b.i.d" in instructions_lower:
        frequency = 2
    elif "three times" in instructions_lower or "tid" in instructions_lower or "t.i.d" in instructions_lower:
        frequency = 3
    elif "four times" in instructions_lower or "qid" in instructions_lower or "q.i.d" in instructions_lower:
        frequency = 4
    elif "daily" in instructions_lower or "qd" in instructions_lower or "once" in instructions_lower:
        frequency = 1
    
    # Extract dose amount using simple numeric extraction
    numeric_chars = ''.join(c for c in instructions if c.isdigit())
    if numeric_chars:
        try:
            daily_dose = int(numeric_chars[:2])  # Take first 1-2 digits
        except:
            daily_dose = 1
    
    # Calculate total quantity
    total_quantity = daily_dose * frequency * days_supply
    
    # Format based on medication type
    if any(word in instructions_lower for word in ["drop", "gtt"]):
        # For drops, return as bottle (ml)
        return f"{max(5, total_quantity // 20)} mL", True
    elif any(word in instructions_lower for word in ["apply", "cream", "ointment", "gel"]):
        # For topicals, return as tube/jar
        return f"{max(15, total_quantity)} g", True
    else:
        # For tablets/capsules
        return str(total_quantity), True


def infer_days_from_quantity(quantity: str, instructions: str) -> Tuple[str, bool]:
    """Infer days of use from quantity and instructions using string matching"""
    if not quantity or not instructions:
        return "30", True  # Default
    
    try:
        # Extract numeric quantity using simple extraction
        qty_nums = ''.join(c for c in quantity if c.isdigit())
        if not qty_nums:
            return "30", True
        
        qty_num = int(qty_nums[:3])  # Take first 1-3 digits
        
        # Extract frequency from instructions
        instructions_lower = instructions.lower()
        frequency = 1  # Default once daily
        
        if "twice" in instructions_lower or "bid" in instructions_lower:
            frequency = 2
        elif "three times" in instructions_lower or "tid" in instructions_lower:
            frequency = 3
        elif "four times" in instructions_lower or "qid" in instructions_lower:
            frequency = 4
        
        # Extract dose per administration using simple extraction
        inst_nums = ''.join(c for c in instructions if c.isdigit())
        dose_per_admin = int(inst_nums[:2]) if inst_nums else 1
        
        # Calculate days
        total_daily_dose = dose_per_admin * frequency
        if total_daily_dose > 0:
            days = qty_num // total_daily_dose
            return str(max(1, days)), True
        
    except (ValueError, ZeroDivisionError):
        logger.error("Failed to infer days from quantity and instructions")
    
    return "30", True  # Default fallback


def generate_sig_english(instructions: str) -> str:
    """Generate clear English instructions from prescription sig"""
    if not instructions or not instructions.strip():
        return ""
    
    # Common abbreviation mappings
    sig_mappings = {
        "po": "by mouth",
        "bid": "twice daily",
        "tid": "three times daily", 
        "qid": "four times daily",
        "qd": "once daily",
        "daily": "daily",
        "prn": "as needed",
        "ac": "before meals",
        "pc": "after meals",
        "hs": "at bedtime",
        "q4h": "every 4 hours",
        "q6h": "every 6 hours",
        "q8h": "every 8 hours",
        "q12h": "every 12 hours",
        "gtt": "drop",
        "gtts": "drops",
        "ou": "both eyes",
        "od": "right eye",
        "os": "left eye",
        "au": "both ears",
        "ad": "right ear",
        "as": "left ear"
    }
    
    # Start with the original instructions
    result = instructions.lower()
    
    # Replace common abbreviations
    for abbrev, full_text in sig_mappings.items():
        result = result.replace(abbrev, full_text)
    
    # Add action verb if missing
    if not any(verb in result for verb in ["take", "apply", "instill", "use", "insert"]):
        if any(word in result for word in ["drop", "eye", "ear"]):
            result = "instill " + result
        elif any(word in result for word in ["cream", "ointment", "gel", "apply"]):
            result = "apply " + result
        else:
            result = "take " + result
    
    # Capitalize first letter and clean up
    result = result.strip().capitalize()
    
    return result
