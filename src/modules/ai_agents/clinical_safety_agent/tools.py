"""
Clinical Safety Agent Tools
RxNorm integration and safety validation utilities
"""

import logging
from typing import Dict, Any, List
from json_repair import loads as repair_json_loads

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


def validate_safety_assessment_response(response_content: str) -> Dict[str, Any]:
    """
    Validate and repair safety assessment response from Gemini
    
    Args:
        response_content: Raw response from Gemini
        
    Returns:
        Validated safety assessment dictionary
    """
    try:
        # Parse and repair JSON response
        safety_data = repair_json_loads(response_content)
        
        # Validate required fields
        required_fields = {
            "safety_score": 50,  # Default cautious score
            "safety_flags": [],
            "recommendations": [],
            "risk_level": "MEDIUM",
            "requires_pharmacist_review": True,
            "safety_notes": "Assessment completed"
        }
        
        for field, default_value in required_fields.items():
            if field not in safety_data:
                safety_data[field] = default_value
                logger.warning(f"Missing field '{field}' in safety assessment, using default: {default_value}")
        
        # Validate safety_score is numeric and within range
        try:
            score = float(safety_data["safety_score"])
            if not 0 <= score <= 100:
                logger.warning(f"Safety score {score} out of range, clamping to 0-100")
                score = max(0, min(100, score))
            safety_data["safety_score"] = score
        except (ValueError, TypeError):
            logger.warning("Invalid safety_score, using default: 50")
            safety_data["safety_score"] = 50
        
        # Validate risk_level
        valid_risk_levels = ["LOW", "MEDIUM", "HIGH"]
        if safety_data["risk_level"] not in valid_risk_levels:
            logger.warning(f"Invalid risk_level '{safety_data['risk_level']}', using MEDIUM")
            safety_data["risk_level"] = "MEDIUM"
        
        # Ensure lists are actually lists
        list_fields = ["safety_flags", "recommendations"]
        for field in list_fields:
            if not isinstance(safety_data[field], list):
                safety_data[field] = [str(safety_data[field])] if safety_data[field] else []
        
        # Add monitoring_requirements if missing
        if "monitoring_requirements" not in safety_data:
            safety_data["monitoring_requirements"] = []
        
        logger.info(f"✅ Safety assessment validated: Score {safety_data['safety_score']}, Risk {safety_data['risk_level']}")
        return safety_data
        
    except Exception as e:
        logger.error(f"Failed to validate safety assessment: {e}")
        return get_default_safety_assessment("Validation failed", str(e))


def get_default_safety_assessment(drug_name: str, error_msg: str) -> Dict[str, Any]:
    """
    Get default safety assessment when evaluation fails
    
    Args:
        drug_name: Name of the drug being assessed
        error_msg: Error message describing the failure
        
    Returns:
        Default safety assessment dictionary
    """
    return {
        "safety_score": 30,  # Conservative score indicating need for review
        "safety_flags": [f"Safety assessment failed for {drug_name}: {error_msg}"],
        "recommendations": [
            "Immediate manual pharmacist review required",
            "Verify medication details and dosing manually",
            "Confirm patient safety before dispensing"
        ],
        "risk_level": "HIGH",
        "requires_pharmacist_review": True,
        "safety_notes": f"Automated safety assessment failed for {drug_name}. Manual clinical review required before dispensing.",
        "monitoring_requirements": ["Manual safety verification required"]
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


def determine_safety_status(overall_score: float) -> str:
    """
    Determine safety status based on overall score
    
    Args:
        overall_score: Overall safety score (0-100)
        
    Returns:
        Safety status: "safe", "caution", or "unsafe"
    """
    try:
        if overall_score >= 90:
            return "safe"
        elif overall_score >= 70:
            return "caution"
        else:
            return "unsafe"
    except:
        return "caution"  # Default to caution if calculation fails


def extract_critical_safety_flags(safety_results: List[Dict[str, Any]]) -> List[str]:
    """
    Extract and deduplicate critical safety flags from all assessments
    
    Args:
        safety_results: List of individual medication safety assessments
        
    Returns:
        List of unique critical safety flags
    """
    try:
        all_flags = []
        
        for result in safety_results:
            flags = result.get("safety_flags", [])
            if isinstance(flags, list):
                all_flags.extend(flags)
            elif flags:  # Single flag as string
                all_flags.append(str(flags))
        
        # Remove duplicates while preserving order
        unique_flags = []
        seen = set()
        for flag in all_flags:
            if flag and flag not in seen:
                unique_flags.append(flag)
                seen.add(flag)
        
        return unique_flags
        
    except Exception as e:
        logger.error(f"Failed to extract safety flags: {e}")
        return ["Safety flag extraction failed"]


def extract_safety_recommendations(safety_results: List[Dict[str, Any]]) -> List[str]:
    """
    Extract and deduplicate safety recommendations from all assessments
    
    Args:
        safety_results: List of individual medication safety assessments
        
    Returns:
        List of unique safety recommendations
    """
    try:
        all_recommendations = []
        
        for result in safety_results:
            recommendations = result.get("recommendations", [])
            if isinstance(recommendations, list):
                all_recommendations.extend(recommendations)
            elif recommendations:  # Single recommendation as string
                all_recommendations.append(str(recommendations))
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec and rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        return unique_recommendations
        
    except Exception as e:
        logger.error(f"Failed to extract recommendations: {e}")
        return ["Manual pharmacist review recommended"]
