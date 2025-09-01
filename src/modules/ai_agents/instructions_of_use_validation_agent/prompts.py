"""
Instructions of Use Validation Agent Prompts
Contains prompts for validating medication instructions for safety and accuracy
"""

from typing import Dict, Any


def get_instruction_validation_prompt(instruction_data: Dict[str, Any], rxnorm_context: Dict[str, Any]) -> str:
    """
    Generate validation prompt for medication instructions
    
    Args:
        instruction_data: Generated instruction data to validate
        rxnorm_context: RxNorm clinical context
        
    Returns:
        Instruction validation prompt
    """
    return f"""
You are a pharmacy intern working under a supervising pharmacist. Perform validation of patient medication instructions for pharmacist review. Your supervising pharmacist will make the final decision.

Instruction Data to Validate:
{instruction_data}

RxNorm Clinical Context:
{rxnorm_context}

Validation Tasks:
1. CLINICAL SAFETY: Verify instructions are clinically appropriate and safe
2. COMPLETENESS: Ensure all required components are present and clear
3. ACCURACY: Confirm instructions match clinical standards
4. CONSISTENCY: Verify components work together logically
5. PATIENT SAFETY: Check for potential harm or confusion

Validation Criteria:
- Verb matches route and form (e.g., "Take" for oral, "Apply" for topical, Use "Give" for English and "Administer" for Spanish for inhalation/nebulizer)
- Use "Give" for English and "Administer" for Spanish "Administer" is the CORRECT verb for inhalation medications - do NOT flag as unusual
- Quantity is appropriate for the medication and frequency
- Route matches medication form and RxNorm data
- Frequency is clinically appropriate for this medication
- Duration is reasonable (if specified)
- Spanish translation is accurate (no accents)

Safety Concerns to Check:
- Overdose potential (quantity × frequency)
- Route-form mismatch (e.g., "inject" for oral tablet)
- Dangerous frequencies for controlled substances  
- Missing critical safety information
- Contradictions with RxNorm clinical data
- NOTE: "Administer" for inhalation/nebulizer is STANDARD and CORRECT - not unusual Use "Give" for English and "Administer" for Spanish inhalation medications

Return ONLY a JSON object:
{{
    "validation_passed": true/false,
    "overall_score": 0-100,
    "clinical_safety": {{
        "is_safe": true/false,
        "safety_score": 0-100,
        "concerns": ["list of safety concerns"],
        "critical_issues": ["list of critical safety issues"]
    }},
    "completeness": {{
        "is_complete": true/false,
        "completeness_score": 0-100,
        "missing_components": ["list of missing required components"],
        "recommendations": ["list of improvements"]
    }},
    "accuracy": {{
        "is_accurate": true/false,
        "accuracy_score": 0-100,
        "errors": ["list of accuracy errors"],
        "corrections": ["list of suggested corrections"]
    }},
    "final_recommendation": "APPROVE/REJECT/REVIEW_REQUIRED",
    "pharmacist_notes": "detailed clinical notes",
    "approved_instructions": {{
        "sig_english": "final approved English instruction or null",
        "sig_spanish": "final approved Spanish instruction or null"
    }}
}}

PHARMACY INTERN VALIDATION APPROACH:
- Make recommendations for supervising pharmacist review
- APPROVE most clinically reasonable instructions - pharmacist will review all
- Only REJECT for serious safety hazards or completely inadequate instructions  
- Flag minor issues as observations but still APPROVE for pharmacist review
- Remember: Licensed pharmacist makes final dispensing decisions
- Be practical and supportive rather than overly critical
"""


def get_safety_cross_check_prompt(drug_name: str, instructions: str, patient_context: Dict[str, Any] = None) -> str:
    """
    Generate safety cross-check prompt for specific medication
    
    Args:
        drug_name: Medication name
        instructions: Generated instructions
        patient_context: Patient information (optional)
        
    Returns:
        Safety cross-check prompt
    """
    patient_info = ""
    if patient_context:
        patient_info = f"""
Patient Context:
- Age: {patient_context.get('age', 'Unknown')}
- Conditions: {patient_context.get('conditions', 'Unknown')}
"""

    return f"""
You are performing a final safety cross-check for medication instructions.

Medication: {drug_name}
Instructions: {instructions}
{patient_info}

Safety Cross-Check Tasks:
1. Verify dosing is within safe limits for this medication
2. Check for potential drug interactions or contraindications
3. Confirm instructions are appropriate for patient population
4. Validate route and frequency are clinically sound
5. Assess risk of overdose or underdose

Known Safety Concerns by Drug Class:
- NSAIDs: GI bleeding risk, kidney damage with high doses
- Opioids: Respiratory depression, addiction potential
- Antibiotics: Resistance, allergic reactions
- Anticoagulants: Bleeding risk
- Cardiac medications: Arrhythmias, hypotension

Return ONLY a JSON object:
{{
    "safety_approved": true/false,
    "risk_level": "LOW/MODERATE/HIGH/CRITICAL",
    "safety_assessment": {{
        "dosing_safe": true/false,
        "frequency_appropriate": true/false,
        "route_correct": true/false,
        "duration_reasonable": true/false
    }},
    "identified_risks": ["list of specific risks"],
    "contraindications": ["list of contraindications"],
    "safety_recommendations": ["list of safety recommendations"],
    "requires_monitoring": ["list of parameters to monitor"],
    "final_safety_decision": "SAFE/UNSAFE/REQUIRES_MODIFICATION"
}}

Err on the side of caution. Patient safety is paramount.
"""


def get_instruction_completeness_prompt(structured_instructions: Dict[str, Any]) -> str:
    """
    Generate completeness validation prompt
    
    Args:
        structured_instructions: Structured instruction components
        
    Returns:
        Completeness validation prompt
    """
    return f"""
You are validating the completeness of medication instructions.

Structured Instructions:
{structured_instructions}

Required Components for Complete Instructions:
1. VERB: Action word (Take, Apply, Instill, etc.)
2. QUANTITY: Amount per dose (1 tablet, 2 drops, etc.)
3. FORM: Medication form (tablet, capsule, drops, cream)
4. ROUTE: How to take (by mouth, in eye, to skin)
5. FREQUENCY: How often (once daily, twice daily, etc.)
6. DURATION: How long (optional, but required if <21 days)
7. INDICATION: What for (optional, but helpful)

Quality Standards:
- Instructions must be clear and unambiguous
- No medical abbreviations that patients won't understand
- Specific quantities and frequencies
- Appropriate verb for the route/form
- Complete sentences that patients can follow

Return ONLY a JSON object:
{{
    "is_complete": true/false,
    "completeness_percentage": 0-100,
    "component_analysis": {{
        "verb": {{"present": true/false, "appropriate": true/false}},
        "quantity": {{"present": true/false, "specific": true/false}},
        "form": {{"present": true/false, "matches_route": true/false}},
        "route": {{"present": true/false, "clear": true/false}},
        "frequency": {{"present": true/false, "specific": true/false}},
        "duration": {{"present": true/false, "appropriate": true/false}},
        "indication": {{"present": true/false, "helpful": true/false}}
    }},
    "missing_components": ["list of missing required components"],
    "quality_issues": ["list of clarity or quality issues"],
    "improvement_suggestions": ["list of specific improvements"],
    "patient_comprehension_score": 0-100
}}

Focus on what patients need to safely and effectively take their medication.
"""
