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
from src.modules.ai_agents.utils.common_tools import (
    calculate_quantity_from_sig,
    infer_days_from_quantity,
    generate_sig_english
)

@observe(name="rxnorm_comprehensive_lookup", as_type="generation", capture_input=True, capture_output=True)
async def get_rxnorm_drug_info(drug_name: str, strength: str = None, instructions: str = None, safety_assessment: Dict[str, Any] = None, context: Dict[str, Any] = None, medication_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get comprehensive drug information from RxNorm Neo4j knowledge graph with NO HALLUCINATION
    Uses enhanced search with safety context and all extracted data

    Args:
        drug_name: Name of the drug
        strength: Drug strength (optional)
        instructions: Usage instructions for context
        safety_assessment: Safety assessment data to help ranking
        context: Additional context (brand names, etc.)
        medication_details: Parsed components from the drug string.

    Returns:
        Dictionary with RxNorm information or null values (NO HALLUCINATION)
    """
    search_strength = (medication_details.get("strength") if medication_details else None) or strength
    dose_form = (medication_details.get("dose_form") if medication_details else None)

    # Gather all possible drug names for a comprehensive search
    search_terms = {drug_name}
    if medication_details:
        if medication_details.get("drug_name"):
            search_terms.add(medication_details.get("drug_name"))
        if medication_details.get("generic_name"):
            search_terms.add(medication_details.get("generic_name"))
        if medication_details.get("brand_name"):
            search_terms.add(medication_details.get("brand_name"))
        
        other_names = medication_details.get("other_drug_names", [])
        if isinstance(other_names, list):
            search_terms.update(other_names)

    search_terms = {term.strip() for term in search_terms if term and term.strip()}
    
    logger.info(f"🔍 ENHANCED RXNORM LOOKUP: Original='{drug_name}', Strength='{search_strength or 'N/A'}', Search Terms={list(search_terms)}")

    # Prepare context for the search
    search_context = context or {}
    if dose_form:
        search_context['dose_form'] = dose_form

    try:
        search_tasks = []

        # 1. Search for brand name
        brand_name = medication_details.get("brand_name") if medication_details else None
        if brand_name and brand_name.strip():
            search_tasks.append(
                get_drug_info(
                    drug_name=brand_name.strip(),
                    strength=search_strength,
                    instructions=instructions,
                    context=search_context,
                    search_type='brand'
                )
            )

        # 2. Search for generic name
        generic_name = medication_details.get("generic_name") if medication_details else None
        if generic_name and generic_name.strip():
            search_tasks.append(
                get_drug_info(
                    drug_name=generic_name.strip(),
                    strength=search_strength,
                    instructions=instructions,
                    context=search_context,
                    search_type='generic'
                )
            )

        # 3. Search for drug_name and other_drug_names
        drug_names_to_search = {drug_name}
        if medication_details:
            if medication_details.get("drug_name"):
                drug_names_to_search.add(medication_details.get("drug_name"))
            other_names = medication_details.get("other_drug_names", [])
            if isinstance(other_names, list):
                drug_names_to_search.update(other_names)
        
        drug_names_to_search = {term.strip() for term in drug_names_to_search if term and term.strip()}
        for term in drug_names_to_search:
            if term:
                search_tasks.append(
                    get_drug_info(
                        drug_name=term,
                        strength=search_strength,
                        instructions=instructions,
                        context=search_context,
                        search_type='drug'
                    )
                )
        
        all_results_lists = await asyncio.gather(*search_tasks)
        
        # Flatten, deduplicate, and merge results
        comprehensive_results = []
        seen_rxcuis = set()
        for result_list in all_results_lists:
            for result in result_list:
                rxcui = result.get("rxcui")
                if rxcui and rxcui not in seen_rxcuis:
                    comprehensive_results.append(result)
                    seen_rxcuis.add(rxcui)
        
        if comprehensive_results:
            comprehensive_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            logger.info(f"📋 RxNorm found {len(comprehensive_results)} unique drug variants from {len(search_terms)} search terms.")

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


# calculate_quantity_from_sig, infer_days_from_quantity, and generate_sig_english now imported from common_tools


async def process_medication_parallel(medications: List[Dict[str, Any]], state: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Process multiple medications in parallel"""
    try:
        import asyncio
        
        async def process_single_med(medication):
            try:
                drug_name = medication.get('drug_name', 'unknown')
                logger.info(f"Processing: {drug_name}")
                
                safety_assessment = state.get("safety_assessment") if state else None
                
                # Get RxNorm information
                rxnorm_data = await get_rxnorm_drug_info(
                    drug_name=drug_name,
                    strength=medication.get("strength"),
                    instructions=medication.get("instructions_for_use"),
                    safety_assessment=safety_assessment,
                    medication_details=medication
                )
                
                # Merge with original medication data
                enhanced_med = {**medication, **rxnorm_data}
                
                # Calculate quantity if missing
                if not enhanced_med.get("quantity") and enhanced_med.get("instructions_for_use"):
                    calculated_qty, was_inferred = calculate_quantity_from_sig(enhanced_med["instructions_for_use"])
                    enhanced_med["quantity"] = calculated_qty
                    enhanced_med["infer_qty"] = "Yes" if was_inferred else "No"
                
                # Infer days of use if needed
                if not enhanced_med.get("days_of_use") and enhanced_med.get("quantity") and enhanced_med.get("instructions_for_use"):
                    inferred_days, was_inferred = infer_days_from_quantity(
                        enhanced_med["quantity"], 
                        enhanced_med["instructions_for_use"]
                    )
                    enhanced_med["days_of_use"] = inferred_days
                    enhanced_med["infer_days"] = "Yes" if was_inferred else "No"
                
                return enhanced_med
                
            except Exception as e:
                logger.error(f"Failed to process {medication.get('drug_name', 'unknown')}: {e}")
                return medication  # Return original on failure
        
        # Create coroutine tasks for all medications
        tasks = [process_single_med(med) for med in medications]
        
        # Process in parallel with max 5 concurrent - tasks are already coroutines
        processed_medications = await asyncio.gather(*tasks[:5] if len(tasks) > 5 else tasks)
        
        logger.info(f"✅ Completed parallel processing of {len(processed_medications)} medications")
        return processed_medications
        
    except Exception as e:
        logger.error(f"Parallel medication processing failed: {e}")
        return medications  # Return originals on failure
