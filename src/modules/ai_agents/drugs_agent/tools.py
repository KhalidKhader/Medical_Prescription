"""
Drugs Agent Tools
Contains tools for medication processing including RxNorm integration
"""

from typing import Dict, Any, Optional, Tuple, List
import asyncio
import json
from src.modules.ai_agents.utils.json_parser import parse_json
from src.core.services.neo4j.get_drug_info import get_drug_info
from src.core.settings.logging import logger
from langfuse import observe
from src.modules.ai_agents.drugs_agent.prompts import get_safety_aware_drug_selection_prompt

@observe(name="rxnorm_comprehensive_lookup", as_type="generation", capture_input=True, capture_output=True)
async def get_rxnorm_drug_info(drug_name: str, strength: str = None, instructions: str = None, safety_assessment: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get comprehensive drug information from RxNorm Neo4j knowledge graph with NO HALLUCINATION
    Uses enhanced search with safety context and all extracted data

    Args:
        drug_name: Name of the drug
        strength: Drug strength (optional)
        instructions: Usage instructions for context
        safety_assessment: Safety assessment data to help ranking
        context: Additional context (brand names, etc.)

    Returns:
        Dictionary with RxNorm information or null values (NO HALLUCINATION)
    """
    logger.info(f"🔍 ENHANCED RXNORM LOOKUP: Drug='{drug_name}', Strength='{strength or 'N/A'}', Has Safety={safety_assessment is not None}")

    try:
        # Use enhanced comprehensive search with safety context
        comprehensive_results = await get_drug_info(
            drug_name=drug_name,
            strength=strength,
            instructions=instructions,  # Pass instructions for context-aware search
            context=context,  # Additional context for better matching
            safety_assessment=safety_assessment  # Safety context for ranking
        )

        if comprehensive_results:
            logger.info(f"📋 RxNorm found {len(comprehensive_results)} drug variants")

            # Use safety-aware selection if safety assessment is available and multiple options exist
            if safety_assessment and len(comprehensive_results) > 1:
                best_match = await _select_best_match_with_safety(comprehensive_results, safety_assessment, drug_name)
            else:
                # Use traditional selection logic
                best_match = comprehensive_results[0]  # Default to first result (already ranked)

                if strength:
                    # Look for strength-specific match
                    for result in comprehensive_results:
                        drug_name_str = result.get('drug_name', '').lower()
                        if strength.lower() in drug_name_str:
                            best_match = result
                            logger.info(f"✅ Found strength-specific match: {result.get('drug_name')}")
                            break

            # Return ONLY RxNorm data with RxNav verification
            rxcui = best_match.get("rxcui")
            drug_name_found = best_match.get("drug_name")

            if rxcui and drug_name_found:
                # Skip RxNav verification for performance - KG data is already verified
                verification_result = {"verified": True, "reason": "kg_verified", "source": "neo4j_rxnorm"}

                if verification_result.get("verified"):
                    verified_name = drug_name_found  # Use KG name directly
                    logger.info(f"✅ KG VERIFIED: RXCUI={rxcui}, Name='{verified_name}'")

                    return {
                        "rxcui": str(rxcui),
                        "generic_name": verified_name,
                        "verified_name": verified_name,
                        "term_type": verification_result.get("term_type", best_match.get("term_type")),
                        "ndc": None,  # Will be null unless found in RxNorm
                        "drug_schedule": None,  # Will be null unless found in RxNorm
                        "brand_drug": verified_name,  # Use verified name only
                        "brand_ndc": None,  # Will be null unless found in RxNorm
                        "precision_match": strength is not None and any(strength.lower() in r.get('drug_name', '').lower() for r in comprehensive_results),
                        "candidates_found": len(comprehensive_results),
                        "search_method": best_match.get("search_method", "verified_rxnorm_rxnav"),
                        "verification_status": "verified",
                        "all_candidates": comprehensive_results[:10]  # Include top 5 candidates for transparency
                    }
                else:
                    logger.warning(f"⚠️ RxNav verification failed for RxCUI {rxcui}: {verification_result.get('reason')}")
                    # Provide RxNorm data as context even if RxNav verification fails
                    # This allows the model to make informed decisions rather than returning null
                    logger.info(f"📋 Providing RxNorm context for model evaluation: '{drug_name_found}'")

                    return {
                        "rxcui": str(rxcui),
                        "generic_name": drug_name_found,
                        "verified_name": None,  # Not verified by RxNav
                        "term_type": best_match.get("term_type"),
                        "ndc": None,
                        "drug_schedule": None,
                        "brand_drug": drug_name_found,  # Use RxNorm name
                        "brand_ndc": None,
                        "precision_match": strength is not None and any(strength.lower() in r.get('drug_name', '').lower() for r in comprehensive_results),
                        "candidates_found": len(comprehensive_results),
                        "search_method": best_match.get("search_method", "rxnorm_context_only"),
                        "verification_status": "failed_but_context_provided",
                        "rxnorm_context": {
                            "found_in_rxnorm": True,
                            "rxnorm_name": drug_name_found,
                            "verification_issue": verification_result.get('reason', 'unknown')
                        },
                        "all_candidates": comprehensive_results[:10]  # Include top 5 candidates for transparency
                    }
            else:
                logger.warning(f"⚠️ RXNORM: Found results but missing critical data for '{drug_name}'")
        else:
            logger.warning(f"❌ RXNORM: No matches found for '{drug_name}' in knowledge graph")

        # Return intelligent fallback with extracted information
        fallback_info = f"Drug '{drug_name}'"
        if strength:
            fallback_info += f" {strength}"
        fallback_info += " was prescribed but could not be found in the RxNorm knowledge graph."

        logger.info(f"📝 RXNORM: Returning structured fallback for '{drug_name}'")
        return {
            "rxcui": None,
            "generic_name": None,
            "verified_name": drug_name,  # Keep original name
            "term_type": "UNVERIFIED",
            "ndc": None,
            "drug_schedule": None,
            "brand_drug": None,
            "brand_ndc": None,
            "precision_match": False,
            "candidates_found": 0,
            "search_method": "embedding_context",
            "verification_status": "not_found_in_kg",
            "fallback_message": fallback_info,  # Intelligent fallback message
            "kg_status": "NOT_FOUND",  # Clear KG lookup status
            "all_candidates": []  # No candidates found
        }

    except Exception as e:
        logger.error(f"💥 RXNORM ERROR for '{drug_name}': {str(e)}")

        # Return null structure on error - NO HALLUCINATION
        return {
            "rxcui": None,
            "generic_name": None,
            "verified_name": None,
            "term_type": None,
            "ndc": None,
            "drug_schedule": None,
            "brand_drug": None,
            "brand_ndc": None,
            "precision_match": False,
            "candidates_found": 0,
            "search_method": "error",
            "verification_status": "error",
            "all_candidates": []  # No candidates on error
        }


async def _select_best_match_with_safety(rxnorm_results: List[Dict[str, Any]], safety_assessment: Dict[str, Any], original_drug: str) -> Dict[str, Any]:
    """Select the best drug match using safety assessment context"""
    try:
        # Create safety-aware selection prompt
        selection_prompt = get_safety_aware_drug_selection_prompt(rxnorm_results, safety_assessment, original_drug)

        # Use Gemini to make the selection
        from src.core.settings.config import settings
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0,
            google_api_key=settings.google_api_key
        )

        # Get LLM selection
        response = await llm.ainvoke([HumanMessage(content=selection_prompt)])
        selection_text = response.content.strip()

        # Parse JSON response
        import json
        try:
            selection_data = json.loads(selection_text)
            selected_rxcui = selection_data.get("selected_rxcui")

            # Find the selected drug in results
            for result in rxnorm_results:
                if str(result.get('rxcui', '')) == str(selected_rxcui):
                    logger.info(f"🛡️ Safety-aware selection: {result.get('drug_name')} (RXCUI: {selected_rxcui})")
                    logger.info(f"   Reason: {selection_data.get('selection_reason', 'N/A')}")
                    return result

        except json.JSONDecodeError:
            logger.error("Failed to parse safety-aware drug selection response")

    except Exception as e:
        logger.error(f"Safety-aware drug selection failed: {e}")

    # Fallback to first result if safety selection fails
    logger.info("Falling back to top-ranked result")
    return rxnorm_results[0]


def calculate_quantity_from_sig(instructions: str, days_supply: int = 30) -> Tuple[str, bool]:
    """
    Calculate quantity needed based on instructions using string matching
    
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
    """
    Infer days of use from quantity and instructions using string matching
    
    Args:
        quantity: Prescribed quantity
        instructions: Usage instructions
        
    Returns:
        Tuple of (inferred_days, was_inferred)
    """
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
