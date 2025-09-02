"""
Instructions of Use Agent Prompts
Contains prompts for generating accurate, structured medication instructions
"""

from typing import Dict, Any, Optional


def get_instructions_generation_prompt(drug_name: str, strength: str, raw_instructions: str, rxnorm_context: Optional[Dict] = None) -> str:
    """
    Generate structured medication instructions with RxNorm clinical context
    
    Args:
        drug_name: Name of the medication
        strength: Medication strength/dosage
        raw_instructions: Raw prescription instructions
        rxnorm_context: RxNorm drug information for clinical context
        
    Returns:
        Instructions generation prompt
    """
    rxnorm_info = ""
    if rxnorm_context:
        rxnorm_info = f"""
RxNorm Clinical Context:
- Drug: {rxnorm_context.get('drug_name', 'N/A')}
- RxCUI: {rxnorm_context.get('concept_id', 'N/A')}
- Typical Form: {rxnorm_context.get('dosage_form', 'Unknown')}
- Route: {rxnorm_context.get('route', 'Unknown')}
- Schedule: {rxnorm_context.get('drug_schedule', 'Not controlled')}
"""

    return f"""
You are a pharmacy intern working under a supervising pharmacist who will review all your recommendations. Generate clear, professional patient medication instructions for pharmacist review.

Medication Information:
- Drug Name: {drug_name}
- Strength: {strength}
- Raw Instructions: {raw_instructions}

{rxnorm_info}

INSTRUCTION GENERATION RULES:
1. Write clear instructions for the patient based on the doctor's abbreviated instructions
2. Include: verb, quantity, route of administration, and frequency/interval
3. Use "Give" for English and "Administer" for Spanish inhalation medications (not "Inhale by inhalation")
4. Generate BOTH English (sig_english) AND Spanish (sig_spanish) instructions
5. For Spanish: NO accents on any letters - use standard characters only
6. For durations <21 days: include duration in instructions
7. Use words for frequency, not numbers (except for hour intervals like "every 4 hours")
8. Do NOT add indication recommendations into the instruction - leave for pharmacist review
8. Make changes to improve instructions and note observations for pharmacist

Should always be:
VERB + QUANTITY + FORM + ROUTE + FREQUENCY + DURATION + INDICATION

eg: Take 1 tablet by mouth every day for 21 days for anxiety.

Those are always the components.

Component Guidelines:
1. VERB: Choose based on route/form
   - Oral tablets/capsules: "Take"
   - Vaginal tablets: "Insert"
   - Eye drops: "Instill"
   - Topical: "Apply"
   - Injections: "Inject"
   - Inhalers: Use "Give" for English and "Administer" for Spanish "Administer" (NOT "Inhale")

2. QUANTITY: Exact amount per dose
   - "1 tablet", "2 capsules", "2 puffs", "thin layer"

3. FORM: Medication form
   - "tablet", "capsule", "puff", "drop", "cream"

4. ROUTE: Administration route
   - "by mouth", "by inhalation", "in each eye", "to affected area"

5. FREQUENCY: Use words, not numbers (except for hour intervals)
   - "once daily", "twice daily", "every 4 hours", "as needed"

6. DURATION: Include if less than 21 days
   - "for 7 days", "for 10 days", "until symptoms improve"

7. INDICATION: Purpose if known
   - "for breathing", "for allergies", "for pain"

Return ONLY a JSON object:
{{
    "structured_instructions": {{
        "verb": "action verb",
        "quantity": "amount per dose",
        "form": "medication form",
        "route": "administration route", 
        "frequency": "how often",
        "duration": "how long or null",
        "indication": "purpose or null"
    }},
    "sig_english": "Complete English instruction",
    "sig_spanish": "Complete Spanish instruction (no accents)",
    "intern_observations": {{
        "changes_made": ["list of changes made to improve instructions"],
        "pharmacist_review_notes": ["observations for supervising pharmacist"],
        "rxnorm_match": true/false,
        "safety_concerns": ["safety concerns for pharmacist review"]
    }},
    "certainty": 0-100
}}

Examples:
- "1 po bid x 7d" → "Take 1 tablet by mouth twice daily for 7 days"
- "2 puffs bid" → "Give  2 puffs by inhalation twice daily"
- "T PO qd am" → "Take 1 tablet by mouth once daily in the morning"
"""