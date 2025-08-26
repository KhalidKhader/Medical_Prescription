"""
Drugs Agent Tools
Contains tools for medication processing including RxNorm integration
"""

from typing import Dict, Any, Optional, Tuple, List
import asyncio
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
from src.core.settings.logging import logger
from langfuse import observe


@observe(name="rxnorm_drug_lookup_enhanced", as_type="generation", capture_input=True, capture_output=True)
async def get_rxnorm_drug_info(drug_name: str, strength: str = None) -> Dict[str, Any]:
    """
    Get drug information from RxNorm Neo4j knowledge graph with comprehensive logging
    
    Args:
        drug_name: Name of the drug
        strength: Drug strength (optional)
        
    Returns:
        Dictionary with RxNorm information
    """
    logger.info(f"🔍 RXNORM LOOKUP START: Drug='{drug_name}', Strength='{strength or 'N/A'}'")
    
    try:
        # Log search initiation
        logger.info(f"📊 Initiating RxNorm search in Neo4j knowledge graph")
        
        # Search for drug in RxNorm
        search_results = await rxnorm_service.search_drug(drug_name, limit=5)
        
        logger.info(f"📋 RxNorm search returned {len(search_results) if search_results else 0} results")
        
        if search_results:
            # Log all search results for transparency
            for i, result in enumerate(search_results[:3]):  # Log top 3
                logger.info(f"🔸 Result {i+1}: {result.get('concept_name', 'N/A')} (ID: {result.get('concept_id', 'N/A')})")
            
            # Use the first/best match
            best_match = search_results[0]
            concept_id = best_match.get("concept_id")
            concept_name = best_match.get("concept_name", drug_name)
            
            if concept_id:
                logger.info(f"✅ RXNORM MATCH FOUND: Concept ID={concept_id}, Name='{concept_name}'")
                
                # Get detailed drug information
                logger.info(f"📖 Fetching detailed drug information for concept {concept_id}")
                drug_details = await rxnorm_service.get_drug_details(concept_id)
                
                # Log detailed information found
                rxcui = str(concept_id)
                ndc = drug_details.get("NDC")
                drug_schedule = drug_details.get("DEA_SCHEDULE") 
                brand_drug = drug_details.get("BRAND_NAME") or best_match.get("generic_name")
                brand_ndc = drug_details.get("BRAND_NDC")
                
                logger.info(f"💊 RXNORM DATA EXTRACTED:")
                logger.info(f"   - RxCUI: {rxcui}")
                logger.info(f"   - NDC: {ndc or 'Not found'}")
                logger.info(f"   - DEA Schedule: {drug_schedule or 'Not controlled'}")
                logger.info(f"   - Brand Drug: {brand_drug or 'Generic only'}")
                logger.info(f"   - Brand NDC: {brand_ndc or 'Not found'}")
                
                result_data = {
                    "rxcui": rxcui,
                    "ndc": ndc,
                    "drug_schedule": drug_schedule,
                    "brand_drug": brand_drug,
                    "brand_ndc": brand_ndc
                }
                
                logger.info(f"✅ RXNORM LOOKUP SUCCESS: {drug_name} mapped successfully")
                return result_data
            else:
                logger.warning(f"⚠️ No concept ID found in search results for {drug_name}")
        else:
            logger.warning(f"❌ RXNORM NO RESULTS: No matches found for '{drug_name}' in knowledge graph")
        
        # Return empty structure with logging
        logger.info(f"📝 Returning empty RxNorm data structure for {drug_name}")
        return {
            "rxcui": None,
            "ndc": None,
            "drug_schedule": None,
            "brand_drug": None,
            "brand_ndc": None
        }
        
    except Exception as e:
        logger.error(f"💥 RXNORM LOOKUP ERROR for '{drug_name}': {str(e)}")
        logger.error(f"🔧 Error type: {type(e).__name__}")
        
        # Return empty structure on error
        return {
            "rxcui": None,
            "ndc": None,
            "drug_schedule": None,
            "brand_drug": None,
            "brand_ndc": None
        }


def calculate_quantity_from_sig(instructions: str, days_supply: int = 30) -> Tuple[str, bool]:
    """
    Calculate quantity needed based on instructions
    
    Args:
        instructions: Prescription instructions
        days_supply: Number of days to calculate for
        
    Returns:
        Tuple of (calculated_quantity, was_inferred)
    """
    if not instructions or not instructions.strip():
        return "30", True  # Default fallback
    
    instructions_lower = instructions.lower()
    
    # Common patterns for quantity calculation
    daily_dose = 1  # Default
    frequency = 1   # Default
    
    # Extract frequency
    if "twice" in instructions_lower or "bid" in instructions_lower or "b.i.d" in instructions_lower:
        frequency = 2
    elif "three times" in instructions_lower or "tid" in instructions_lower or "t.i.d" in instructions_lower:
        frequency = 3
    elif "four times" in instructions_lower or "qid" in instructions_lower or "q.i.d" in instructions_lower:
        frequency = 4
    elif "daily" in instructions_lower or "qd" in instructions_lower or "once" in instructions_lower:
        frequency = 1
    
    # Extract dose amount (look for numbers)
    import re
    dose_match = re.search(r'(\d+)', instructions)
    if dose_match:
        daily_dose = int(dose_match.group(1))
    
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
    """
    Infer days of use from quantity and instructions
    
    Args:
        quantity: Prescribed quantity
        instructions: Usage instructions
        
    Returns:
        Tuple of (inferred_days, was_inferred)
    """
    if not quantity or not instructions:
        return "30", True  # Default
    
    try:
        # Extract numeric quantity
        import re
        qty_match = re.search(r'(\d+)', quantity)
        if not qty_match:
            return "30", True
        
        qty_num = int(qty_match.group(1))
        
        # Extract frequency from instructions
        instructions_lower = instructions.lower()
        frequency = 1  # Default once daily
        
        if "twice" in instructions_lower or "bid" in instructions_lower:
            frequency = 2
        elif "three times" in instructions_lower or "tid" in instructions_lower:
            frequency = 3
        elif "four times" in instructions_lower or "qid" in instructions_lower:
            frequency = 4
        
        # Extract dose per administration
        dose_match = re.search(r'(\d+)', instructions)
        dose_per_admin = int(dose_match.group(1)) if dose_match else 1
        
        # Calculate days
        total_daily_dose = dose_per_admin * frequency
        if total_daily_dose > 0:
            days = qty_num // total_daily_dose
            return str(max(1, days)), True
        
    except (ValueError, ZeroDivisionError):
        pass
    
    return "30", True  # Default fallback


