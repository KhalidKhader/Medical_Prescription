"""
Drugs Validation Agent Prompts
Contains all prompts for medication validation
"""

def get_medication_validation_prompt(medications: list) -> str:
    """Generate prompt for medication validation"""
    return f"""You are a clinical pharmacist validating prescription medications. Analyze the following medications for clinical accuracy, safety, and completeness.

Medications to validate:
{medications}

For each medication, check:
1. Drug name accuracy and spelling
2. Strength appropriateness for the indication
3. Dosage form compatibility with route
4. Instructions clarity and safety
5. Quantity and days supply reasonableness
6. Potential drug interactions
7. Contraindications or warnings

Return JSON with validation results:
{{
    "validation_summary": {{
        "total_medications": number,
        "valid_medications": number,
        "medications_with_warnings": number,
        "critical_issues": number
    }},
    "medication_validations": [
        {{
            "drug_name": "medication name",
            "validation_status": "valid|warning|critical",
            "issues": ["list of issues found"],
            "recommendations": ["list of recommendations"],
            "confidence": number_0_to_100
        }}
    ],
    "overall_assessment": "brief overall safety assessment"
}}"""

def get_drug_interaction_prompt(medications: list) -> str:
    """Generate prompt for drug interaction checking"""
    return f"""Analyze potential drug-drug interactions for these medications:

Medications: {medications}

Check for:
1. Major interactions (contraindicated)
2. Moderate interactions (monitor closely)
3. Minor interactions (be aware)
4. Duplicate therapy
5. Therapeutic duplication

Return JSON:
{{
    "interactions_found": number,
    "severity_breakdown": {{
        "major": number,
        "moderate": number,
        "minor": number
    }},
    "interactions": [
        {{
            "drug1": "first drug",
            "drug2": "second drug", 
            "severity": "major|moderate|minor",
            "description": "interaction description",
            "clinical_significance": "clinical impact",
            "management": "how to manage this interaction"
        }}
    ]
}}"""