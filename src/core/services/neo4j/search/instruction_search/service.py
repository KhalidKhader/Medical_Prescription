"""
Instruction Search Module
Handles instruction-based drug searching in RxNorm using route and form analysis
"""

from typing import Dict, Any, List
from src.core.settings.logging import logger
from src.core.services.neo4j.search.instruction_search.methods import analyze_instructions, search_by_route_match, search_by_form_match, search_by_route_and_strength_match, search_by_form_and_strength_match

async def search_by_instructions(drug_name: str, instructions: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs based on instruction analysis"""
    try:
        analysis = analyze_instructions(instructions)
        if not any(analysis.values()):
            logger.info(f"No instruction hints found for '{instructions}'")
            return []
        
        all_results = []
        
        # Search by route hints
        for route_hint in analysis.get("route_hints", []):
            results = await search_by_route_match(drug_name, route_hint, limit)
            # Add analysis info to each result
            for result in results:
                result["instruction_analysis"] = analysis
                result["route_matched"] = route_hint
            all_results.extend(results)
        
        # Search by form hints
        for form_hint in analysis.get("form_hints", []):
            results = await search_by_form_match(drug_name, form_hint, limit)
            # Add analysis info to each result
            for result in results:
                result["instruction_analysis"] = analysis
                result["form_matched"] = form_hint
            all_results.extend(results)
        
        # Remove duplicates based on rxcui
        seen_rxcuis = set()
        unique_results = []
        for result in all_results:
            rxcui = result.get("rxcui")
            if rxcui and rxcui not in seen_rxcuis:
                seen_rxcuis.add(rxcui)
                unique_results.append(result)
        
        logger.info(f"Instruction search found {len(unique_results)} results for '{drug_name}' with instructions '{instructions}'")
        return unique_results[:limit]
        
    except Exception as e:
        logger.error(f"Instruction search failed: {e}")
        return []

async def search_instructions_with_strength(drug_name: str, instructions: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs based on instructions and strength"""
    try:
        analysis = analyze_instructions(instructions)
        if not any(analysis.values()):
            return []
        
        all_results = []
        
        # Search by route hints with strength
        for route_hint in analysis.get("route_hints", []):
            results = await search_by_route_and_strength_match(drug_name, route_hint, strength, limit)
            # Add analysis info to each result
            for result in results:
                result["instruction_analysis"] = analysis
                result["route_matched"] = route_hint
            all_results.extend(results)
        
        # Search by form hints with strength
        for form_hint in analysis.get("form_hints", []):
            results = await search_by_form_and_strength_match(drug_name, form_hint, strength, limit)
            # Add analysis info to each result
            for result in results:
                result["instruction_analysis"] = analysis
                result["form_matched"] = form_hint
            all_results.extend(results)
        
        # Remove duplicates and enhance with analysis
        seen_rxcuis = set()
        unique_results = []
        for result in all_results:
            rxcui = result.get("rxcui")
            if rxcui and rxcui not in seen_rxcuis:
                seen_rxcuis.add(rxcui)
                unique_results.append(result)
        
        logger.info(f"Instruction with strength search found {len(unique_results)} results")
        return unique_results[:limit]
        
    except Exception as e:
        logger.error(f"Instruction with strength search failed: {e}")
        return []