def validate_medication_data(medication: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate medication data structure and content
    
    Args:
        medication: Medication dictionary to validate
        
    Returns:
        Tuple of (is_valid, warnings, cleaned_medication)
    """
    warnings = []
    cleaned_med = medication.copy()
    
    # Check required fields
    required_fields = ["drug_name", "strength", "instructions_for_use"]
    for field in required_fields:
        if not cleaned_med.get(field):
            warnings.append(f"Missing required field: {field}")
    
    # Validate drug name
    drug_name = cleaned_med.get("drug_name", "")
    if drug_name and len(drug_name.strip()) < 2:
        warnings.append("Drug name appears too short or invalid")
    
    # Validate strength format
    strength = cleaned_med.get("strength", "")
    if strength and not any(char.isdigit() for char in strength):
        warnings.append("Strength appears to lack numeric value")
    
    # Validate quantity
    quantity = cleaned_med.get("quantity")
    if quantity and str(quantity).strip():
        if not any(char.isdigit() for char in str(quantity)):
            # Check if it's a valid quantity description
            valid_units = ["tabs", "capsules", "ml", "bottles", "tubes", "g", "mg", "units"]
            if not any(unit in str(quantity).lower() for unit in valid_units):
                warnings.append("Quantity format appears invalid")
    
    # Validate refills
    refills = cleaned_med.get("refills")
    if refills is not None:
        try:
            refill_num = int(str(refills).replace("refills", "").replace("refill", "").strip())
            if refill_num < 0 or refill_num > 12:  # Reasonable refill range
                warnings.append("Refill count appears unusual")
            cleaned_med["refills"] = str(refill_num)
        except (ValueError, TypeError):
            warnings.append("Invalid refill format")
            cleaned_med["refills"] = "0"
    
    # Validate certainty score
    certainty = cleaned_med.get("certainty")
    if certainty is not None:
        try:
            cert_val = int(certainty)
            if cert_val < 0 or cert_val > 100:
                warnings.append("Certainty should be between 0-100")
                cleaned_med["certainty"] = 50
        except (ValueError, TypeError):
            warnings.append("Certainty should be numeric")
            cleaned_med["certainty"] = 50
    
    # Set defaults for inference flags
    if "infer_qty" not in cleaned_med:
        cleaned_med["infer_qty"] = "No"
    if "infer_days" not in cleaned_med:
        cleaned_med["infer_days"] = "No"
    
    is_valid = len(warnings) == 0
    return is_valid, warnings, cleaned_med


def generate_sig_english(instructions: str) -> str:
    """
    Generate clear English instructions from prescription sig
    
    Args:
        instructions: Raw prescription instructions
        
    Returns:
        Clear English instructions
    """
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


def repair_medications_json(json_text: str) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Repair and validate medications JSON using json_repair
    
    Args:
        json_text: Raw JSON text containing medications
        
    Returns:
        Tuple of (is_valid, parsed_medications, error_message)
    """
    try:
        parsed_data = parse_json(json_text)
        
        if not parsed_data:
            return False, None, "Failed to parse JSON"
        
        # Extract medications array
        if isinstance(parsed_data, dict) and "medications" in parsed_data:
            medications = parsed_data["medications"]
        elif isinstance(parsed_data, list):
            medications = parsed_data
        else:
            return False, None, "Invalid medication data structure"
        
        if not isinstance(medications, list):
            return False, None, "Medications must be a list"
        
        # Validate and clean each medication
        cleaned_medications = []
        for med in medications:
            if isinstance(med, dict):
                # Ensure all expected fields are present
                expected_fields = [
                    "drug_name", "strength", "instructions_for_use", "quantity", 
                    "infer_qty", "days_of_use", "infer_days", "refills", "certainty"
                ]
                for field in expected_fields:
                    if field not in med:
                        med[field] = None
                
                cleaned_medications.append(med)
        
        logger.info(f"Successfully repaired medications JSON with {len(cleaned_medications)} medications")
        return True, cleaned_medications, None
        
    except Exception as e:
        logger.error(f"Medications JSON repair failed: {e}")
        return False, None, str(e)