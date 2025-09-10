"""
Instructions of Use Agent Tools
Contains tools for RxNorm lookup, instruction parsing, and safety validation
"""

import logging
from typing import Dict, Any, Optional, List
from langfuse import observe
from src.modules.ai_agents.utils.common_tools import (
    infer_dosage_form,
    infer_administration_route,
    parse_instruction_components,
    generate_sig_english
)

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


# infer_dosage_form and infer_administration_route now imported from common_tools


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


# parse_instruction_components now imported from common_tools
@observe(name="parse_instruction_components", as_type="generation", capture_input=True, capture_output=True)
def parse_instruction_components_with_logging(raw_instructions: str) -> Dict[str, Any]:
    """Wrapper for parse_instruction_components with logging"""
    logger.info(f"📝 Parsing instruction components: '{raw_instructions}'")
    result = parse_instruction_components(raw_instructions)
    logger.info(f"✅ Parsed components: {result}")
    return result


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
                logger.warning("Failed to parse duration")
        
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