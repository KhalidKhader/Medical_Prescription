from typing import Dict, Any, List
from src.core.settings.logging import logger



def calculate_scores(
    results: List[Dict[str, Any]],
    original_drug: str,
    strength: str = None,
    instructions: str = None,
    safety_context: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Calculate comprehensive relevance scores for all results
    
    Args:
        results: List of drug results
        original_drug: Original drug name from prescription
        strength: Drug strength
        instructions: Usage instructions
        safety_context: Safety assessment context
        
    Returns:
        Results with comprehensive scores
    """
    try:
        for result in results:
            score = 0.0
            scoring_details = {}
            
            # Base score from search method confidence
            base_confidence = result.get("match_confidence", 0.5)
            score += base_confidence * 30  # Up to 30 points
            scoring_details["base_confidence"] = base_confidence
            
            # Drug name matching (30 points max)
            drug_name = result.get("drug_name", "").lower()
            original_lower = original_drug.lower()
            
            if drug_name == original_lower:
                score += 30
                scoring_details["name_match"] = "exact"
            elif original_lower in drug_name or drug_name in original_lower:
                score += 20
                scoring_details["name_match"] = "partial"
            else:
                score += 10
                scoring_details["name_match"] = "weak"
            
            # Strength matching (20 points max)
            if strength and result.get("strength"):
                result_strength = result.get("strength", "").lower()
                strength_nums = ''.join(c for c in strength if c.isdigit())
                result_nums = ''.join(c for c in result_strength if c.isdigit())
                
                if strength_nums and result_nums and strength_nums == result_nums:
                    score += 20
                    scoring_details["strength_match"] = "exact"
                elif strength.lower() in result_strength:
                    score += 15
                    scoring_details["strength_match"] = "partial"
                else:
                    score += 5
                    scoring_details["strength_match"] = "weak"
            
            # Multiple search method bonus (10 points max)
            search_methods = result.get("search_methods_found", [])
            if len(search_methods) > 1:
                score += min(len(search_methods) * 2, 10)
                scoring_details["multi_method_bonus"] = len(search_methods)
            
            # Primary search method bonus (15 points max) - prioritize strength-focused methods
            primary_method = result.get("primary_search_method", "")
            if primary_method in ["strength_focused", "comprehensive_instruction"]:
                score += 15  # Highest priority for strength-focused searches
                scoring_details["strength_method_bonus"] = 15
            elif primary_method in ["exact_match", "exact_match_strength"]:
                score += 10
            elif primary_method in ["brand_exact", "brand_strength"]:
                score += 8
            elif primary_method in ["fuzzy_match_strength", "synonym_search"]:
                score += 6
            else:
                score += 3
            scoring_details["primary_method_bonus"] = primary_method

            # Additional strength score bonus (20 points max)
            if result.get("strength_score", 0) > 0:
                strength_bonus = min(result.get("strength_score", 0) / 25.0 * 20, 20)
                score += strength_bonus
                scoring_details["strength_focused_bonus"] = strength_bonus
            
            # Safety context bonus (if available)
            if safety_context:
                # This would be implemented based on safety assessment structure
                scoring_details["safety_bonus"] = 0
            
            result["comprehensive_score"] = round(score, 2)
            result["scoring_details"] = scoring_details
        
        # Sort by comprehensive score
        results.sort(key=lambda x: x.get("comprehensive_score", 0), reverse=True)
        
        logger.info(f"📊 Comprehensive scoring complete for {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive scoring failed: {e}")
        return results
