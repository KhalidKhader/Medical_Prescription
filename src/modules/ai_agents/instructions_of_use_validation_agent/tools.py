"""
Instructions of Use Validation Agent Tools
Contains tools for validating medication instructions for safety and completeness
"""

import logging
from typing import Dict, Any, List
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


@observe(name="validate_instruction_components", as_type="generation", capture_input=True, capture_output=True)
def validate_instruction_components(structured_instructions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate individual instruction components for completeness and accuracy
    
    Args:
        structured_instructions: Structured instruction components
        
    Returns:
        Component validation results
    """
    try:
        logger.info("🔍 Validating instruction components...")
        
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
        
        # Validate quantity
        quantity = structured_instructions.get("quantity")
        if not quantity:
            validation["issues"].append("Missing quantity per dose")
            validation["component_scores"]["quantity"] = 0
            validation["all_valid"] = False
        else:
            validation["component_scores"]["quantity"] = 100
        
        # Validate route
        route = structured_instructions.get("route")
        if not route:
            validation["issues"].append("Missing administration route")
            validation["component_scores"]["route"] = 0
            validation["all_valid"] = False
        else:
            validation["component_scores"]["route"] = 100
        
        # Validate frequency
        frequency = structured_instructions.get("frequency")
        if not frequency:
            validation["issues"].append("Missing dosing frequency")
            validation["component_scores"]["frequency"] = 0
            validation["all_valid"] = False
        else:
            validation["component_scores"]["frequency"] = 100
        
        # Validate verb-route consistency
        if verb and route:
            consistency = check_verb_route_consistency(verb, route)
            if not consistency["consistent"]:
                validation["issues"].append(consistency["issue"])
                validation["component_scores"]["consistency"] = 0
                validation["all_valid"] = False
            else:
                validation["component_scores"]["consistency"] = 100
        
        # Calculate overall score
        scores = list(validation["component_scores"].values())
        validation["overall_score"] = sum(scores) / len(scores) if scores else 0
        
        logger.info(f"✅ Component validation complete: {validation['overall_score']:.1f}%")
        return validation
        
    except Exception as e:
        logger.error(f"❌ Component validation failed: {e}")
        return {
            "all_valid": False,
            "overall_score": 0,
            "issues": [f"Validation error: {str(e)}"],
            "error": str(e)
        }


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


@observe(name="assess_safety_risks", as_type="generation", capture_input=True, capture_output=True)
def assess_safety_risks(drug_name: str, structured_instructions: Dict[str, Any], rxnorm_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess safety risks based on drug name, instructions, and RxNorm context
    
    Args:
        drug_name: Medication name
        structured_instructions: Instruction components
        rxnorm_context: RxNorm clinical context
        
    Returns:
        Safety risk assessment
    """
    try:
        logger.info(f"🛡️ Assessing safety risks for {drug_name}")
        
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
        
        # Drug-specific risk assessment
        drug_lower = drug_name.lower()
        
        # NSAID risks
        if any(nsaid in drug_lower for nsaid in ['ibuprofen', 'naproxen', 'diclofenac', 'aspirin']):
            risk_assessment["risk_factors"].append("NSAID - GI and cardiovascular risks")
            risk_assessment["monitoring_required"].append("Monitor for GI bleeding")
            risk_assessment["contraindications"].append("Avoid with active GI bleeding")
        
        # Acetaminophen overdose risk
        if 'acetaminophen' in drug_lower:
            quantity = structured_instructions.get("quantity", "")
            frequency = structured_instructions.get("frequency", "")
            if "4" in frequency or "6" in frequency:  # More than 3 times daily
                risk_assessment["safety_concerns"].append("High frequency acetaminophen - monitor total daily dose")
                risk_assessment["overall_risk"] = "MODERATE"
        
        # Antibiotic resistance
        if any(abx in drug_lower for abx in ['amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline']):
            duration = structured_instructions.get("duration")
            if not duration:
                risk_assessment["safety_concerns"].append("Antibiotic without specified duration")
                risk_assessment["overall_risk"] = "MODERATE"
        
        # Route-specific risks
        route = structured_instructions.get("route", "")
        if "eye" in route.lower() and "drop" not in structured_instructions.get("form", "").lower():
            risk_assessment["safety_concerns"].append("Eye administration with non-drop formulation")
            risk_assessment["overall_risk"] = "HIGH"
        
        # Set final risk level
        if risk_assessment["safety_concerns"]:
            if risk_assessment["overall_risk"] == "LOW":
                risk_assessment["overall_risk"] = "MODERATE"
        
        logger.info(f"🛡️ Risk assessment complete: {risk_assessment['overall_risk']} risk")
        return risk_assessment
        
    except Exception as e:
        logger.error(f"❌ Safety risk assessment failed: {e}")
        return {
            "overall_risk": "HIGH",
            "risk_factors": [f"Assessment error: {str(e)}"],
            "safety_concerns": ["Unable to assess safety - manual review required"],
            "error": str(e)
        }


@observe(name="validate_spanish_translation", as_type="generation", capture_input=True, capture_output=True)
def validate_spanish_translation(english_sig: str, spanish_sig: str) -> Dict[str, Any]:
    """
    Validate Spanish translation of medication instructions
    
    Args:
        english_sig: English instruction
        spanish_sig: Spanish translation
        
    Returns:
        Translation validation results
    """
    try:
        logger.info("🌐 Validating Spanish translation...")
        
        validation = {
            "is_valid": True,
            "accuracy_score": 100,
            "issues": [],
            "suggestions": []
        }
        
        # Check for accents (should not have any)
        accented_chars = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'Á', 'É', 'Í', 'Ó', 'Ú', 'Ñ']
        if any(char in spanish_sig for char in accented_chars):
            validation["issues"].append("Spanish translation contains accents - remove all accents")
            validation["accuracy_score"] -= 20
            validation["is_valid"] = False
        
        # Check for common translation patterns
        translation_checks = [
            ("take", ["tome", "tomar"]),
            ("tablet", ["tableta", "pastilla"]),
            ("by mouth", ["por la boca", "oral"]),
            ("daily", ["al dia", "diario"]),
            ("twice", ["dos veces"]),
            ("as needed", ["segun sea necesario", "cuando sea necesario"])
        ]
        
        english_lower = english_sig.lower()
        spanish_lower = spanish_sig.lower()
        
        for english_term, spanish_terms in translation_checks:
            if english_term in english_lower:
                if not any(spanish_term in spanish_lower for spanish_term in spanish_terms):
                    validation["suggestions"].append(f"Consider translating '{english_term}' to one of: {spanish_terms}")
                    validation["accuracy_score"] -= 10
        
        # Check length similarity (Spanish is typically 10-20% longer)
        length_ratio = len(spanish_sig) / len(english_sig) if len(english_sig) > 0 else 1
        if length_ratio < 0.8 or length_ratio > 1.5:
            validation["issues"].append("Translation length seems unusual - verify completeness")
            validation["accuracy_score"] -= 15
        
        logger.info(f"🌐 Spanish validation complete: {validation['accuracy_score']}%")
        return validation
        
    except Exception as e:
        logger.error(f"❌ Spanish translation validation failed: {e}")
        return {
            "is_valid": False,
            "accuracy_score": 0,
            "issues": [f"Validation error: {str(e)}"],
            "error": str(e)
        }


def repair_validation_json(json_str: str) -> Dict[str, Any]:
    """
    Repair and validate validation JSON response
    
    Args:
        json_str: JSON string to repair
        
    Returns:
        Repaired validation JSON
    """
    try:
        # Use json_repair to fix malformed JSON
        repaired_data = repair_json_loads(json_str)
        
        # Ensure required structure
        if not isinstance(repaired_data, dict):
            repaired_data = {"validation_passed": False, "error": "Invalid JSON structure"}
        
        # Ensure required fields
        required_fields = ["validation_passed", "overall_score"]
        for field in required_fields:
            if field not in repaired_data:
                if field == "validation_passed":
                    repaired_data[field] = False
                elif field == "overall_score":
                    repaired_data[field] = 0
        
        logger.info("✅ Successfully repaired validation JSON")
        return repaired_data
        
    except Exception as e:
        logger.error(f"❌ Validation JSON repair failed: {e}")
        return {
            "validation_passed": False,
            "overall_score": 0,
            "error": f"JSON repair failed: {str(e)}"
        }
