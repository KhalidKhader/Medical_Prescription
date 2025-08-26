"""
Instructions of Use Agent Tools
Contains tools for RxNorm lookup, instruction parsing, and safety validation
"""

import json
import logging
from typing import Dict, Any, Optional, List
from json_repair import loads as repair_json_loads

# LangFuse observability
try:
    from langfuse import observe
except ImportError:
    def observe(name: str):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


@observe(name="rxnorm_instruction_context", as_type="generation", capture_input=True, capture_output=True)
async def get_rxnorm_instruction_context(drug_name: str, strength: str = None) -> Dict[str, Any]:
    """
    Get RxNorm context for instruction generation and safety validation
    
    Args:
        drug_name: Name of the medication
        strength: Medication strength (optional)
        
    Returns:
        RxNorm context with clinical information
    """
    try:
        from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
        
        logger.info(f"🔍 RXNORM INSTRUCTION CONTEXT: Drug='{drug_name}', Strength='{strength}'")
        
        # Search for drug information
        search_results = await rxnorm_service.search_drug(drug_name, limit=3)
        
        if not search_results:
            logger.warning(f"⚠️ No RxNorm context found for {drug_name}")
            return {
                "found": False,
                "drug_name": drug_name,
                "message": "No RxNorm data available"
            }
        
        # Get the best match
        best_match = search_results[0]
        concept_id = best_match.get('concept_id')
        
        # Get detailed information
        details = {}
        if concept_id:
            details = await rxnorm_service.get_drug_details(concept_id)
        
        # Build comprehensive context
        context = {
            "found": True,
            "drug_name": best_match.get('drug_name', drug_name),
            "concept_id": concept_id,
            "concept_name": best_match.get('concept_name'),
            "rxcui": concept_id,
            "ndc": details.get('NDC'),
            "drug_schedule": details.get('DEA_SCHEDULE'),
            "brand_name": details.get('BRAND_NAME'),
            "brand_ndc": details.get('BRAND_NDC'),
            # Infer common information for instruction context
            "dosage_form": infer_dosage_form(drug_name, best_match.get('drug_name', '')),
            "route": infer_administration_route(drug_name, best_match.get('drug_name', '')),
            "typical_frequency": infer_typical_frequency(drug_name, details.get('DEA_SCHEDULE')),
            "safety_notes": generate_safety_notes(details.get('DEA_SCHEDULE'), drug_name)
        }
        
        logger.info(f"✅ RxNorm context found: {context['drug_name']} (RxCUI: {concept_id})")
        return context
        
    except Exception as e:
        logger.error(f"❌ RxNorm context lookup failed: {e}")
        return {
            "found": False,
            "drug_name": drug_name,
            "error": str(e),
            "message": "RxNorm lookup error"
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
    """Infer typical dosing frequencies for a drug"""
    frequencies = []
    
    # Schedule-based frequencies
    if schedule in ['II', 'III', 'IV']:
        frequencies.extend(['as needed for pain', 'every 4-6 hours as needed'])
    
    # Drug-specific patterns
    drug_lower = drug_name.lower()
    if 'antibiotic' in drug_lower or any(abx in drug_lower for abx in ['amoxicillin', 'azithromycin', 'ciprofloxacin']):
        frequencies.extend(['twice daily', 'three times daily'])
    elif 'pain' in drug_lower or any(pain in drug_lower for pain in ['ibuprofen', 'acetaminophen', 'aspirin']):
        frequencies.extend(['every 6 hours as needed', 'every 4-6 hours as needed'])
    else:
        frequencies.extend(['once daily', 'twice daily'])
    
    return frequencies


def generate_safety_notes(schedule: str, drug_name: str) -> List[str]:
    """Generate safety notes based on drug schedule and name"""
    notes = []
    
    if schedule in ['II', 'III', 'IV']:
        notes.append(f"Controlled substance (Schedule {schedule}) - monitor for dependency")
        notes.append("Do not exceed prescribed dose")
        notes.append("Do not combine with alcohol")
    
    drug_lower = drug_name.lower()
    if any(nsaid in drug_lower for nsaid in ['ibuprofen', 'naproxen', 'diclofenac']):
        notes.append("Take with food to reduce stomach irritation")
    elif 'acetaminophen' in drug_lower:
        notes.append("Do not exceed 3000mg in 24 hours")
    
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
        
        # Parse quantity
        quantity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:tablet|tab|capsule|cap|drop|gtts|ml|mg)',
            r'(\d+(?:-\d+)?)\s*(?:tablet|tab|capsule|cap|drop|gtts)',
            r'(one|two|three|four|five|1|2|3|4|5)'
        ]
        
        for pattern in quantity_patterns:
            import re
            match = re.search(pattern, raw)
            if match:
                components["quantity"] = match.group(1)
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
        duration_patterns = [
            r'(?:for|x)\s*(\d+)\s*(?:day|d)',
            r'(\d+)\s*day',
            r'until\s+gone'
        ]
        
        for pattern in duration_patterns:
            import re
            match = re.search(pattern, raw)
            if match:
                if 'until' in pattern:
                    components["duration"] = "until gone"
                else:
                    days = match.group(1)
                    components["duration"] = f"for {days} days"
                break
        
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
