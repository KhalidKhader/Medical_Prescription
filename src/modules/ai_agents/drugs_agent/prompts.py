"""
Drugs Agent Prompts
Contains prompts for extracting and processing medication information
"""

from typing import Dict, Any, List


def get_medication_processing_prompt(medications: list) -> str:
    """Generate prompt for medication processing enhancement"""
    return f"""You are a clinical pharmacist processing prescription medications. Enhance and validate the following medication data for accuracy and completeness.

Medications to process:
{medications}

For each medication, provide:
1. Enhanced drug name accuracy
2. Strength validation and standardization
3. Instructions clarity improvement
4. Quantity and days supply verification
5. Clinical appropriateness assessment

Return JSON with enhanced medication data:
{{
    "processed_medications": [
        {{
            "drug_name": "standardized drug name",
            "strength": "validated strength",
            "instructions_for_use": "clarified instructions",
            "quantity": "verified quantity",
            "days_of_use": "calculated days",
            "clinical_notes": "any clinical observations",
            "confidence": number_0_to_100
        }}
    ],
    "processing_summary": {{
        "total_processed": number,
        "enhancements_made": ["list of improvements"],
        "warnings": ["any concerns found"]
    }}
}}"""

def get_safety_aware_drug_selection_prompt(rxnorm_results: List[Dict[str, Any]], safety_assessment: Dict[str, Any], original_drug: str) -> str:
    """
    Get prompt for selecting the best drug match avoiding wrong suffixes and using safety context

    Args:
        rxnorm_results: List of drug matches from RxNorm
        safety_assessment: Safety assessment data
        original_drug: Original drug name from prescription

    Returns:
        Enhanced drug selection prompt focusing on avoiding wrong suffixes
    """
    # Format safety information
    safety_status = safety_assessment.get("safety_status", "unknown")
    safety_score = safety_assessment.get("safety_score", "N/A")
    safety_flags = safety_assessment.get("safety_flags", [])
    recommendations = safety_assessment.get("recommendations", [])

    # Format drug options with enhanced details
    drug_options_text = ""
    for i, drug in enumerate(rxnorm_results[:10]):  # Show top 10 options for better selection
        drug_options_text += f"""
Option {i+1}:
- RXCUI: {drug.get('rxcui', 'N/A')}
- Name: {drug.get('drug_name', 'Unknown')}
- Generic: {drug.get('generic_name', 'N/A')}
- Strength: {drug.get('strength', 'N/A')}
- Route: {drug.get('route', 'N/A')}
- Dose Form: {drug.get('dose_form', 'N/A')}
- Term Type: {drug.get('term_type', 'N/A')}
- Search Method: {drug.get('search_method', 'N/A')}
- Relevance Score: {drug.get('relevance_score', 0):.1f}
"""

    return f"""
You are an expert clinical pharmacist selecting the most appropriate drug match from RxNorm knowledge graph.

ORIGINAL PRESCRIPTION DRUG: "{original_drug}"

AVAILABLE DRUG OPTIONS FROM RXNORM:{drug_options_text}

CRITICAL SELECTION RULES - AVOID WRONG SUFFIXES:
1. **DO NOT SELECT "chewable", "rapid disintegrating", "extended release", "delayed release", "enteric coated" UNLESS explicitly ordered**
2. **DO NOT SELECT combination products unless the original prescription clearly indicates a combination**
3. **PREFER standard tablets/capsules over specialized forms when no specific form is mentioned**
4. **MATCH the exact strength - avoid approximations**
5. **ENSURE route compatibility with prescription instructions**

SAFETY ASSESSMENT CONTEXT:
- Safety Status: {safety_status}
- Safety Score: {safety_score}/100
- Critical Safety Flags: {', '.join(safety_flags[:5]) if safety_flags else 'None identified'}

SELECTION PRIORITY (in order):
1. **Exact Drug Name + Exact Strength + Standard Form** (tablet, capsule, solution)
2. **Generic Equivalent + Exact Strength + Standard Form**
3. **Brand Equivalent + Exact Strength + Standard Form**
4. **Safety Context Match** (mentioned in safety assessment)
5. **Highest Relevance Score** with appropriate form

AVOID THESE COMMON MISTAKES:
- Selecting "chewable" when regular tablet was prescribed
- Choosing "extended release" for immediate release prescriptions
- Picking combination drugs when single ingredient was ordered
- Using wrong strength approximations
- Mismatching routes (oral vs topical vs ophthalmic)

Return ONLY valid JSON:

{{
    "selected_rxcui": "best matching RXCUI",
    "selected_drug_name": "selected drug name",
    "selection_reason": "why this option was selected avoiding wrong suffixes",
    "form_justification": "why this dosage form is appropriate",
    "strength_match": "exact or approximate strength match",
    "avoided_issues": "any wrong suffixes or forms avoided",
    "safety_alignment": "how well this matches safety assessment",
    "confidence_score": 85,
    "alternative_options": ["rxcui1", "rxcui2"]
}}
"""
