"""
Instructions of Use Agent Tools
Contains tools for RxNorm lookup, instruction parsing, and safety validation
"""

import json
import logging
from typing import Dict, Any, Optional, List
from json_repair import loads as repair_json_loads
from langfuse import observe


logger = logging.getLogger(__name__)


def get_rxnorm_instruction_context(drug_name: str, rxnorm_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get RxNorm context for instruction generation using existing RxNorm data
    
    Args:
        drug_name: Name of the medication
        rxnorm_data: Existing RxNorm data from drug lookup (can be None)
        
    Returns:
        RxNorm context with clinical information
    """
    try:
        # If no RxNorm data available, create basic context
        if not rxnorm_data or not rxnorm_data.get('rxcui'):
            logger.info(f"ℹ️ Creating basic RxNorm context for {drug_name}")
            context = {
                "found": False,
                "drug_name": drug_name,
                "rxcui": None,
                "ndc": None,
                "drug_schedule": None,
                "brand_name": None,
                "brand_ndc": None,
                # Infer basic information from drug name
                "dosage_form": infer_dosage_form(drug_name, ""),
                "route": infer_administration_route(drug_name, ""),
                "typical_frequency": infer_typical_frequency(drug_name, None),
                "safety_notes": generate_safety_notes(None, drug_name),
                "message": "Basic context created from drug name"
            }
            return context
        
        # Build context from existing RxNorm data
        context = {
            "found": True,
            "drug_name": rxnorm_data.get('verified_name', drug_name),
            "rxcui": rxnorm_data.get('rxcui'),
            "ndc": rxnorm_data.get('ndc'),
            "drug_schedule": rxnorm_data.get('drug_schedule'),
            "brand_name": rxnorm_data.get('brand_drug'),
            "brand_ndc": rxnorm_data.get('brand_ndc'),
            # Infer information from drug name and existing data
            "dosage_form": infer_dosage_form(drug_name, rxnorm_data.get('verified_name', '')),
            "route": infer_administration_route(drug_name, rxnorm_data.get('verified_name', '')),
            "typical_frequency": infer_typical_frequency(drug_name, rxnorm_data.get('drug_schedule')),
            "safety_notes": generate_safety_notes(rxnorm_data.get('drug_schedule'), drug_name)
        }
        
        logger.info(f"✅ Using existing RxNorm context: {context['drug_name']} (RxCUI: {context['rxcui']})")
        return context
        
    except Exception as e:
        logger.error(f"❌ RxNorm context processing failed: {e}")
        return {
            "found": False,
            "drug_name": drug_name,
            "error": str(e),
            "message": "RxNorm context error"
        }


def infer_dosage_form(original_name: str, rxnorm_name: str) -> str:
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


def infer_administration_route(original_name: str, rxnorm_name: str) -> str:
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


def infer_typical_frequency(drug_name: str, schedule: str) -> List[str]:
    """Infer typical dosing frequencies based on schedule only - no drug-specific logic"""
    frequencies = []
    
    # Schedule-based frequencies only
    if schedule in ['II', 'III', 'IV']:
        frequencies.extend(['as needed for pain', 'every 4-6 hours as needed'])
    else:
        frequencies.extend(['once daily', 'twice daily', 'three times daily'])
    
    return frequencies


def generate_safety_notes(schedule: str, drug_name: str) -> List[str]:
    """Generate safety notes based on drug schedule only - no drug-specific logic"""
    notes = []
    
    if schedule in ['II', 'III', 'IV']:
        notes.append(f"Controlled substance (Schedule {schedule}) - monitor for dependency")
        notes.append("Do not exceed prescribed dose")
        notes.append("Do not combine with alcohol")
    
    return notes


@observe(name="parse_instruction_components", as_type="generation", capture_input=True, capture_output=True)
def parse_instruction_components(raw_instructions: str) -> Dict[str, Any]:
    """
    Parse raw prescription instructions into structured components
    
    Args:
        raw_instructions: Raw prescription instructions
        
    Returns:
        Parsed instruction components
    """
    try:
        logger.info(f"📝 Parsing instruction components: '{raw_instructions}'")
        
        raw = raw_instructions.lower().strip()
        
        # Initialize components
        components = {
            "verb": None,
            "quantity": None,
            "form": None,
            "route": None,
            "frequency": None,
            "duration": None,
            "indication": None,
            "confidence": 0.7
        }
        
        # Parse quantity using string matching
        quantity_terms = ["tablet", "tab", "capsule", "cap", "drop", "gtts", "ml", "mg"]
        for term in quantity_terms:
            if term in raw:
                # Find numbers before the term
                term_pos = raw.find(term)
                before_term = raw[:term_pos].strip()
                # Extract last number before term
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
        
        # Parse duration using string matching
        if "until gone" in raw:
            components["duration"] = "until gone"
        else:
            # Look for "for X days" or "X days"
            if "day" in raw:
                day_pos = raw.find("day")
                before_day = raw[:day_pos].strip()
                # Extract last number before "day"
                nums = ''.join(c if c.isdigit() else ' ' for c in before_day)
                num_parts = nums.strip().split()
                if num_parts:
                    days = num_parts[-1]
                    components["duration"] = f"for {days} days"
        
        logger.info(f"✅ Parsed components: {components}")
        return components
        
    except Exception as e:
        logger.error(f"❌ Component parsing failed: {e}")
        return {
            "verb": None,
            "quantity": None, 
            "form": None,
            "route": None,
            "frequency": None,
            "duration": None,
            "indication": None,
            "confidence": 0.0,
            "error": str(e)
        }


@observe(name="validate_instruction_safety", as_type="generation", capture_input=True, capture_output=True)
def validate_instruction_safety(drug_name: str, structured_instructions: Dict[str, Any], rxnorm_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate instruction safety against RxNorm clinical context
    
    Args:
        drug_name: Medication name
        structured_instructions: Parsed instruction components
        rxnorm_context: RxNorm clinical context
        
    Returns:
        Safety validation results
    """
    try:
        logger.info(f"🛡️ Validating instruction safety for {drug_name}")
        
        validation = {
            "is_safe": True,
            "safety_score": 100,
            "concerns": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Route validation
        inferred_route = rxnorm_context.get('route', '')
        instruction_route = structured_instructions.get('route', '')
        
        if inferred_route and instruction_route:
            if inferred_route != instruction_route and inferred_route != 'as directed':
                validation["concerns"].append(f"Route mismatch: RxNorm suggests '{inferred_route}' but instruction uses '{instruction_route}'")
                validation["safety_score"] -= 20
        
        # Frequency validation for controlled substances
        schedule = rxnorm_context.get('drug_schedule')
        frequency = structured_instructions.get('frequency', '')
        
        if schedule in ['II', 'III', 'IV']:
            if 'as needed' not in frequency:
                validation["warnings"].append(f"Controlled substance (Schedule {schedule}) - consider 'as needed' dosing")
            validation["recommendations"].append("Monitor for signs of dependency")
        
        # Duration validation
        duration = structured_instructions.get('duration')
        if schedule in ['II', 'III'] and duration and 'day' in duration:
            try:
                days = int(duration.split()[1]) if 'for' in duration else 0
                if days > 7:
                    validation["warnings"].append(f"Long duration ({duration}) for Schedule {schedule} controlled substance")
                    validation["safety_score"] -= 10
            except:
                pass
        
        # Final safety determination
        if validation["safety_score"] < 70:
            validation["is_safe"] = False
        
        logger.info(f"🛡️ Safety validation complete: Score {validation['safety_score']}/100")
        return validation
        
    except Exception as e:
        logger.error(f"❌ Safety validation failed: {e}")
        return {
            "is_safe": False,
            "safety_score": 0,
            "concerns": [f"Validation error: {str(e)}"],
            "warnings": [],
            "recommendations": ["Manual pharmacist review required"]
        }


def repair_instruction_json(json_str: str) -> Dict[str, Any]:
    """
    Repair and validate instruction JSON response
    
    Args:
        json_str: JSON string to repair
        
    Returns:
        Repaired and validated JSON data
    """
    try:
        # Use json_repair to fix malformed JSON
        repaired_data = repair_json_loads(json_str)
        
        # Ensure required structure
        if not isinstance(repaired_data, dict):
            repaired_data = {"error": "Invalid JSON structure"}
        
        # Validate required fields
        required_fields = ["structured_instructions", "sig_english", "sig_spanish"]
        for field in required_fields:
            if field not in repaired_data:
                repaired_data[field] = None
        
        # Ensure structured_instructions has proper format
        if repaired_data.get("structured_instructions"):
            instruction_fields = ["verb", "quantity", "form", "route", "frequency", "duration", "indication"]
            for field in instruction_fields:
                if field not in repaired_data["structured_instructions"]:
                    repaired_data["structured_instructions"][field] = None
        
        logger.info("✅ Successfully repaired instruction JSON")
        return repaired_data
        
    except Exception as e:
        logger.error(f"❌ JSON repair failed: {e}")
        return {
            "structured_instructions": None,
            "sig_english": None,
            "sig_spanish": None,
            "error": f"JSON repair failed: {str(e)}"
        }
