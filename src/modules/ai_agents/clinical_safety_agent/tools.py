"""
Clinical Safety Agent Tools
RxNorm integration and safety validation utilities
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_rxnorm_safety_context(rxnorm_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract safety-relevant information from RxNorm data
    
    Args:
        rxnorm_data: RxNorm lookup results
        
    Returns:
        Dict with safety-relevant RxNorm context
    """
    try:
        return {
            "rxcui": rxnorm_data.get("rxcui"),
            "drug_schedule": rxnorm_data.get("drug_schedule"),
            "brand_drug": rxnorm_data.get("brand_drug"),
            "ndc": rxnorm_data.get("ndc"),
            "is_controlled": bool(rxnorm_data.get("drug_schedule")),
            "has_brand": bool(rxnorm_data.get("brand_drug")),
            "rxnorm_available": bool(rxnorm_data.get("rxcui"))
        }
    except Exception as e:
        logger.error(f"Failed to extract RxNorm safety context: {e}")
        return {
            "rxcui": None,
            "drug_schedule": None,
            "brand_drug": None,
            "ndc": None,
            "is_controlled": False,
            "has_brand": False,
            "rxnorm_available": False
        }

def calculate_overall_safety_score(safety_results: List[Dict[str, Any]]) -> float:
    """
    Calculate overall safety score from individual medication assessments
    
    Args:
        safety_results: List of individual medication safety assessments
        
    Returns:
        Overall safety score (0-100)
    """
    try:
        if not safety_results:
            return 0.0
        
        # Extract valid safety scores
        scores = []
        for result in safety_results:
            try:
                score = float(result.get("safety_score", 0))
                if 0 <= score <= 100:
                    scores.append(score)
            except (ValueError, TypeError):
                continue
        
        if not scores:
            return 30.0  # Conservative default
        
        # Calculate weighted average (could be enhanced with drug-specific weights)
        overall_score = sum(scores) / len(scores)
        
        logger.info(f"Calculated overall safety score: {overall_score:.1f} from {len(scores)} medications")
        return round(overall_score, 1)
        
    except Exception as e:
        logger.error(f"Failed to calculate overall safety score: {e}")
        return 30.0  # Conservative default
