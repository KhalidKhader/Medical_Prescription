"""
Common Tools - Shared utilities for all AI agents
Provides standardized functions for common operations
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import re
from src.core.settings.logging import logger
from src.modules.ai_agents.utils.json_parser import parse_json
from datetime import datetime


def extract_numeric_value(text: str) -> Optional[float]:
    """Extract numeric value from text string"""
    if not text:
        return None
    cleaned = re.sub(r'[^\d.]', '', str(text))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


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


def validate_medication_data(medication: Dict[str, Any]) -> List[str]:
    """Validate medication data completeness"""
    issues = []
    
    if not medication.get("drug_name"):
        issues.append("Missing drug name")
    if not medication.get("instructions_for_use"):
        issues.append("Missing instructions for use")
    
    strength = medication.get("strength")
    if strength:
        strength_components = extract_strength_components(strength)
        if not strength_components["value"]:
            issues.append("Invalid strength format")
    
    return issues


def standardize_route(route: str) -> str:
    """Standardize medication route"""
    if not route:
        return ""
    
    route_mappings = {
        "po": "by mouth", "oral": "by mouth", "orally": "by mouth",
        "iv": "intravenously", "im": "intramuscularly", 
        "sc": "subcutaneously", "subq": "subcutaneously",
        "sl": "sublingually", "pr": "rectally", 
        "top": "topically", "inh": "by inhalation"
    }
    
    return route_mappings.get(route.lower().strip(), route)


def standardize_frequency(frequency: str) -> str:
    """Standardize medication frequency"""
    if not frequency:
        return ""
    
    freq_mappings = {
        "qd": "once daily", "bid": "twice daily", "tid": "three times daily",
        "qid": "four times daily", "q4h": "every 4 hours", "q6h": "every 6 hours", 
        "q8h": "every 8 hours", "q12h": "every 12 hours", "prn": "as needed",
        "hs": "at bedtime", "ac": "before meals", "pc": "after meals"
    }
    
    return freq_mappings.get(frequency.lower().strip(), frequency)


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


# Drug parsing and validation functions
def validate_parsed_components(components: Dict[str, Any], original_string: str) -> Dict[str, Any]:
    """Validate parsed drug components"""
    drug_name = components.get("drug_name", "")
    strength = components.get("strength", "")
    form = components.get("form", "")
    
    if drug_name:
        components["drug_name"] = normalize_drug_name(drug_name)
    if strength:
        components["strength"] = clean_text_field(strength)
    if form:
        components["form"] = clean_text_field(form)
    
    components["original_string"] = original_string
    components["parsing_confidence"] = calculate_parsing_confidence(components, original_string)
    return components


def calculate_parsing_confidence(components: Dict[str, Any], original: str) -> int:
    """Calculate confidence in parsing accuracy"""
    confidence = 100
    drug_name = components.get("drug_name", "")
    
    if not drug_name or len(drug_name) < 2:
        confidence -= 40
    
    if drug_name and original:
        if drug_name.lower() not in original.lower() and original.lower() not in drug_name.lower():
            if len(drug_name) >= 3 and len(original) >= 3:
                if drug_name[:3].lower() != original[:3].lower():
                    confidence -= 30
    
    strength = components.get("strength", "")
    if strength:
        strength_components = extract_strength_components(strength)
        if not strength_components["value"]:
            confidence -= 20
    
    return max(0, confidence)


def extract_drug_components_fallback(drug_string: str) -> Dict[str, Any]:
    """Fallback method to extract components using simple parsing"""
    if not drug_string:
        return {"drug_name": "", "strength": "", "form": ""}
    
    import re
    
    strength_pattern = r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|iu)(?:/\w+)?)'
    strength_match = re.search(strength_pattern, drug_string, re.IGNORECASE)
    strength = strength_match.group(1) if strength_match else ""
    
    form_patterns = [
        r'\b(tablet|capsule|injection|solution|cream|ointment|gel|patch|inhaler|spray)\b',
        r'\b(oral|topical|injectable|inhalation)\b'
    ]
    form = ""
    for pattern in form_patterns:
        form_match = re.search(pattern, drug_string, re.IGNORECASE)
        if form_match:
            form = form_match.group(1)
            break
    
    drug_name = drug_string
    if strength:
        drug_name = drug_name.replace(strength, "").strip()
    if form:
        drug_name = drug_name.replace(form, "").strip()
    
    drug_name = re.sub(r'\s+', ' ', drug_name).strip()
    
    return {
        "drug_name": drug_name or drug_string,
        "strength": strength,
        "form": form
    }


# Instruction parsing and validation functions
def parse_instruction_components(raw_instructions: str) -> Dict[str, Any]:
    """Parse raw prescription instructions into structured components"""
    if not raw_instructions:
        return {"verb": None, "quantity": None, "form": None, "route": None, "frequency": None, "duration": None, "confidence": 0.0}
    
    raw = raw_instructions.lower().strip()
    components = {
        "verb": None, "quantity": None, "form": None, "route": None,
        "frequency": None, "duration": None, "indication": None, "confidence": 0.75
    }
    
    # Parse quantity
    quantity_terms = ["tablet", "tab", "capsule", "cap", "drop", "gtts", "ml", "mg"]
    for term in quantity_terms:
        if term in raw:
            term_pos = raw.find(term)
            before_term = raw[:term_pos].strip()
            nums = ''.join(c if c.isdigit() or c == '.' else ' ' for c in before_term)
            num_parts = nums.strip().split()
            if num_parts:
                components["quantity"] = num_parts[-1]
                break
    
    # Check for word numbers
    word_nums = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
    for word, num in word_nums.items():
        if word in raw:
            components["quantity"] = num
            break
    
    # Parse frequency
    if 'bid' in raw or 'twice' in raw:
        components["frequency"] = "twice daily"
    elif 'tid' in raw or 'three times' in raw:
        components["frequency"] = "three times daily"
    elif 'qid' in raw or 'four times' in raw:
        components["frequency"] = "four times daily"
    elif 'daily' in raw or 'qd' in raw:
        components["frequency"] = "once daily"
    elif 'q6h' in raw:
        components["frequency"] = "every 6 hours"
    elif 'q4h' in raw:
        components["frequency"] = "every 4 hours"
    elif 'prn' in raw:
        components["frequency"] = "as needed"
    
    # Parse route
    if 'po' in raw or 'by mouth' in raw:
        components["route"] = "by mouth"
    elif 'ou' in raw or 'both eyes' in raw:
        components["route"] = "in both eyes"
    elif 'od' in raw or 'right eye' in raw:
        components["route"] = "in right eye"
    elif 'topical' in raw:
        components["route"] = "to affected area"
    
    # Parse duration
    if "until gone" in raw:
        components["duration"] = "until gone"
    elif "day" in raw:
        day_pos = raw.find("day")
        before_day = raw[:day_pos].strip()
        nums = ''.join(c if c.isdigit() else ' ' for c in before_day)
        num_parts = nums.strip().split()
        if num_parts:
            days = num_parts[-1]
            components["duration"] = f"for {days} days"
    
    return components


def validate_instruction_components(structured_instructions: Dict[str, Any]) -> Dict[str, Any]:
    """Validate instruction components for completeness"""
    validation = {
        "all_valid": True,
        "component_scores": {},
        "issues": [],
        "recommendations": []
    }
    
    # Validate verb
    verb = structured_instructions.get("verb")
    if not verb:
        validation["issues"].append("Missing action verb")
        validation["component_scores"]["verb"] = 0
        validation["all_valid"] = False
    elif verb.lower() not in ["take", "apply", "instill", "insert", "inject", "use"]:
        validation["issues"].append(f"Unusual verb: '{verb}' - verify appropriateness")
        validation["component_scores"]["verb"] = 70
    else:
        validation["component_scores"]["verb"] = 100
    
    # Validate other components
    for component in ["quantity", "route", "frequency"]:
        if not structured_instructions.get(component):
            validation["issues"].append(f"Missing {component}")
            validation["component_scores"][component] = 0
            validation["all_valid"] = False
        else:
            validation["component_scores"][component] = 100
    
    # Calculate overall score
    scores = list(validation["component_scores"].values())
    validation["overall_score"] = sum(scores) / len(scores) if scores else 0
    
    return validation


def validate_spanish_translation(english_sig: str, spanish_sig: str) -> Dict[str, Any]:
    """Validate Spanish translation of medication instructions"""
    validation = {
        "is_valid": True,
        "accuracy_score": 100,
        "issues": [],
        "suggestions": []
    }
    
    if not spanish_sig:
        return {"is_valid": False, "accuracy_score": 0, "issues": ["No Spanish translation provided"]}
    
    # Check for accents (should not have any)
    accented_chars = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'Á', 'É', 'Í', 'Ó', 'Ú', 'Ñ']
    if any(char in spanish_sig for char in accented_chars):
        validation["issues"].append("Spanish translation contains accents - remove all accents")
        validation["accuracy_score"] -= 20
        validation["is_valid"] = False
    
    # Check length similarity
    length_ratio = len(spanish_sig) / len(english_sig) if len(english_sig) > 0 else 1
    if length_ratio < 0.8 or length_ratio > 1.5:
        validation["issues"].append("Translation length seems unusual - verify completeness")
        validation["accuracy_score"] -= 15
    
    return validation


# JSON parsing utilities
def repair_patient_json(response: str) -> Dict[str, Any]:
    """Repair and parse patient JSON response"""
    try:
        result = parse_json(response)
        if result and isinstance(result, dict):
            return result
    except Exception:
        pass
    
    # Fallback extraction
    default_patient = {
        "full_name": "", "date_of_birth": "", "age": "",
        "facility_name": "", "address": "", "extraction_confidence": "low"
    }
    
    lines = response.split('\n')
    for line in lines:
        line = line.strip().lower()
        if 'name' in line and ':' in line:
            default_patient["full_name"] = line.split(':', 1)[1].strip()
        elif 'age' in line and ':' in line:
            default_patient["age"] = line.split(':', 1)[1].strip()
        elif ('dob' in line or 'birth' in line) and ':' in line:
            default_patient["date_of_birth"] = line.split(':', 1)[1].strip()
    
    return default_patient


# Additional common functions from various agents
def is_drug_substitution(original: str, extracted: str) -> bool:
    """Check if extracted drug name is a substitution rather than extraction"""
    if not original or not extracted:
        return False
    
    original_clean = original.lower().strip()
    extracted_clean = extracted.lower().strip()
    
    # If they're the same or extracted is contained in original, it's valid
    if extracted_clean == original_clean or extracted_clean in original_clean:
        return False
    
    # If original is contained in extracted, it's valid (e.g., "Lantus" -> "Lantus SoloStar")
    if original_clean in extracted_clean:
        return False
    
    # Check for common prefixes (first 3+ characters match)
    if len(original_clean) >= 3 and len(extracted_clean) >= 3:
        if original_clean[:3] == extracted_clean[:3]:
            return False
    
    # Otherwise, it's likely a substitution
    return True


def check_verb_route_consistency(verb: str, route: str) -> Dict[str, Any]:
    """Check if verb and route are consistent"""
    verb_lower = verb.lower()
    route_lower = route.lower()
    
    # Define valid verb-route combinations
    valid_combinations = {
        "take": ["by mouth", "orally", "po"],
        "apply": ["to affected area", "topically", "to skin"],
        "instill": ["in eye", "in eyes", "in ear", "in ears"],
        "insert": ["vaginally", "rectally"],
        "inject": ["subcutaneously", "intramuscularly", "intravenously"],
        "inhale": ["by inhalation", "into lungs"]
    }
    
    for valid_verb, valid_routes in valid_combinations.items():
        if verb_lower == valid_verb:
            if any(valid_route in route_lower for valid_route in valid_routes):
                return {"consistent": True, "issue": None}
            else:
                return {
                    "consistent": False,
                    "issue": f"Verb '{verb}' doesn't match route '{route}' - expected routes: {valid_routes}"
                }
    
    # If verb not in our list, assume it's valid (could be specialized)
    return {"consistent": True, "issue": None}


def assess_safety_risks(drug_name: str, structured_instructions: Dict[str, Any], rxnorm_context: Dict[str, Any]) -> Dict[str, Any]:
    """Assess safety risks based on drug name, instructions, and RxNorm context"""
    risk_assessment = {
        "overall_risk": "LOW",
        "risk_factors": [],
        "safety_concerns": [],
        "monitoring_required": [],
        "contraindications": []
    }
    
    # Check controlled substance risks
    schedule = rxnorm_context.get('drug_schedule')
    if schedule in ['II', 'III', 'IV']:
        risk_assessment["risk_factors"].append(f"Controlled substance (Schedule {schedule})")
        risk_assessment["overall_risk"] = "MODERATE"
        risk_assessment["monitoring_required"].append("Monitor for signs of dependency")
        
        # Check frequency for controlled substances
        frequency = structured_instructions.get("frequency", "")
        if "as needed" not in frequency.lower():
            risk_assessment["safety_concerns"].append("Fixed dosing schedule for controlled substance - consider PRN")
    
    # Route-specific risks
    route = structured_instructions.get("route", "")
    if "eye" in route.lower() and "drop" not in structured_instructions.get("form", "").lower():
        risk_assessment["safety_concerns"].append("Eye administration with non-drop formulation")
        risk_assessment["overall_risk"] = "HIGH"
    
    # Set final risk level
    if risk_assessment["safety_concerns"]:
        if risk_assessment["overall_risk"] == "LOW":
            risk_assessment["overall_risk"] = "MODERATE"
    
    return risk_assessment


def infer_dosage_form(original_name: str, rxnorm_name: str = "") -> str:
    """Infer dosage form from drug names"""
    combined = f"{original_name} {rxnorm_name}".lower()
    
    if any(word in combined for word in ['tablet', 'tab']):
        return 'tablet'
    elif any(word in combined for word in ['capsule', 'cap']):
        return 'capsule'
    elif any(word in combined for word in ['drop', 'solution', 'gtts']):
        return 'drops'
    elif any(word in combined for word in ['cream', 'ointment', 'gel', 'lotion']):
        return 'topical'
    elif any(word in combined for word in ['injection', 'injectable']):
        return 'injection'
    elif any(word in combined for word in ['patch']):
        return 'patch'
    else:
        return 'unknown'


def infer_administration_route(original_name: str, rxnorm_name: str = "") -> str:
    """Infer administration route from drug names"""
    combined = f"{original_name} {rxnorm_name}".lower()
    
    if any(word in combined for word in ['oral', 'tablet', 'capsule']):
        return 'by mouth'
    elif any(word in combined for word in ['ophthalmic', 'eye', 'ocular']):
        return 'in eye(s)'
    elif any(word in combined for word in ['topical', 'cream', 'ointment']):
        return 'to affected area'
    elif any(word in combined for word in ['vaginal']):
        return 'vaginally'
    elif any(word in combined for word in ['injection', 'injectable']):
        return 'by injection'
    else:
        return 'as directed'


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
